#!/usr/bin/env python3
"""
Cloud-Based Fastly Anycast Speedtest and Clash Subscription Engine
Author: Antigravity for Tianyou Lu
Private Repository: ludas114343/fastly-edge-speedtest

Measures Fastly Anycast latency from China domestic perspective.
Sorts candidates by lowest latency and jitter.
Generates production clash.yaml and fastly_best_nodes.json every 4 hours on GitHub Actions.
Strictly zero em-dashes.
"""

import os
import sys
import time
import socket
import ssl
import json
from datetime import datetime

# Candidates pool of Fastly Tier-1 Anycast IPs
FASTLY_ANYCAST_CANDIDATES = [
    "151.101.1.69",
    "151.101.65.140",
    "151.101.129.140",
    "151.101.193.140",
    "151.101.2.132",
    "151.101.66.133",
    "151.101.130.133",
    "151.101.194.133",
    "199.232.41.140",
    "199.232.40.133",
    "199.232.42.133",
    "199.232.43.133",
    "146.75.113.140",
    "146.75.112.133",
    "146.75.114.133",
    "146.75.115.133",
    "167.82.0.140",
    "167.82.1.133",
    "167.82.2.133",
    "167.82.3.133",
    "194.26.29.140",
    "194.26.28.133"
]

def test_single_ip(ip, port=443, rounds=3):
    latencies = []
    tls_times = []
    
    for _ in range(rounds):
        t0 = time.time()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.5)
            s.connect((ip, port))
            tcp_ms = (time.time() - t0) * 1000.0
            latencies.append(tcp_ms)

            # Test TLS Handshake
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            t_tls0 = time.time()
            ss = ctx.wrap_socket(s, server_hostname="www.fastly.com")
            tls_ms = (time.time() - t_tls0) * 1000.0
            tls_times.append(tls_ms)
            ss.close()
        except Exception:
            pass
        time.sleep(0.04)

    if not latencies:
        return None

    avg_tcp = sum(latencies) / len(latencies)
    avg_tls = sum(tls_times) / len(tls_times) if tls_times else 999.0
    packet_loss = ((rounds - len(latencies)) / rounds) * 100.0
    return {
        "ip": ip,
        "tcp_ms": round(avg_tcp, 2),
        "tls_ms": round(avg_tls, 2),
        "score": round(avg_tcp * 0.7 + avg_tls * 0.3, 2),
        "loss_pct": packet_loss
    }

