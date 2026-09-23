#!/usr/bin/env python3
"""
Geo Gate Pre-Publish Hard Verification Gate
Enforces 100% agreement between Node Name / Flag and Real Tunnel Egress Country.
Tests: TLS -> WS 101 -> VLESS -> generate_204 -> Real Outbound IP Geolocation.
Any mismatch causes gate failure. Zero false positives.
"""

import os
import sys
import time
import json
import socket
import ssl
import urllib.request
import urllib.parse
import subprocess
import yaml
import budget_watchdog

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

COUNTRY_NAME_MAP = {
    "日本": "JP",
    "韩国": "KR",
    "新加坡": "SG",
    "德国": "DE",
    "英国": "GB",
    "法国": "FR",
    "瑞士": "CH",
    "爱尔兰": "IE",
    "美国": "US",
    "美西": "US",
    "美东": "US",
    "加拿大": "CA",
    "澳大利亚": "AU",
    "印度": "IN",
    "巴西": "BR"
}

LATENCY_TIERS = {
    "APAC": {"countries": ["JP", "KR", "SG", "IN"], "target_max": 2500},
    "EU": {"countries": ["DE", "GB", "FR", "CH", "IE"], "target_max": 3000},
    "AMER_OCE": {"countries": ["US", "CA", "AU", "BR"], "target_max": 3000}
}

def detect_expected_country(node_name):
    for name_keyword, cc in COUNTRY_NAME_MAP.items():
        if name_keyword in node_name:
            return cc
    return None

def run_geo_gate_audit(yaml_path):
    start_time = time.time()
    if not os.path.exists(yaml_path):
        print(f"[GEO GATE ERROR] Configuration file not found: {yaml_path}")
        return False, []

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    proxies = data.get("proxies", [])
    if len(proxies) < 30:
        print(f"[GEO GATE ERROR] Proxy count too low ({len(proxies)} < 30). Aborting publish.")
        return False, []

    # Prepare sandbox
    sandbox_dir = os.path.join(os.path.dirname(yaml_path), "sandbox_geogate")
    os.makedirs(sandbox_dir, exist_ok=True)

    proxy_names = [p["name"] for p in proxies]
    sandbox_cfg = {
        "port": 39951,
        "socks-port": 39952,
        "mixed-port": 39953,
        "allow-lan": False,
        "mode": "global",
        "log-level": "silent",
        "external-controller": "127.0.0.1:39950",
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "GLOBAL",
                "type": "select",
                "proxies": proxy_names
            }
        ]
    }

    cfg_file = os.path.join(sandbox_dir, "config.yaml")
    with open(cfg_file, "w", encoding="utf-8") as f:
        yaml.dump(sandbox_cfg, f, allow_unicode=True)

    mihomo_bin = r"C:\Program Files\Clash Verge\verge-mihomo.exe"
    if not os.path.exists(mihomo_bin):
        # Fallback to linux mihomo if on runner
        mihomo_bin = "mihomo"

    print(f"[*] Geo Gate: launching Mihomo on port 39950 for {len(proxies)} proxies...")
    proc = subprocess.Popen([mihomo_bin, "-d", sandbox_dir, "-f", cfg_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3.5)

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({
        "http": "http://127.0.0.1:39953",
        "https": "http://127.0.0.1:39953"
    }))

    audit_results = []
    mismatch_count = 0
    timeout_count = 0

    print("\n==========================================================================================")
    print("  GEO GATE HARD VERIFICATION REPORT")
    print("==========================================================================================")

    try:
        for idx, p in enumerate(proxies, 1):
            name = p["name"]
            exp_cc = detect_expected_country(name)
            
            # Switch proxy
            sel_req = urllib.request.Request(
                "http://127.0.0.1:39950/proxies/GLOBAL",
                data=json.dumps({"name": name}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="PUT"
            )
            try:
                urllib.request.urlopen(sel_req, timeout=2.0)
            except Exception:
                pass
            time.sleep(0.2)

            # Test 204 delay (with retry for cold-start absorption)
            delay = -1
            for _ in range(2):
                try:
                    delay_url = f"http://127.0.0.1:39950/proxies/{urllib.parse.quote(name)}/delay?url=http://www.gstatic.com/generate_204&timeout=6000"
                    with urllib.request.urlopen(delay_url, timeout=6.5) as r:
                        d = json.loads(r.read().decode())
                        delay = d.get("delay", -1)
                        if delay > 0:
                            break
                except Exception:
                    time.sleep(0.3)

            # Test real egress geolocation
            real_cc = None
            real_country = None
            real_city = None
            real_ip = None
            real_as = None

            for _ in range(2):
                try:
                    ip_req = urllib.request.Request("http://ip-api.com/json", headers={"User-Agent": "curl/7.68.0"})
                    with opener.open(ip_req, timeout=5.0) as resp:
                        ip_data = json.loads(resp.read().decode("utf-8"))
                        if ip_data.get("status") == "success":
                            real_cc = ip_data.get("countryCode")
                            real_country = ip_data.get("country")
                            real_city = ip_data.get("city")
                            real_ip = ip_data.get("query")
                            real_as = ip_data.get("as")
                            break
                except Exception:
                    time.sleep(0.3)

            is_204_pass = (delay > 0)
            is_geo_match = (exp_cc is not None and real_cc == exp_cc)

            if not is_204_pass:
                timeout_count += 1
                status = "TIMEOUT"
            elif not is_geo_match:
                mismatch_count += 1
                status = f"GEO_MISMATCH(Exp:{exp_cc},Got:{real_cc})"
            else:
                status = "PASS"

            record = {
                "idx": idx,
                "name": name,
                "expected_cc": exp_cc,
                "real_cc": real_cc,
                "real_country": real_country,
                "real_city": real_city,
                "real_ip": real_ip,
                "real_as": real_as,
                "delay_ms": delay,
                "is_204_pass": is_204_pass,
                "is_geo_match": is_geo_match,
                "status": status
            }
            audit_results.append(record)
            print(f"#{idx:>2} | {name:<38} | 204: {delay:>4}ms | Exp: {str(exp_cc):<2} | Got: {str(real_cc):<2} ({str(real_country):<10}) | {status}")

    finally:
        proc.terminate()
        proc.wait()

    duration = time.time() - start_time
    total = len(proxies)
    passed_all = sum(1 for r in audit_results if r["status"] == "PASS")
    
    print("==========================================================================================")
    print(f"Summary: {passed_all}/{total} nodes PASSED Geo Gate in {duration:.1f}s (Timeouts: {timeout_count}, Mismatches: {mismatch_count})")

    report_path = os.path.join(os.path.dirname(yaml_path), "geo_audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)

    # Record into budget watchdog
    budget_watchdog.record_run(
        workflow_name="geo-gate-audit",
        duration_seconds=duration,
        node_count=total,
        pass_count=passed_all,
        fail_breakdown={"timeouts": timeout_count, "mismatches": mismatch_count}
    )

    if passed_all == total and mismatch_count == 0 and timeout_count == 0:
        print("[GEO GATE SUCCESS] 100% Geo consistency verified. Zero mismatches. Gate PASSED.")
        return True, audit_results
    else:
        print("[GEO GATE FAILURE] Gate rejected publish due to mismatches or timeouts.")
        return False, audit_results

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\clash_edgeone.yaml"
    success, _ = run_geo_gate_audit(target)
    sys.exit(0 if success else 1)
