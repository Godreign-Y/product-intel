import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")
print("API Key starts with:", api_key[:10] if api_key else None)
if not api_key:
    sys.exit(1)

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key, timeout=5.0)
try:
    print("Sending test request to Llama 3.1 instruct model...")
    response = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[
            {"role": "user", "content": "hello"}
        ],
        max_tokens=10
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
