# AWS deployment

Deployment target: account `263429641790`, region `us-east-2` (Ohio).
Deployer role: `arn:aws:iam::263429641790:role/managed/AccountFullAccessRole`.
The application currently implements PDF upload and chunking only. Deployment
does not enable Bedrock, retrieval, or question answering.

## Current deployment status

On October 10, 2026, the `research` profile authenticated successfully.
Organization policy denied the network check in `us-east-1`, `us-west-2`, and
`eu-west-1`; `us-east-2` allowed it. The image, roles, cluster, and Express Mode
service were created in Ohio. The first provisioning attempt failed during IAM
propagation; a retry completed successfully and receives 100% of traffic.

Live application:
https://ai-9cc795dd20a04970bca0dd0293f8831e.ecs.us-east-2.on.aws

Verification passed: trusted HTTPS certificate, health endpoint returning `ok`,
and a real browser session uploading the sample PDF, showing three pages and
two chunks, opening a page preview, and confirming question answering is disabled.
Public DNS resolved correctly; browser and HTTPS checks used that public address
explicitly because this Mac retained an earlier negative DNS cache entry. A
client that queried the hostname before provisioning completed may need a few
minutes for that cached entry to expire.

Service ARN:
`arn:aws:ecs:us-east-2:263429641790:service/ai-research-assistant/ai-research-assistant`.

## Hosting choice

Use ECS Express Mode on Fargate. AWS has closed App Runner to new customers,
and its WebSocket feature request is closed as not planned. Streamlit uses
WebSockets, so App Runner is unsuitable for this interface. ECS Express Mode
provides an HTTPS endpoint and an Application Load Balancer without an
infrastructure framework.

- [App Runner availability](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html)
- [AWS WebSocket support issue](https://github.com/aws/apprunner-roadmap/issues/13)
- [ECS Express Mode setup](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-getting-started.html)

## Authenticate locally

Install AWS CLI v2 and Docker. On this Mac, these were installed with Homebrew;
Colima supplies the Docker daemon.

```bash
aws login --profile research --region us-east-2
aws sts get-caller-identity --profile research
```

Use the browser to choose the intended account and role. If your organization
uses IAM Identity Center instead, use `aws configure sso` and `aws sso login`
with its start URL and SSO region. Other supported AWS CLI credential providers
also work. A role ARN alone cannot authenticate a session.

The deployer requires ECR repository/image operations, ECS Express Mode and
cluster operations, EC2 network read access, and IAM role creation, policy
attachment, and PassRole permissions for the two application roles. AWS may
also need permission to create service-linked roles on first use.

`AccountFullAccessRole` is a deployer identity, not the application's runtime
role. Do not add credentials to source files or container environment variables.

## Verify the container

From this directory:

```bash
colima start --cpu 2 --memory 4 --disk 20
docker build --platform linux/arm64 -t ai-research-assistant:local .
docker run -d --name research-preview -p 127.0.0.1:8501:8501 ai-research-assistant:local
curl --fail http://localhost:8501/_stcore/health
```

Open http://localhost:8501 and upload `sample_docs/research_notes.pdf`.
When finished, run `docker stop research-preview` and `docker rm research-preview`.
The image uses Python 3.12, a non-root user, and an explicit source allowlist.
AWS profiles, `.env`, `.git`, and local PDFs are excluded from its build context.

## Deploy

```bash
AWS_PROFILE=research python3.12 deploy_aws.py --region us-east-2
```

The script verifies the target account, checks for a default VPC, builds an
ARM64 image, publishes it to a private ECR repository, and submits an ECS
Express Mode service. It creates two service roles with AWS managed policies:

- `ai-research-assistant-execution`: image pulling and log delivery through
  `AmazonECSTaskExecutionRolePolicy`.
- `ai-research-assistant-infrastructure`: infrastructure management through
  `AmazonECSInfrastructureRoleforExpressGatewayServices`.

The current app needs no AWS task role because it calls no AWS APIs. A later
Bedrock implementation should add a dedicated ECS task role scoped to the
chosen models and inference actions. Model access and any required provider
agreements must also be enabled before that feature can work.

Configuration: cluster/service/repository `ai-research-assistant`, ARM64,
0.25 vCPU, 1 GiB memory, one task, container port 8501, health endpoint
`/_stcore/health`. The service uses the default VPC and an internet-facing HTTPS
endpoint. It has no application login and is intended as a demonstration.

The script writes the AWS response to ignored `deployment.json`. Service
creation is asynchronous; it is not proof that the app is healthy. Use the
returned service ARN:

```bash
aws ecs monitor-express-gateway-service --service-arn SERVICE_ARN --profile research --region us-east-2
aws ecs describe-express-gateway-service --service-arn SERVICE_ARN --profile research --region us-east-2
```

Use the actual endpoint returned by AWS. Check `/_stcore/health`, then open
the HTTPS endpoint and test an upload and page preview in the browser. Do not
infer a working URL from the service name. If IAM propagation causes an
assume-role error, wait briefly before retrying. A failed run can leave the
repository, roles, or cluster behind; inspect them before rerunning. This script
creates a service; it does not automatically update an existing service.

## Cost and storage

Costs continue while the service runs, including idle time. Budget for Fargate
CPU/memory, Application Load Balancer hours and capacity units, public IPv4
addresses, ECR image storage, CloudWatch logs, and data transfer. Express Mode
has no separate management charge. Use the AWS calculator for an estimate
for `us-east-2`; credits and free-tier eligibility vary by account.

- [Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [Load balancer pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)
- [AWS Pricing Calculator](https://calculator.aws/)

Uploads and parsed text are session memory only. Task replacement, deployment,
or session loss discards them. A future local FAISS index would also be
ephemeral and would not be durable shared storage. One steady-state task keeps
this initial demonstration simple; deployments may temporarily run replacement
tasks and interrupt sessions.

## Remove the deployment

Delete the Express Mode service using its recorded ARN and wait for managed
resource deletion to finish:

```bash
aws ecs delete-express-gateway-service --service-arn SERVICE_ARN --profile research --region us-east-2
```

Then inspect and remove this project's remaining ECR images/repository,
CloudWatch log groups, empty ECS cluster, and the two IAM roles (detach their
policies first). Do not delete a shared VPC, shared load balancer, or unrelated
resources. Deleting only tasks is insufficient: ECS will restart them, and a
remaining load balancer can continue to incur charges.
