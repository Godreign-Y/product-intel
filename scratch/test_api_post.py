import requests
import json

url = "http://127.0.0.1:8000/api/v1/decision/ask"
payload = {
    "query": "What might happen if we increase discounts by 10%?",
    "product_id": "P001",
    "session_id": "session_abc123"
}
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

try:
    print(f"Sending POST request to {url}...")
    response = requests.post(url, headers=headers, json=payload)
    print("Response Status Code:", response.status_code)
    print("Response Body:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Failed to call API:", e)
