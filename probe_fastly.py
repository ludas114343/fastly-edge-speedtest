import urllib.request
import json
import re
import sys
import os
import ssl

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text)
if not m:
    print('Fastly token not found')
    sys.exit(1)

token = m.group(1).strip()
headers = {'Fastly-Key': token, 'Accept': 'application/json'}

output = []

def log(s):
    output.append(s)
    print(s)

log("=== FASTLY CAPABILITY PROBE ===")

# 1. Check if account can create / has access to Compute (wasm)
log("\n[Test 1] Testing Compute Service Creation Permission (type: wasm)...")
req_create = urllib.request.Request(
    'https://api.fastly.com/service',
    headers={'Fastly-Key': token, 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'},
    data=b'name=probe-compute-test&type=wasm',
    method='POST'
)
try:
    with urllib.request.urlopen(req_create) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        log(f"Create wasm service SUCCESS: ID={res.get('id')}, Type={res.get('type')}")
        # Clean up test service if created
        del_id = res.get('id')
        req_del = urllib.request.Request(f'https://api.fastly.com/service/{del_id}', headers=headers, method='DELETE')
        with urllib.request.urlopen(req_del) as dresp:
            log(f"Cleaned up test service {del_id}")
except urllib.error.HTTPError as he:
    err_body = he.read().decode('utf-8', errors='replace')
    log(f"Create wasm service HTTP {he.code}: {err_body}")
except Exception as e:
    log(f"Create wasm service Exception: {e}")

# 2. Check current VCL service 8K5HGyXmr8P6XuzRc5UPk0 configuration & backends
log("\n[Test 2] Examining Service 8K5HGyXmr8P6XuzRc5UPk0 Active Config...")
try:
    req_svc = urllib.request.Request('https://api.fastly.com/service/8K5HGyXmr8P6XuzRc5UPk0/details', headers=headers)
    with urllib.request.urlopen(req_svc) as resp:
        svc_details = json.loads(resp.read().decode('utf-8'))
        act = svc_details.get('active_version', {})
        log(f"Active Version: {act.get('number')}")
        log(f"Service Type: {svc_details.get('type')}")
        log(f"Domains: {[d.get('name') for d in act.get('domains', [])]}")
        log(f"Backends ({len(act.get('backends', []))}):")
        for b in act.get('backends', []):
            log(f"  - {b.get('name')}: {b.get('address')}:{b.get('port')} (override_host: {b.get('override_host')})")
except Exception as e:
    log(f"Service details error: {e}")

# 3. Dynamic Backend / Arbitrary Host Dialing Test
log("\n[Test 3] Dynamic Arbitrary Host Dialing / Routing Capability Test...")
# In Fastly, can we add a dynamic backend or does VCL require fixed backends?
# Let's test cloning version, attempting to configure dynamic backend or inspecting VCL backend limitations
try:
    # Check if dynamic backends feature flag is enabled on customer
    req_feat = urllib.request.Request('https://api.fastly.com/current_customer', headers=headers)
    with urllib.request.urlopen(req_feat) as resp:
        cust_data = json.loads(resp.read().decode('utf-8'))
        log(f"Customer Name: {cust_data.get('name')}")
        log(f"Pricing Plan: {cust_data.get('pricing_plan')}")
        log(f"Can Compute: {cust_data.get('can_compute')}")
        log(f"Can Dynamic Backends: {cust_data.get('can_dynamic_backends')}")
except Exception as e:
    log(f"Customer feature error: {e}")

# 4. Live Traffic Probe on Fastly Edge Domain ruoyemu.global.ssl.fastly.net
log("\n[Test 4] Live HTTP & WebSocket Probe on ruoyemu.global.ssl.fastly.net...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test 4a: Standard GET to Fastly domain
try:
    req_live = urllib.request.Request(
        'https://ruoyemu.global.ssl.fastly.net/',
        headers={'Host': 'ruoyemu.global.ssl.fastly.net', 'User-Agent': 'FastlyProbe/1.0'}
    )
    with urllib.request.urlopen(req_live, timeout=10, context=ctx) as r:
        log(f"Live GET status: {r.status}")
        log(f"Live GET headers: {dict(r.getheaders())}")
        body = r.read().decode('utf-8', errors='replace')
        log(f"Live GET body (first 200 chars): {body[:200]}")
except urllib.error.HTTPError as he:
    log(f"Live GET HTTP {he.code}: {he.read().decode('utf-8', errors='replace')[:200]}")
except Exception as e:
    log(f"Live GET error: {e}")

# Test 4b: WebSocket Upgrade Probe
log("\n[Test 5] Fastly WebSocket Upgrade Handshake Test...")
import socket
try:
    s = socket.create_connection(('ruoyemu.global.ssl.fastly.net', 443), timeout=10)
    ss = ctx.wrap_socket(s, server_hostname='ruoyemu.global.ssl.fastly.net')
    ws_req = (
        "GET /ws HTTP/1.1\r\n"
        "Host: ruoyemu.global.ssl.fastly.net\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    ss.sendall(ws_req.encode('utf-8'))
    resp_raw = ss.recv(2048).decode('utf-8', errors='replace')
    ss.close()
    log(f"WebSocket Upgrade Raw Response:\n{resp_raw}")
except Exception as e:
    log(f"WebSocket Upgrade error: {e}")

os.makedirs('docs/probes', exist_ok=True)
with open('docs/probes/fastly_raw.txt', 'w', encoding='utf-8') as f_out:
    f_out.write("\n".join(output))

log("\nSaved raw output to docs/probes/fastly_raw.txt")
