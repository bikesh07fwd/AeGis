import subprocess
import json
import time
import urllib.request
import urllib.error

# Get OIDC Identity Token
token = subprocess.check_output("gcloud auth print-identity-token", shell=True).decode('utf-8').strip()
url_base = "https://aegis-api-staging-hyccqmnxfq-uc.a.run.app"

headers = {
    "Authorization": f"Bearer {token}",
    "X-API-KEY": "secret-enterprise-key",
    "Content-Type": "application/json"
}

def measure_endpoint(name, req):
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode('utf-8')
            elapsed = (time.time() - start) * 1000
            print(f"=== {name} ===")
            print(f"Status: {resp.status}")
            print(f"Latency: {elapsed:.2f} ms")
            print(f"Body: {body}\n")
            return elapsed, resp.status, body
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        body = e.read().decode('utf-8')
        print(f"=== {name} ===")
        print(f"HTTPError: {e.code}")
        print(f"Latency: {elapsed:.2f} ms")
        print(f"Body: {body}\n")
        return elapsed, e.code, body
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"=== {name} ===")
        print(f"Error: {e}")
        print(f"Latency: {elapsed:.2f} ms\n")
        return elapsed, 0, str(e)

print("Starting single-request latency measurements...\n")

# 1. Health check
req1 = urllib.request.Request(f"{url_base}/api/v1/health", headers=headers, method="GET")
measure_endpoint("GET /api/v1/health", req1)

# 2. Search check
search_payload = json.dumps({"query": "architecture overview", "limit": 3}).encode('utf-8')
req2 = urllib.request.Request(f"{url_base}/api/v1/chat/search", data=search_payload, headers=headers, method="POST")
measure_endpoint("POST /api/v1/chat/search", req2)

# 3. Chat generate check
gen_payload = json.dumps({
    "question": "What is Aegis AI?",
    "conversation_id": "measure-conv-1",
    "user_id": "measure-user-1"
}).encode('utf-8')
req3 = urllib.request.Request(f"{url_base}/api/v1/chat/generate", data=gen_payload, headers=headers, method="POST")
measure_endpoint("POST /api/v1/chat/generate", req3)
