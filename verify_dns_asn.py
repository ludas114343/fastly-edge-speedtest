#!/usr/bin/env python3
import socket
import urllib.request
import json

domains = [
    "w-la.ruoyemu.asia",
    "w-fr.ruoyemu.asia",
    "w-east.ruoyemu.asia",
    "w-us.ruoyemu.asia",
    "nf-node.ruoyemu.asia"
]

def query_doh(domain):
    url = f"https://1.1.1.1/dns-query?name={domain}&type=A"
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        ips = []
        for ans in data.get("Answer", []):
            if ans.get("type") == 1: # A record
                ips.append(ans.get("data"))
        return ips

def check_ip_asn(ip):
    # Query ip-api or ipinfo
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,isp,org,as,query"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

print("=== DNS & ASN Verification ===")
for d in domains:
    ips = query_doh(d)
    print(f"\nDomain: {d} -> Resolved IPs via DoH: {ips}")
    for ip in ips:
        info = check_ip_asn(ip)
        print(f"  IP: {ip} -> ASN/Org: {info.get('as')} | {info.get('org')} | Country: {info.get('country')}")
