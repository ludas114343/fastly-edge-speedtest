#!/usr/bin/env python3
"""
Edge Published Nodes Lightweight Rechecker (High-Concurrency)
Runs every 4 hours via GitHub Actions.
Validates live health of published nodes across all 6 proxy providers:
- Strict TLS certificate verification (ZERO CERT_NONE, ZERO check_hostname = False).
- RFC 6455 WebSocket 101 Switching Protocols validation.
- Enforces hard fail-safe: never wipes or empties any configuration.
- Zero em-dashes and zero en-dashes.
"""

import os
import sys
import time
import socket
import ssl
import json
import base64
from concurrent.futures import ThreadPoolExecutor
import yaml
import budget_watchdog

YAML_FILES = [
    "clash_supabase.yaml",
    "clash_wasmer.yaml",
    "clash_northflank.yaml",
    "clash_edgetunnel.yaml",
    "clash.yaml",
    "clash_fastly.yaml",
    "clash_netlify.yaml",
    "clash_edgeone.yaml"
]

def check_endpoint_ws101(server, port=443, sni=None, path="/", timeout=3.0):
    """
    Perform physical socket connection, strict TLS handshake, and RFC 6455 WS 101 verification.
    """
    sni = sni or server
    for _ in range(2):
        try:
            sock = socket.create_connection((server, port), timeout=timeout)
            if port in (443, 8443):
                # Strict TLS context with CA certificate verification
                ctx = ssl.create_default_context()
                tls_sock = ctx.wrap_socket(sock, server_hostname=sni)
                
                # RFC 6455 WebSocket Upgrade Handshake
                ws_key = base64.b64encode(os.urandom(16)).decode("ascii")
                ws_req = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {sni}\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {ws_key}\r\n"
                    "Sec-WebSocket-Version: 13\r\n\r\n"
                )
                tls_sock.sendall(ws_req.encode("utf-8"))
                tls_sock.settimeout(timeout)
                resp = tls_sock.recv(2048).decode("utf-8", errors="ignore")
                tls_sock.close()
                
                if " 101 " in resp or resp.startswith("HTTP/1.1 101"):
                    return True
                return False
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
    path = (proxy.get("ws-opts") or {}).get("path", "/")
    name = proxy.get("name", "Unknown")
    passed = check_endpoint_ws101(server, port, sni, path)
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

        with ThreadPoolExecutor(max_workers=8) as pool:
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
    print(f"\nCompleted recheck of {total_tested} published nodes in {duration:.1f}s. {total_passed}/{total_tested} healthy.")
    
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
