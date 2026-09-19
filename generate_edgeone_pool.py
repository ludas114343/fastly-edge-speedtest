import ipaddress
import json
import os

# Subnets and endpoints for Tencent Cloud EdgeOne Anycast & Regional POPs
EDGEONE_SUBNETS = [
    # Hong Kong (CMI, CN2, 4837 optimized)
    {"region": "HK", "cidr": "43.153.64.0/23", "step": 1, "port": 443, "isp": "CM_CMI"},
    {"region": "HK", "cidr": "162.14.20.0/23", "step": 1, "port": 443, "isp": "CT_CN2_163"},
    {"region": "HK", "cidr": "150.109.112.0/23", "step": 1, "port": 443, "isp": "CU_4837"},
    
    # Japan Tokyo
    {"region": "JP", "cidr": "43.129.20.0/23", "step": 2, "port": 443, "isp": "Anycast_JP"},
    {"region": "JP", "cidr": "150.109.108.0/23", "step": 2, "port": 443, "isp": "Anycast_JP"},
    
    # South Korea Seoul
    {"region": "KR", "cidr": "43.133.232.0/23", "step": 3, "port": 443, "isp": "Anycast_KR"},
    {"region": "KR", "cidr": "119.28.160.0/23", "step": 3, "port": 443, "isp": "Anycast_KR"},
    
    # Singapore
    {"region": "SG", "cidr": "119.28.128.0/23", "step": 2, "port": 443, "isp": "Anycast_SG"},
    {"region": "SG", "cidr": "124.156.128.0/23", "step": 2, "port": 443, "isp": "Anycast_SG"},
    
    # Taiwan
    {"region": "TW", "cidr": "43.153.68.0/23", "step": 3, "port": 443, "isp": "Anycast_TW"},
    
    # Germany Frankfurt
    {"region": "DE", "cidr": "150.109.16.0/23", "step": 3, "port": 443, "isp": "Anycast_DE"},
    
    # UK London
    {"region": "GB", "cidr": "162.14.128.0/23", "step": 3, "port": 443, "isp": "Anycast_GB"},
    
    # France Paris
    {"region": "FR", "cidr": "150.109.20.0/23", "step": 4, "port": 443, "isp": "Anycast_FR"},
    
    # Switzerland Zurich
    {"region": "CH", "cidr": "150.109.24.0/23", "step": 4, "port": 443, "isp": "Anycast_CH"},
    
    # US West (San Jose)
    {"region": "US_WEST", "cidr": "170.106.128.0/23", "step": 2, "port": 443, "isp": "Anycast_USW"},
    
    # US East (Virginia)
    {"region": "US_EAST", "cidr": "170.106.130.0/23", "step": 2, "port": 443, "isp": "Anycast_USE"},
    
    # Canada
    {"region": "CA", "cidr": "170.106.132.0/23", "step": 4, "port": 443, "isp": "Anycast_CA"},
    
    # Australia (Sydney)
    {"region": "AU", "cidr": "150.109.28.0/23", "step": 4, "port": 443, "isp": "Anycast_AU"},
]

CLEAN_DOMAINS = [
    {"region": "HK", "host": "eo-hk.ruoyemu.asia", "port": 443, "isp": "Domain_HK"},
    {"region": "JP", "host": "eo-jp.ruoyemu.asia", "port": 443, "isp": "Domain_JP"},
    {"region": "SG", "host": "eo-sg.ruoyemu.asia", "port": 443, "isp": "Domain_SG"},
    {"region": "US_WEST", "host": "eo-us.ruoyemu.asia", "port": 443, "isp": "Domain_US"},
    {"region": "DE", "host": "eo-eu.ruoyemu.asia", "port": 443, "isp": "Domain_EU"},
    {"region": "GLOBAL", "host": "eo.ruoyemu.asia", "port": 443, "isp": "Domain_Global"},
    {"region": "GLOBAL", "host": "ruoyemu.asia", "port": 443, "isp": "Domain_Apex"}
]

def build_pool():
    pool = []
    seen = set()

    # 1. Add domain candidates
    for d in CLEAN_DOMAINS:
        item = {
            "type": "domain",
            "host": d["host"],
            "port": d["port"],
            "region": d["region"],
            "isp": d["isp"]
        }
        pool.append(item)
        seen.add(f"{d['host']}:{d['port']}")

    # 2. Add IP candidates from EdgeOne subnets
    for sub in EDGEONE_SUBNETS:
        net = ipaddress.ip_network(sub["cidr"])
        step = sub.get("step", 1)
        count = 0
        for i, ip in enumerate(net.hosts()):
            if i % step == 0:
                ip_str = str(ip)
                key = f"{ip_str}:{sub['port']}"
                if key not in seen:
                    seen.add(key)
                    pool.append({
                        "type": "ip",
                        "host": ip_str,
                        "port": sub["port"],
                        "region": sub["region"],
                        "isp": sub["isp"]
                    })
                    count += 1
            if count >= 100:  # Cap per subnet to keep distribution balanced
                break

    return pool

if __name__ == "__main__":
    candidates = build_pool()
    target_path = os.path.join(os.path.dirname(__file__), "edgeone_candidates.json")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)
    print(f"Generated {len(candidates)} EdgeOne candidate endpoints -> {target_path}")
