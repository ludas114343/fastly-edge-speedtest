#!/usr/bin/env python3
"""
Multi-Platform Candidate Pool Generator
Generates ~1000+ candidate endpoints each for:
- EdgeOne (1000+ candidates)
- Fastly (1000+ candidates)
- Wasmer (1000+ candidates)
- Netlify (1000+ candidates)
Total: ~4000+ candidate pool with full country and ISP tags.
Zero em-dashes.
"""

import json
import os
import ipaddress

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

REGIONS = ["HK", "JP", "KR", "SG", "TW", "DE", "GB", "FR", "CH", "US_WEST", "US_EAST", "CA", "AU"]

# 1. EdgeOne Networks & Domains
EDGEONE_NETWORKS = [
    {"cidr": "162.14.128.0/24", "regions": ["HK", "JP", "KR", "SG", "TW"], "isp": "Anycast_APAC"},
    {"cidr": "162.14.129.0/24", "regions": ["DE", "GB", "FR", "CH"], "isp": "Anycast_EU"},
    {"cidr": "162.14.130.0/24", "regions": ["US_WEST", "US_EAST", "CA", "AU"], "isp": "Anycast_US"},
    {"cidr": "162.14.131.0/24", "regions": ["HK", "JP", "SG", "US_WEST"], "isp": "Anycast_APAC_US"},
    {"cidr": "162.14.132.0/24", "regions": ["DE", "GB", "US_EAST", "CA"], "isp": "Anycast_EU_US"},
]
EDGEONE_DOMAINS = [
    {"region": "HK", "host": "ruoyemu.asia", "port": 443, "isp": "Domain_Apex"},
    {"region": "HK", "host": "eo.ruoyemu.asia", "port": 443, "isp": "Domain_EdgeOne"},
    {"region": "JP", "host": "eo-jp.ruoyemu.asia", "port": 443, "isp": "Domain_Tokyo"},
    {"region": "SG", "host": "eo-sg.ruoyemu.asia", "port": 443, "isp": "Domain_Singapore"},
    {"region": "US_WEST", "host": "eo-us.ruoyemu.asia", "port": 443, "isp": "Domain_US_West"},
    {"region": "DE", "host": "eo-eu.ruoyemu.asia", "port": 443, "isp": "Domain_Europe"},
]

# 2. Fastly Networks & Domains
FASTLY_NETWORKS = [
    {"cidr": "151.101.1.0/24", "regions": ["HK", "JP", "SG"], "isp": "Fastly_APAC_1"},
    {"cidr": "151.101.2.0/24", "regions": ["DE", "GB", "FR"], "isp": "Fastly_EU_1"},
    {"cidr": "151.101.65.0/24", "regions": ["US_WEST", "US_EAST"], "isp": "Fastly_US_1"},
    {"cidr": "151.101.129.0/24", "regions": ["HK", "TW", "KR"], "isp": "Fastly_APAC_2"},
    {"cidr": "199.232.1.0/24", "regions": ["CH", "CA", "AU"], "isp": "Fastly_Global_1"},
]
FASTLY_DOMAINS = [
    {"region": "HK", "host": "fastly.jsdelivr.net", "port": 443, "isp": "Fastly_jsDelivr"},
    {"region": "US_EAST", "host": "reddit.map.fastly.net", "port": 443, "isp": "Fastly_Reddit"},
    {"region": "US_WEST", "host": "github.global.ssl.fastly.net", "port": 443, "isp": "Fastly_GitHub"},
]

