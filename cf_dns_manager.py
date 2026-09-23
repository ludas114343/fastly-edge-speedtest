#!/usr/bin/env python3
import urllib.request
import json
import re
import socket
import sys

CRED_PATH = r"D:\Obsidian\CollegeAid\planning\平台凭据速查.md"
ZONE_ID = "92ff80748a90e7ef55880af0952d2037"

def get_token():
    with open(CRED_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"cfut_[A-Za-z0-9]+", text)
    if m:
        return m.group(0)
    raise RuntimeError("Cloudflare token not found in credentials file.")

def cf_request(method, endpoint, data=None):
    token = get_token()
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method=method
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def list_records():
    res = cf_request("GET", "dns_records?per_page=100")
    if not res.get("success"):
        print("Failed to list records:", res.get("errors"))
        return []
    records = res.get("result", [])
    print(f"Retrieved {len(records)} DNS records.")
    for r in records:
        name = r.get("name", "")
        if any(target in name for target in ["w-", "nf-", "net", "eo", "fastly", "sb"]):
            print(f"Record: ID={r.get('id')} Name={name} Type={r.get('type')} Content={r.get('content')} Proxied={r.get('proxied')}")
    return records

def update_proxied(target_names, proxied=False):
    records = list_records()
    targets_map = {r["name"]: r for r in records if r["name"] in target_names}
    
    updated = []
    for name in target_names:
        if name not in targets_map:
            print(f"WARNING: Record {name} not found in zone!")
            continue
        rec = targets_map[name]
        rec_id = rec["id"]
        current_proxied = rec.get("proxied", False)
        print(f"Processing {name}: current proxied={current_proxied}, setting to {proxied}")
        
        payload = {
            "type": rec["type"],
            "name": rec["name"],
            "content": rec["content"],
            "proxied": proxied,
            "ttl": 1 # 1 = automatic
        }
        res = cf_request("PATCH", f"dns_records/{rec_id}", payload)
        if res.get("success"):
            print(f"SUCCESS: Updated {name} (proxied={proxied})")
            updated.append(name)
        else:
            print(f"ERROR: Failed to update {name}: {res.get('errors')}")
    return updated

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "list"
    if action == "list":
        list_records()
    elif action == "unproxy":
        targets = [
            "w-la.ruoyemu.asia",
            "w-fr.ruoyemu.asia",
            "w-east.ruoyemu.asia",
            "w-us.ruoyemu.asia",
            "nf-node.ruoyemu.asia"
        ]
        update_proxied(targets, proxied=False)
