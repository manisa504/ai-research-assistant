"""Build and deploy the current app to ECS Express Mode using AWS CLI v2.

Uses the caller's AWS credential chain. No credentials are copied into Docker.
Run from this directory: python deploy_aws.py --region us-east-2
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time


def aws(*arguments: str):
    result = subprocess.run(
        ["aws", "--region", REGION, "--no-cli-pager", *arguments, "--output", "json"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def get_or_create(get_arguments, create_arguments, missing_code):
    try:
        return aws(*get_arguments)
    except subprocess.CalledProcessError as error:
        if missing_code not in error.stderr:
            raise
        return aws(*create_arguments)


def deploy(expected_account: str):
    identity = aws("sts", "get-caller-identity")
    account = identity["Account"]
    if account != expected_account:
        raise SystemExit(f"Expected account {expected_account}, authenticated to {account}.")
    print(f"Deploying {NAME} in account {account}, region {REGION}.", flush=True)
    # Check the network before creating any resources. Do not silently create a VPC.
    vpcs = aws("ec2", "describe-vpcs", "--filters", "Name=is-default,Values=true")
    if not vpcs["Vpcs"]:
        raise SystemExit("A default VPC with public subnets is required in this region.")
    subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL)
    # Fail before mutations if this CLI does not support Express Mode.
    aws("ecs", "create-express-gateway-service", "--generate-cli-skeleton", "input")

    registry = f"{account}.dkr.ecr.{REGION}.amazonaws.com"
    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    image = f"{registry}/{NAME}:{tag}"
    subprocess.run(
        ["docker", "build", "--platform", "linux/arm64", "-t", image, "."], check=True
    )
    get_or_create(
        ("ecr", "describe-repositories", "--repository-names", NAME),
        ("ecr", "create-repository", "--repository-name", NAME,
         "--image-tag-mutability", "IMMUTABLE",
         "--image-scanning-configuration", "scanOnPush=true"),
        "RepositoryNotFoundException",
    )
    password = subprocess.run(
        ["aws", "--region", REGION, "ecr", "get-login-password"],
        check=True, capture_output=True, text=True,
    ).stdout
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin", registry],
        input=password, text=True, check=True,
    )
    subprocess.run(["docker", "push", image], check=True)

    roles = {}
    for suffix, principal, policy in [
        ("execution", "ecs-tasks.amazonaws.com", "AmazonECSTaskExecutionRolePolicy"),
        ("infrastructure", "ecs.amazonaws.com", "AmazonECSInfrastructureRoleforExpressGatewayServices"),
    ]:
        role_name = f"{NAME}-{suffix}"
        trust = json.dumps({"Version": "2012-10-17", "Statement": [{
            "Effect": "Allow", "Principal": {"Service": principal},
            "Action": "sts:AssumeRole",
        }]})
        role = get_or_create(
            ("iam", "get-role", "--role-name", role_name),
            ("iam", "create-role", "--role-name", role_name,
             "--assume-role-policy-document", trust), "NoSuchEntity",
        )
        aws("iam", "attach-role-policy", "--role-name", role_name,
            "--policy-arn", f"arn:aws:iam::aws:policy/service-role/{policy}")
        roles[suffix] = role["Role"]["Arn"]
    task_name = f"{NAME}-bedrock"
    trust = json.dumps({"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole", "Condition": {
            "StringEquals": {"aws:SourceAccount": account},
            "ArnLike": {"aws:SourceArn": f"arn:aws:ecs:{REGION}:{account}:*"},
        },
    }]})
    task_role = get_or_create(
        ("iam", "get-role", "--role-name", task_name),
        ("iam", "create-role", "--role-name", task_name,
         "--assume-role-policy-document", trust), "NoSuchEntity",
    )["Role"]["Arn"]
    policy = Path("iam/bedrock-task-policy.json").read_text().replace("us-east-2", REGION)
    aws("iam", "put-role-policy", "--role-name", task_name,
        "--policy-name", "InvokeResearchModels", "--policy-document", policy)
    aws("ecs", "create-cluster", "--cluster-name", NAME)
    print("Allowing IAM roles to propagate before service creation…", flush=True)
    time.sleep(60)
    primary = json.dumps({"image": image, "containerPort": 8501,
        "environment": [{"name": "AWS_DEFAULT_REGION", "value": REGION}]})
    service_arn = f"arn:aws:ecs:{REGION}:{account}:service/{NAME}/{NAME}"
    try:
        aws("ecs", "describe-express-gateway-service", "--service-arn", service_arn)
        exists = True
    except subprocess.CalledProcessError as error:
        if "ServiceNotFoundException" not in error.stderr:
            raise
        exists = False
    common = ("--primary-container", primary, "--task-role-arn", task_role,
              "--cpu", "256", "--memory", "1024", "--cpu-architecture", "ARM64",
              "--health-check-path", "/_stcore/health",
              "--scaling-target", json.dumps({"minTaskCount": 1, "maxTaskCount": 1}))
    if exists:
        response = aws("ecs", "update-express-gateway-service", "--service-arn", service_arn, *common)
    else:
        response = aws("ecs", "create-express-gateway-service", "--service-name", NAME,
                       "--cluster", NAME, "--execution-role-arn", roles["execution"],
                       "--infrastructure-role-arn", roles["infrastructure"], *common,
                       "--tags", "key=Project,value=ai-research-assistant")
    Path("deployment.json").write_text(json.dumps(response, indent=2) + "\n")
    print(json.dumps(response, indent=2))
    print("Service deployment submitted. Monitor the service ARN in deployment.json.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="us-east-2")
    parser.add_argument("--expected-account", default="263429641790")
    arguments = parser.parse_args()
    REGION = arguments.region
    NAME = "ai-research-assistant"
    try:
        deploy(arguments.expected_account)
    except subprocess.CalledProcessError as error:
        if error.stderr:
            print(error.stderr)
        raise SystemExit(error.returncode) from error
