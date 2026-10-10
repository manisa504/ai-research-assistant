# AWS deployment

1. Browser reaches the managed HTTPS load balancer.
2. Traffic reaches the single Fargate task on port 8501.
3. boto3 uses the task role to invoke Titan embeddings and Nova Lite in Ohio.

ECR supplies the container image; the execution role permits image pulls and logs. The dedicated task role permits only the two model ARNs. CloudWatch receives container logs. ACM manages the endpoint certificate. The diagram omits service-managed subnet details. Documents and FAISS are session-local, not durable or shared.
