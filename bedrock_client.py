"""Small Bedrock adapter; credentials come from boto3's standard chain."""
import json
import os

import boto3
from botocore.config import Config


class BedrockClient:
    def __init__(self, runtime=None):
        self.region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-2"))
        self.embedding_model = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
        self.chat_model = os.getenv("BEDROCK_CHAT_MODEL", "amazon.nova-lite-v1:0")
        self.runtime = runtime if runtime is not None else boto3.client(
            "bedrock-runtime", region_name=self.region,
            config=Config(connect_timeout=5, read_timeout=90,
                          retries={"total_max_attempts": 3, "mode": "adaptive"}),
        )

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Embedding text must not be empty.")
        if len(text) > 12000:
            raise ValueError("A chunk exceeds the demo's 12,000-character embedding limit.")
        response = self.runtime.invoke_model(
            modelId=self.embedding_model, contentType="application/json", accept="application/json",
            body=json.dumps({"inputText": text, "dimensions": 256, "normalize": True}),
        )
        with response["body"] as body:
            return json.loads(body.read())["embedding"]

    def complete(self, system: str, prompt: str) -> str:
        response = self.runtime.converse(
            modelId=self.chat_model,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 700, "temperature": 0},
        )
        if response.get("stopReason") != "end_turn":
            raise ValueError("Bedrock did not finish the response. Try a shorter question.")
        text = "\n".join(block["text"] for block in response["output"]["message"]["content"] if "text" in block)
        if not text.strip():
            raise ValueError("Bedrock returned an empty response.")
        return text
