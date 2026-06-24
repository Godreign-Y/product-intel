from ollama import chat

MODEL_NAME = "gemma3:4b"

response = chat(
    model=MODEL_NAME,
    messages=[
        {
            "role": "user",
            "content": "Explain how LightGBM works in simple terms."
        }
    ],
    stream=True,
)

print("\n=== Response ===\n")

for chunk in response:
    content = chunk["message"]["content"]
    print(content, end="", flush=True)

print("\n")