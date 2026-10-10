from io import BytesIO
import json
from bedrock_client import BedrockClient


def test_embedding_and_converse_contract():
    class Runtime:
        def invoke_model(self, **kwargs):
            body = json.loads(kwargs["body"])
            assert body == {"inputText": "hello", "dimensions": 256, "normalize": True}
            assert kwargs["modelId"] == "amazon.titan-embed-text-v2:0"
            return {"body": BytesIO(b'{"embedding":[1,0]}')}
        def converse(self, **kwargs):
            assert kwargs["inferenceConfig"]["maxTokens"] == 700
            assert kwargs["system"] == [{"text": "system"}]
            return {"stopReason": "end_turn", "output": {"message": {"content": [{"text": "hello"}]}}}
    client = BedrockClient(Runtime())
    assert client.embed("hello") == [1, 0]
    assert client.complete("system", "prompt") == "hello"
