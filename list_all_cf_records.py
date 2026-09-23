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

url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?per_page=100"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    records = json.loads(resp.read().decode("utf-8")).get("result", [])

print(f"Total records in zone: {len(records)}")
for r in sorted(records, key=lambda x: x.get('name')):
    print(f"Name={r.get('name')} | Type={r.get('type')} | Content={r.get('content')} | Proxied={r.get('proxied')}")
