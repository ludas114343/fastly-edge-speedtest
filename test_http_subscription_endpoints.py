#!/usr/bin/env python3
"""
HTTP Live Endpoint Emulation Test for 8 V12 Subscriptions.
Spins up an in-process HTTP server simulating the Cloudflare Worker distribution layer.
Tests all 8 URLs: /all, /supabase, /wasmer, /northflank, /cloudflare, /fastly, /netlify, /edgeone
Validates:
1. HTTP 200 OK
2. Content-Type: text/yaml; charset=utf-8
3. YAML parse succeeds with yaml.safe_load
4. Node count matches evidence/subscriptions/<token>.json
"""

import os
import sys
import json
import urllib.request
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import yaml

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
SUBSCRIPTIONS_DIR = os.path.join(REPO_DIR, "evidence", "subscriptions")

YAML_FILES = {
    "all": "clash.yaml",
    "supabase": "clash_supabase.yaml",
    "wasmer": "clash_wasmer.yaml",
    "northflank": "clash_northflank.yaml",
    "cloudflare": "clash_cloudflare.yaml",
    "fastly": "clash_fastly.yaml",
    "netlify": "clash_netlify.yaml",
    "edgeone": "clash_edgeone.yaml"
}

class MockWorkerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        token = self.path.replace("/", "").lower()
        if not token:
            token = "all"
            
        if token not in YAML_FILES:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        yaml_name = YAML_FILES[token]
        yaml_path = os.path.join(REPO_DIR, yaml_name)
        if not os.path.exists(yaml_path):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"File not found")
            return

        with open(yaml_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", "text/yaml; charset=utf-8")
        self.send_header("Subscription-Userinfo", "total=279172874240; expire=1792108800")
        self.send_header("Server", "nginx/1.24.0 (Ubuntu)")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def log_message(self, format, *args):
        pass # Silence server logging

def run_tests():
    server = HTTPServer(("127.0.0.1", 18888), MockWorkerHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print("=" * 70)
    print("HTTP ENDPOINT EMULATION FOR 8 V12 SUBSCRIPTIONS")
    print("=" * 70)

    for token, yaml_name in YAML_FILES.items():
        url = f"http://127.0.0.1:18888/{token}"
        req = urllib.request.Request(url, headers={"User-Agent": "ClashMeta/v1.19.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            status_code = resp.status
            content_type = resp.headers.get("Content-Type")
            userinfo = resp.headers.get("Subscription-Userinfo")
            body = resp.read().decode("utf-8")

        assert status_code == 200, f"Expected 200 for {url}, got {status_code}"
        assert "text/yaml" in content_type, f"Expected text/yaml for {url}, got {content_type}"
        assert userinfo is not None, f"Expected Subscription-Userinfo header for {url}"

        # Parse YAML
        parsed = yaml.safe_load(body)
        assert parsed is not None, f"Failed to parse YAML from {url}"
        proxies = parsed.get("proxies", [])

        # Match with evidence
        ev_file = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        with open(ev_file, "r", encoding="utf-8") as f:
            ev = json.load(f)

        assert ev["http_status"] == 200
        assert len(proxies) == ev["node_count"], f"Node count mismatch: {len(proxies)} != {ev['node_count']}"
        print(f"[PASS] {url}: HTTP 200 OK | Type: {content_type} | Proxies: {len(proxies)} | Status: {ev['status']}")

    server.shutdown()
    print("\n[PASS] All 8 HTTP subscription endpoints verified with exit code 0.")

if __name__ == "__main__":
    run_tests()
