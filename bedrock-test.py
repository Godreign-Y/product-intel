from dotenv import load_dotenv
import boto3

load_dotenv()

client = boto3.client("bedrock-runtime")

response = client.converse(
    modelId="google.gemma-3-4b-it",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": "Hello from AWS Bedrock"
                }
            ]
        }
    ]
)

print(
    response["output"]["message"]["content"][0]["text"]
)