# 3. Wasmer Networks & Domains
WASMER_NETWORKS = [
    {"cidr": "66.42.98.0/24", "regions": ["HK", "JP", "KR", "SG", "TW"], "isp": "Wasmer_Vultr_APAC"},
    {"cidr": "151.158.1.0/24", "regions": ["DE", "GB", "FR", "CH"], "isp": "Wasmer_Hetzner_EU"},
    {"cidr": "5.78.28.0/24", "regions": ["US_WEST", "CA"], "isp": "Wasmer_Hetzner_USW"},
    {"cidr": "5.161.23.0/24", "regions": ["US_EAST", "AU"], "isp": "Wasmer_Hetzner_USE"},
    {"cidr": "208.68.180.0/24", "regions": ["US_WEST", "HK", "JP"], "isp": "Wasmer_Fremont"},
]
WASMER_DOMAINS = [
    {"region": "US_WEST", "host": "w-us.ruoyemu.asia", "port": 443, "isp": "Wasmer_USW"},
    {"region": "US_EAST", "host": "w-east.ruoyemu.asia", "port": 443, "isp": "Wasmer_USE"},
    {"region": "FR", "host": "w-fr.ruoyemu.asia", "port": 443, "isp": "Wasmer_EU"},
    {"region": "HK", "host": "w-la.ruoyemu.asia", "port": 443, "isp": "Wasmer_APAC"},
    {"region": "US_WEST", "host": "wasmer.io", "port": 443, "isp": "Wasmer_Official"},
]

# 4. Netlify Networks & Domains
NETLIFY_NETWORKS = [
    {"cidr": "75.2.60.0/24", "regions": ["HK", "JP", "KR", "SG"], "isp": "Netlify_Global_1"},
    {"cidr": "99.83.190.0/24", "regions": ["DE", "GB", "FR", "CH"], "isp": "Netlify_Global_2"},
    {"cidr": "100.24.100.0/24", "regions": ["US_EAST", "US_WEST", "CA"], "isp": "Netlify_AWS_1"},
    {"cidr": "54.214.50.0/24", "regions": ["US_WEST", "AU", "TW"], "isp": "Netlify_AWS_2"},
    {"cidr": "34.223.80.0/24", "regions": ["HK", "JP", "SG", "US_WEST"], "isp": "Netlify_AWS_3"},
]
NETLIFY_DOMAINS = [
    {"region": "US_EAST", "host": "netlify.app", "port": 443, "isp": "Netlify_App"},
    {"region": "US_WEST", "host": "netlify.com", "port": 443, "isp": "Netlify_Com"},
]

def build_candidates_for_provider(networks, domains):
    pool = []
    seen = set()
    for d in domains:
        key = f"{d['host']}:{d['port']}"
        seen.add(key)
        pool.append({
            "type": "domain",
            "host": d["host"],
            "port": d["port"],
            "region": d["region"],
            "isp": d["isp"]
        })
    for net_info in networks:
        net = ipaddress.ip_network(net_info["cidr"])
        regions = net_info["regions"]
        for i, ip in enumerate(net.hosts()):
            ip_str = str(ip)
            key = f"{ip_str}:443"
            if key not in seen:
                seen.add(key)
                assigned_region = regions[i % len(regions)]
                pool.append({
                    "type": "ip",
                    "host": ip_str,
                    "port": 443,
                    "region": assigned_region,
                    "isp": net_info["isp"]
                })
    return pool

def generate_all():
    providers = [
        ("edgeone", EDGEONE_NETWORKS, EDGEONE_DOMAINS, "edgeone_candidates.json"),
        ("fastly", FASTLY_NETWORKS, FASTLY_DOMAINS, "fastly_candidates.json"),
        ("wasmer", WASMER_NETWORKS, WASMER_DOMAINS, "wasmer_candidates.json"),
        ("netlify", NETLIFY_NETWORKS, NETLIFY_DOMAINS, "netlify_candidates.json"),
    ]
    total = 0
    for name, nets, doms, filename in providers:
        pool = build_candidates_for_provider(nets, doms)
        filepath = os.path.join(REPO_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(pool, f, indent=2)
        total += len(pool)
        print(f"[{name.upper()}] Generated {len(pool)} candidates -> {filename}")
    print(f"\nTotal candidate pool across 4 providers: {total} candidates.")

if __name__ == "__main__":
    generate_all()
