import requests

BASE = "http://127.0.0.1:8000"

payload = {
    "job_description": "Python, Java, AI, MCA degree required",
    "user_resume": "B.Tech AI 2024. Python, PyTorch, Java"
}

r = requests.post(f"{BASE}/evaluate-json", json=payload)
print(r.status_code)
print(r.json())