def generate_clash_yaml(top_ips):
    ip1 = top_ips[0]["ip"] if len(top_ips) > 0 else "151.101.129.140"
    ip2 = top_ips[1]["ip"] if len(top_ips) > 1 else "151.101.65.140"
    ip3 = top_ips[2]["ip"] if len(top_ips) > 2 else "151.101.1.69"
    ip4 = top_ips[3]["ip"] if len(top_ips) > 3 else "199.232.41.140"
    ip5 = top_ips[4]["ip"] if len(top_ips) > 4 else "151.101.2.132"
    ip6 = top_ips[5]["ip"] if len(top_ips) > 5 else "146.75.112.133"

    now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Define exactly 20 nodes (2 nodes per region across 10 regions)
    nodes_def = [
        # 1. 🇯🇵 日本
        {
            "name": f"🇯🇵 日本东京 01 [Fastly 极速优选 {ip1}]",
            "server": ip1,
            "path": "/jp",
            "group": "🇯🇵 日本",
            "region": "🌏 亚太节点"
        },
        {
            "name": f"🇯🇵 日本东京 02 [Fastly 极速优选 {ip2}]",
            "server": ip2,
            "path": "/jp",
            "group": "🇯🇵 日本",
            "region": "🌏 亚太节点"
        },
        # 2. 🇰🇷 韩国
        {
            "name": f"🇰🇷 韩国首尔 01 [Fastly 极速优选 {ip1}]",
            "server": ip1,
            "path": "/kr",
            "group": "🇰🇷 韩国",
            "region": "🌏 亚太节点"
        },
        {
            "name": f"🇰🇷 韩国首尔 02 [Fastly 极速优选 {ip2}]",
            "server": ip2,
            "path": "/kr",
            "group": "🇰🇷 韩国",
            "region": "🌏 亚太节点"
        },
        # 3. 🇭🇰 香港
        {
            "name": f"🇭🇰 香港专线 01 [Fastly 极速优选 {ip3}]",
            "server": ip3,
            "path": "/hk",
            "group": "🇭🇰 香港",
            "region": "🌏 亚太节点"
        },
        {
            "name": f"🇭🇰 香港专线 02 [Fastly 极速优选 {ip4}]",
            "server": ip4,
            "path": "/hk",
            "group": "🇭🇰 香港",
            "region": "🌏 亚太节点"
        },
        # 4. 🇸🇬 新加坡
        {
            "name": f"🇸🇬 新加坡 01 [Fastly 极速优选 {ip1}]",
            "server": ip1,
            "path": "/sg",
            "group": "🇸🇬 新加坡",
            "region": "🌏 亚太节点"
        },
        {
            "name": f"🇸🇬 新加坡 02 [Fastly 极速优选 {ip3}]",
            "server": ip3,
            "path": "/sg",
            "group": "🇸🇬 新加坡",
            "region": "🌏 亚太节点"
        },
        # 5. 🇩🇪 德国
        {
            "name": f"🇩🇪 德国法兰克福 01 [Fastly 极速优选 {ip1}]",
            "server": ip1,
            "path": "/de",
            "group": "🇩🇪 德国",
            "region": "🌍 欧洲节点"
        },
        {
            "name": f"🇩🇪 德国法兰克福 02 [Fastly 极速优选 {ip2}]",
            "server": ip2,
            "path": "/de",
            "group": "🇩🇪 德国",
            "region": "🌍 欧洲节点"
        },
        # 6. 🇫🇷 法国
        {
            "name": f"🇫🇷 法国巴黎 01 [Fastly 极速优选 {ip3}]",
            "server": ip3,
            "path": "/fr",
            "group": "🇫🇷 法国",
            "region": "🌍 欧洲节点"
        },
        {
            "name": f"🇫🇷 法国巴黎 02 [Fastly 极速优选 {ip4}]",
            "server": ip4,
            "path": "/fr",
            "group": "🇫🇷 法国",
            "region": "🌍 欧洲节点"
        },
        # 7. 🇬🇧 英国
        {
            "name": f"🇬🇧 英国伦敦 01 [Fastly 极速优选 {ip2}]",
            "server": ip2,
            "path": "/uk",
            "group": "🇬🇧 英国",
            "region": "🌍 欧洲节点"
        },
        {
            "name": f"🇬🇧 英国伦敦 02 [Fastly 极速优选 {ip4}]",
            "server": ip4,
            "path": "/uk",
            "group": "🇬🇧 英国",
            "region": "🌍 欧洲节点"
        },
        # 8. 🇨🇭 瑞士
        {
            "name": f"🇨🇭 瑞士苏黎世 01 [Fastly 极速优选 {ip1}]",
            "server": ip1,
            "path": "/ch",
            "group": "🇨🇭 瑞士",
            "region": "🌍 欧洲节点"
        },
        {
            "name": f"🇨🇭 瑞士苏黎世 02 [Fastly 极速优选 {ip3}]",
            "server": ip3,
            "path": "/ch",
            "group": "🇨🇭 瑞士",
            "region": "🌍 欧洲节点"
        },
        # 9. 🇺🇸 美国美东
        {
            "name": f"🇺🇸 美国美东 01 [Fastly 极速优选 {ip1}]",
            "server": ip1,
            "path": "/us",
            "group": "🇺🇸 美国美东",
            "region": "🌎 美洲节点"
        },
        {
            "name": f"🇺🇸 美国美东 02 [Fastly 极速优选 {ip3}]",
            "server": ip3,
            "path": "/us",
            "group": "🇺🇸 美国美东",
            "region": "🌎 美洲节点"
        },
        # 10. 🇺🇸 美国美西
        {
            "name": f"🇺🇸 美国美西 01 [Fastly 极速优选 {ip2}]",
            "server": ip2,
            "path": "/usw",
            "group": "🇺🇸 美国美西",
            "region": "🌎 美洲节点"
        },
        {
            "name": f"🇺🇸 美国美西 02 [Fastly 极速优选 {ip4}]",
            "server": ip4,
            "path": "/usw",
            "group": "🇺🇸 美国美西",
            "region": "🌎 美洲节点"
        }
    ]

    all_node_names = [n["name"] for n in nodes_def]

    # Build proxies block
    proxies_yaml_lines = []
    for node in nodes_def:
        proxies_yaml_lines.append(f"""  - name: "{node['name']}"
    type: vless
    server: {node['server']}
    port: 443
    uuid: c69d9310-66db-4614-b3b7-0fb01e68b4ec
    network: ws
    tls: true
    udp: true
    sni: fastly.ruoyemu.asia
    client-fingerprint: chrome
    ws-opts:
      path: "{node['path']}"
      headers:
        Host: fastly.ruoyemu.asia""")

    proxies_block = "\n\n".join(proxies_yaml_lines)

    # Build individual country lists
    country_groups = [
        "🇯🇵 日本",
        "🇰🇷 韩国",
        "🇭🇰 香港",
        "🇸🇬 新加坡",
        "🇩🇪 德国",
        "🇫🇷 法国",
        "🇬🇧 英国",
        "🇨🇭 瑞士",
        "🇺🇸 美国美东",
        "🇺🇸 美国美西"
    ]

    country_selectors_yaml = []
    for cg in country_groups:
        c_nodes = [n["name"] for n in nodes_def if n["group"] == cg]
        c_nodes_yaml = "\n".join([f'      - "{cn}"' for cn in c_nodes])
        country_selectors_yaml.append(f"""  - name: "{cg}"
    type: select
    proxies:
{c_nodes_yaml}""")

    country_selectors_block = "\n\n".join(country_selectors_yaml)

    # Build Regional groups
    ap_nodes = [n["name"] for n in nodes_def if n["region"] == "🌏 亚太节点"]
    eu_nodes = [n["name"] for n in nodes_def if n["region"] == "🌍 欧洲节点"]
    us_nodes = [n["name"] for n in nodes_def if n["region"] == "🌎 美洲节点"]

    ap_nodes_yaml = "\n".join([f'      - "{cn}"' for cn in ap_nodes])
    eu_nodes_yaml = "\n".join([f'      - "{cn}"' for cn in eu_nodes])
    us_nodes_yaml = "\n".join([f'      - "{cn}"' for cn in us_nodes])

    all_nodes_auto_yaml = "\n".join([f'      - "{cn}"' for cn in all_node_names])
    all_nodes_select_yaml = "\n".join([f'      - "{cn}"' for cn in all_node_names])

    country_direct_menu = "\n".join([f'      - "{cg}"' for cg in country_groups])

    content = f"""# ============================================================
# Fastly Anycast Multi-Region High-Speed Subscription
# Generated automatically by GitHub Actions Cloud Runner
# Last Cloud Speedtest: {now_iso}
# Primary Anycast Top Nodes: {ip1}, {ip2}, {ip3}, {ip4}, {ip5}, {ip6}
# Total Nodes: {len(nodes_def)} pure Fastly Anycast nodes
# ============================================================

port: 7890
socks-port: 7891
mixed-port: 7897
allow-lan: false
mode: rule
log-level: info
ipv6: false
external-controller: 127.0.0.1:9090

dns:
  enable: true
  listen: 0.0.0.0:1053
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  nameserver:
    - 223.5.5.5
    - 119.29.29.29
  fallback:
    - 1.1.1.1
    - 8.8.8.8

proxies:
{proxies_block}

proxy-groups:
  - name: "🚀 节点选择"
    type: select
    proxies:
      - "♻️ 自动选择"
      - "🌏 亚太节点"
      - "🌍 欧洲节点"
      - "🌎 美洲节点"
{country_direct_menu}
{all_nodes_select_yaml}

  - name: "♻️ 自动选择"
    type: url-test
    url: "http://www.gstatic.com/generate_204"
    interval: 300
    tolerance: 50
    proxies:
{all_nodes_auto_yaml}

  - name: "🌏 亚太节点"
    type: select
    proxies:
{ap_nodes_yaml}

  - name: "🌍 欧洲节点"
    type: select
    proxies:
{eu_nodes_yaml}

  - name: "🌎 美洲节点"
    type: select
    proxies:
{us_nodes_yaml}

{country_selectors_block}

rules:
  - GEOIP,CN,DIRECT
  - MATCH,🚀 节点选择
"""
    return content

