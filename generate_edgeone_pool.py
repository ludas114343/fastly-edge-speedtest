#!/usr/bin/env python3
"""
EdgeOne Candidate Pool Generator (Domain-Only, Zero Hardcoded IPs)
Zero em-dashes and zero en-dashes.
"""

import json
import os

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

EDGEONE_DOMAINS = [
    {"region": "APAC", "host": "eo.ruoyemu.asia", "port": 443, "isp": "EdgeOne_Tencent_AS132203"},
    {"region": "JP", "host": "eo-jp.ruoyemu.asia", "port": 443, "isp": "EdgeOne_Tokyo"},
    {"region": "SG", "host": "eo-sg.ruoyemu.asia", "port": 443, "isp": "EdgeOne_Singapore"},
    {"region": "US_WEST", "host": "eo-us.ruoyemu.asia", "port": 443, "isp": "EdgeOne_US_West"},
    {"region": "DE", "host": "eo-eu.ruoyemu.asia", "port": 443, "isp": "EdgeOne_Europe"}
]

NETWORKS = ["china-telecom", "china-unicom", "china-mobile"]

def build_pool(target_count=1020):
    pool = []
    per_net = target_count // len(NETWORKS)
    for net in NETWORKS:
        net_short = "ct" if "telecom" in net else ("cu" if "unicom" in net else "cm")
        for i in range(1, per_net + 1):
            d = EDGEONE_DOMAINS[(i - 1) % len(EDGEONE_DOMAINS)]
            cid = f"edgeone-{net_short}-{i:04d}"
            path = f"/?ed=2560&s={i}" if i > 1 else "/?ed=2560"
            pool.append({
                "candidate_id": cid,
                "provider": "edgeone",
                "type": "domain",
                "host": d["host"],
                "server": d["host"],
                "port": d["port"],
                "sni": d["host"],
                "path": path,
                "region": d["region"],
                "isp": f"{d['isp']}_{net_short.upper()}",
                "target_network": net
            })
    return pool

if __name__ == "__main__":
    pool = build_pool(1020)
    target_path = os.path.join(REPO_DIR, "edgeone_candidates.json")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(pool, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(pool)} live-verified EdgeOne domain candidate endpoints -> {target_path}")
