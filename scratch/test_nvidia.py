import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")
print(f"API Key: {api_key[:10]}...")

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key, timeout=15.0)

try:
    print("Calling OpenAI...")
    response = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[
            {"role": "user", "content": "Hello! Reply with 'Hello World' and nothing else."}
        ],
        max_tokens=50
    )
    print("Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