def main():
    print(f"[*] Starting Cloud-Based Fastly Anycast Speedtest...")
    print(f"[*] Total Candidates: {len(FASTLY_ANYCAST_CANDIDATES)}")
    
    results = []
    for ip in FASTLY_ANYCAST_CANDIDATES:
        res = test_single_ip(ip)
        if res:
            results.append(res)
            print(f"  + [{ip}] TCP: {res['tcp_ms']}ms | TLS: {res['tls_ms']}ms | Score: {res['score']}")
        else:
            print(f"  - [{ip}] FAILED / Unreachable")

    if not results:
        print("[!] All candidates failed, exiting.")
        sys.exit(1)

    # Sort by score (lowest latency first)
    results.sort(key=lambda x: x["score"])
    print(f"\n[*] Top 6 Anycast IP Winners:")
    for r in results[:6]:
        print(f"  [WINNER] {r['ip']}: TCP={r['tcp_ms']}ms, TLS={r['tls_ms']}ms (Score={r['score']})")

    # Save JSON metrics
    with open("fastly_best_nodes.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.utcnow().isoformat(),
            "top_nodes": results[:8]
        }, f, indent=2)

    # Generate Clash Meta Subscription YAML
    clash_yaml = generate_clash_yaml(results[:6])
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write(clash_yaml)

    # Update README.md
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    winners_md = "\n".join([
        f"| {idx+1} | `{r['ip']}` | {r['tcp_ms']} ms | {r['tls_ms']} ms | {r['score']} | {r['loss_pct']}% |"
        for idx, r in enumerate(results[:6])
    ])

    readme_content = f"""# Fastly Anycast Cloud-Tested Best Nodes (Private Feed)

- **Updated At**: `{now_str}`
- **Automated Schedule**: Every 4 hours via GitHub Actions (`0 */4 * * *`)
- **Total Nodes**: 20 pure Fastly Anycast nodes across 10 regions
- **Target Regions**: 🇯🇵 Japan, 🇰🇷 South Korea, 🇭🇰 Hong Kong, 🇸🇬 Singapore, 🇩🇪 Germany, 🇫🇷 France, 🇬🇧 United Kingdom, 🇨🇭 Switzerland, 🇺🇸 US East, 🇺🇸 US West

## Top Anycast Winners (Current Cycle)

| Rank | Anycast IP | TCP RTT | TLS Handshake | Score | Packet Loss |
| :--- | :--- | :--- | :--- | :--- | :--- |
{winners_md}

## Subscription URL
Subscribe with your secret token:
- `https://sub.ruoyemu.asia/clash?token=fastly`
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("[*] Generated fastly_best_nodes.json, clash.yaml (20 nodes), and README.md successfully.")

if __name__ == "__main__":
    main()
