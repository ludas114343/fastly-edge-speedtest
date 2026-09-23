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

# Account ID
account_id = "b1103e1120a612a1d939b69025c9138a"
domain_id = "9a3d6babe11d5b8224408b3938ef0b5d46d24a55"

url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/domains/{domain_id}"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="DELETE")
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("DELETE Worker Custom Domain SUCCESS:", res.get("success"))
except Exception as e:
    print("DELETE Worker Custom Domain error:", e)
