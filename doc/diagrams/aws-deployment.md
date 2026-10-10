# AWS deployment

1. Browser reaches the managed HTTPS load balancer.
2. Traffic reaches the single Fargate task on port 8501.
3. boto3 uses the task role to call the regional Bedrock runtime: Titan V2 via InvokeModel and Nova Lite via Converse.

ECR supplies the container image; the execution role permits image pulls and logs. The dedicated task role permits bedrock:InvokeModel only on amazon.titan-embed-text-v2:0 and amazon.nova-lite-v1:0 in us-east-2. Converse uses this same IAM action. CloudWatch receives container logs. ACM manages the endpoint certificate. The diagram omits service-managed subnet details. Documents and FAISS are session-local, not durable or shared.
