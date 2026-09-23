import sys
import re
import json
import urllib.request

CRED_PATH = r"D:\Obsidian\CollegeAid\planning\平台凭据速查.md"
ZONE_ID = "92ff80748a90e7ef55880af0952d2037"

with open(CRED_PATH, "r", encoding="utf-8") as f:
    text = f.read()

m = re.search(r"cfut_[A-Za-z0-9]+", text)
token = m.group(0)

# Check Worker Routes in zone
url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/workers/routes"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(req) as resp:
        routes = json.loads(resp.read().decode("utf-8")).get("result", [])
        print(f"Worker Routes ({len(routes)}):")
        for r in routes:
            print(f"  Pattern={r.get('pattern')} Script={r.get('script')}")
except Exception as e:
    print("Worker Routes error:", e)

# Check Worker Custom Domains in zone
url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/custom_domains"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(req) as resp:
        domains = json.loads(resp.read().decode("utf-8")).get("result", [])
        print(f"Custom Domains ({len(domains)}):")
        for d in domains:
            print(f"  Hostname={d.get('hostname')} Service={d.get('service')} Status={d.get('status')}")
except Exception as e:
    print("Custom Domains error:", e)
