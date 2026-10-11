# AWS deployment

Deployment region: `us-east-2` (Ohio). Supply your own AWS account ID and
deployer identity when following this guide; deployed resource identifiers are omitted.
The application implements PDF ingestion, Titan embeddings, local FAISS retrieval,
and Nova Lite question answering with validated filename/page citations.

## Current deployment status

**Offline as of October 10, 2026.** CloudTrail records deletion of the Express
Mode service at 7:17 PM Pacific. The former endpoint no longer resolves.
Run the application locally using the README instructions. The deployment
and verification details below describe the recorded run before removal.

On October 10, 2026, the `research` profile authenticated successfully.
Organization policy denied the network check in `us-east-1`, `us-west-2`, and
`eu-west-1`; `us-east-2` allowed it. The image, roles, cluster, and Express Mode
service were created in Ohio. The first provisioning attempt failed during IAM
propagation; a retry completed successfully and received 100% of traffic before removal.

The former application endpoint is offline and has been removed from this guide.

The Bedrock integration is verified separately from service health. See the
[recorded browser checks](doc/evidence/browser-smoke.json) and the
[12-case real-Bedrock evaluation](doc/evidence/evaluation_results.csv).

For a new deployment, use the service identifier returned by AWS.
The previous deployment's service ARN is omitted.

## Static project showcase

The portfolio walkthrough is hosted separately at
https://manisa504.github.io/ai-research-assistant/ using GitHub Pages.
`.github/workflows/pages.yml` publishes the existing `doc/` folder directly.
Set the Pages source to **GitHub Actions**, not the nonexistent `/docs` branch
folder. The showcase contains static evidence, an offline notice, and local setup links;
Bedrock inference and AWS credentials remain in the application runtime.
The three architecture drawings describe that AWS application, not Pages hosting.

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
attachment, and PassRole permissions for the three application roles. AWS may
also need permission to create service-linked roles on first use.

Use a separate deployer identity rather than the application's runtime role.
Do not add credentials to source files or container environment variables.

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
AWS_PROFILE=research python3.12 deploy_aws.py --region us-east-2 \
  --expected-account YOUR_AWS_ACCOUNT_ID
```

The script verifies the target account, checks for a default VPC, builds an
ARM64 image, publishes it to a private ECR repository, and submits an ECS
Express Mode service. It creates or updates the service and creates two supporting roles with AWS managed policies:

- `ai-research-assistant-execution`: image pulling and log delivery through
  `AmazonECSTaskExecutionRolePolicy`.
- `ai-research-assistant-infrastructure`: infrastructure management through
  `AmazonECSInfrastructureRoleforExpressGatewayServices`.

A third role, `ai-research-assistant-bedrock`, is the **task role** used by
application code. Its policy allows `bedrock:InvokeModel` on only:

- `arn:aws:bedrock:us-east-2::foundation-model/amazon.titan-embed-text-v2:0`
- `arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-lite-v1:0`

Converse uses the InvokeModel permission. The task trust policy restricts the
source account and ECS region. AWS supplies temporary task credentials; no local
profile or keys enter the image. The execution role remains separate.

Both models were invoked successfully in this account/region. Before deploying
elsewhere, verify model availability and the account's model access/provider
requirements. ListFoundationModels alone does not prove inference access:

```bash
aws bedrock list-foundation-models --profile research --region us-east-2
aws bedrock-runtime converse --profile research --region us-east-2 \
  --model-id amazon.nova-lite-v1:0 \
  --messages '[{"role":"user","content":[{"text":"Say ready"}]}]' \
  --inference-config '{"maxTokens":20,"temperature":0}'
```

The scoped policy in `iam/bedrock-task-policy.json` refines the deterministic
Autopilot baseline in `iam/generated-baseline.json`: it removes unused
Guardrail/tool/bearer-token permissions and scopes the two known regional model
ARNs. Reproduce the baseline with:

```bash
uvx iam-policy-autopilot@latest generate-policies "$PWD/bedrock_client.py" \
  --region us-east-2 --account YOUR_AWS_ACCOUNT_ID --service-hints bedrock-runtime --pretty
```

The Docker health check requires no credentials. A locally started container
without a credential provider can parse PDFs but cannot invoke Bedrock. Use the
local Python environment with an authenticated profile for the full local demo.

Recorded deployment configuration: cluster/service/repository `ai-research-assistant`, ARM64,
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
the HTTPS endpoint and upload the sample, build its index, and ask for the average temperature. Verify
18 degrees Celsius with a page-2 citation and inspect the quote. Also ask for
the absent budget to verify abstention. Do not
infer a working URL from the service name. If IAM propagation causes an
assume-role error, wait briefly before retrying. A failed run can leave the
repository, roles, or cluster behind; inspect them before rerunning. This script
updates the existing service when it is found, otherwise creates it.

## Cost and storage

Costs continue while the service runs, including idle time. Budget for
Bedrock embedding input and Nova input/output tokens, Fargate CPU/memory,
Application Load Balancer hours and capacity units, public IPv4
addresses, ECR image storage, CloudWatch logs, and data transfer. Express Mode
has no separate management charge. Use the AWS calculator for an estimate
for `us-east-2`; credits and free-tier eligibility vary by account.

- [Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [Load balancer pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)
- [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
- [AWS Pricing Calculator](https://calculator.aws/)

Uploads and parsed text are session memory only. Task replacement, deployment,
or session loss discards them. The local FAISS index is also ephemeral and is
not durable shared storage. One steady-state task keeps
this initial demonstration simple; deployments may temporarily run replacement
tasks and interrupt sessions.

## Remove the deployment

Delete the Express Mode service using its recorded ARN and wait for managed
resource deletion to finish:

```bash
aws ecs delete-express-gateway-service --service-arn SERVICE_ARN --profile research --region us-east-2
```

Then inspect and remove this project's remaining ECR images/repository,
CloudWatch log groups, empty ECS cluster, and the three IAM roles (detach their
policies first). Do not delete a shared VPC, shared load balancer, or unrelated
resources. Deleting only tasks is insufficient: ECS will restart them, and a
remaining load balancer can continue to incur charges.

## Repository privacy

Published examples omit account-specific ARNs, account IDs, and former service
endpoints. `YOUR_AWS_ACCOUNT_ID` is a placeholder; supply your own 12-digit
account ID explicitly. AWS-owned model/policy ARNs and runtime-generated ARNs
remain where needed for working IAM policies and deployment code. The generated
baseline policy uses `YOUR_AWS_ACCOUNT_ID` and is an illustrative template, not
a policy to deploy unchanged. Deployment responses remain in ignored
`deployment.json`; review screenshots and logs before adding new evidence.
