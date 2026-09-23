import sys
import re
import json
import urllib.request

CRED_PATH = r"D:\Obsidian\CollegeAid\planning\平台凭据速查.md"

with open(CRED_PATH, "r", encoding="utf-8") as f:
    text = f.read()

m = re.search(r"cfut_[A-Za-z0-9]+", text)
token = m.group(0)

# Get Account ID first
req = urllib.request.Request("https://api.cloudflare.com/client/v4/accounts", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req) as resp:
    accounts = json.loads(resp.read().decode("utf-8")).get("result", [])
    print(f"Accounts: {[a.get('id') for a in accounts]}")
    account_id = accounts[0].get("id")

# List worker scripts
req_scripts = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts", headers={"Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(req_scripts) as resp:
        scripts = json.loads(resp.read().decode("utf-8")).get("result", [])
        print(f"Worker Scripts ({len(scripts)}):")
        for s in scripts:
            print(f"  Script: {s.get('id')}")
except Exception as e:
    print("Worker scripts err:", e)

# List custom domains on account
req_cd = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/domains", headers={"Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(req_cd) as resp:
        domains = json.loads(resp.read().decode("utf-8")).get("result", [])
        print(f"Worker Domains ({len(domains)}):")
        for d in domains:
            print(f"  Domain: ID={d.get('id')} Hostname={d.get('hostname')} Service={d.get('service')}")
except Exception as e:
    print("Worker domains err:", e)
