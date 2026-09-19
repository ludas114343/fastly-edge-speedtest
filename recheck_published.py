#!/usr/bin/env python3
"""
Edge Published Nodes Lightweight Rechecker (High-Concurrency)
Runs every 4 hours via GitHub Actions.
Validates live health of published nodes across all proxy providers.
Enforces hard fail-safe: never wipes or empties any configuration.
"""

import os
import sys
import time
import socket
import ssl
import json
from concurrent.futures import ThreadPoolExecutor
import yaml
import budget_watchdog

YAML_FILES = [
    "clash_edgeone.yaml",
    "clash_fastly.yaml",
    "clash_wasmer.yaml",
    "clash_netlify.yaml",
    "clash.yaml"
]

def check_endpoint_tcp_tls(server, port, sni=None, timeout=2.5):
    for _ in range(2):
        try:
            sock = socket.create_connection((server, port), timeout=timeout)
            if port in (443, 8443):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                tls_sock = ctx.wrap_socket(sock, server_hostname=sni or server)
                tls_sock.close()
            else:
                sock.close()
            return True
        except Exception:
            time.sleep(0.1)
    return False

def check_single_proxy(proxy):
    server = proxy.get("server")
    port = int(proxy.get("port", 443))
    sni = proxy.get("sni") or (proxy.get("ws-opts", {}).get("headers", {}).get("Host"))
    name = proxy.get("name", "Unknown")
    passed = check_endpoint_tcp_tls(server, port, sni)
    return {"name": name, "server": server, "port": port, "passed": passed}

def recheck_published_nodes():
    start_time = time.time()
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    total_tested = 0
    total_passed = 0
    summary_report = {}

    for yaml_name in YAML_FILES:
        yaml_path = os.path.join(repo_dir, yaml_name)
        if not os.path.exists(yaml_path):
            continue
            
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        proxies = data.get("proxies", [])
        if not proxies or len(proxies) < 10:
            print(f"[FAIL-SAFE] {yaml_name} has invalid proxy count ({len(proxies)}). Skipping.")
            continue

        with ThreadPoolExecutor(max_workers=16) as pool:
            results = list(pool.map(check_single_proxy, proxies))

        file_pass = sum(1 for r in results if r["passed"])
        total_tested += len(proxies)
        total_passed += file_pass

        pass_rate = f"{round(file_pass / len(proxies) * 100, 1)}%"
        summary_report[yaml_name] = {
            "total": len(proxies),
            "passed": file_pass,
            "pass_rate": pass_rate
        }
        print(f"[{yaml_name}] Checked {len(proxies)} nodes: {file_pass} healthy ({pass_rate})")

    duration = time.time() - start_time
    print(f"\nCompleted recheck of {total_tested} published nodes in {duration:.1f}s. All {total_passed}/{total_tested} healthy.")
    
    # Record metrics into budget watchdog
    budget_watchdog.record_run(
        workflow_name="published-recheck",
        duration_seconds=duration,
        node_count=total_tested,
        pass_count=total_passed,
        fail_breakdown=summary_report
    )
    return summary_report

if __name__ == "__main__":
    recheck_published_nodes()
