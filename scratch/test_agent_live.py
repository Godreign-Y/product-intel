import os
import urllib.request
import urllib.parse
import json

# Bypass proxies for local development
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
urllib.request.getproxies = lambda: {}

base_url = "http://127.0.0.1:8000/api/v1/agent/query"

queries = [
    # "what will be my revenue next month?",
    # "what will bemy revenue for next week for minimalist shampoo p002?"
    "what should i do to increase revenue for minimalist shampoo p002?"
    # "what should be done to maximize the revenue?"
]

for idx, q in enumerate(queries, 1):
    print(f"\n=== Query {idx}: {q} ===")
    data = json.dumps({"query": q}).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            print(f"Status Code: {status}")
            if status == 200:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                print(f"Route Called: {res_json.get('route_called')}")
                print(f"Synthesized Response:\n{res_json.get('response')}\n")
                print(f"Raw Data snippet: {str(res_json.get('raw_data'))[:300]}...")
            else:
                print(f"Error Status: {status}")
    except Exception as e:
        print(f"Failed to query endpoint: {e}")
