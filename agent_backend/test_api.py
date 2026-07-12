import requests

url = "https://indic-finsight-seaadeep-998877.loca.lt/chat"
headers = {"Bypass-Tunnel-Reminder": "true", "Content-Type": "application/json"}
data = {"text": "What are the supply chain risks for Reliance?", "history": []}

try:
    with requests.post(url, headers=headers, json=data, stream=True) as r:
        print(f"Status: {r.status_code}")
        for line in r.iter_lines():
            if line:
                print(line.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
