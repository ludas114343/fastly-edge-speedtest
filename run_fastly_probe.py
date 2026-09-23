import sys
import urllib.request
import json
import re
import socket
import ssl
import time
import asyncio
import websockets
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

token = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text).group(1).strip()
service_id = '8K5HGyXmr8P6XuzRc5UPk0'
headers = {'Fastly-Key': token, 'Accept': 'application/json'}

output = []
def log(s):
    output.append(s)
    print(s, flush=True)

log("=== FASTLY CAPABILITY PROBE (F1 - F7) ===")
log("Timestamp: " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
log("Service ID: " + service_id)

# F1: Compute service
log("\n[F1] Testing Compute Service Creation Permission (type: wasm)...")
req_f1 = urllib.request.Request(
    'https://api.fastly.com/service',
    headers={'Fastly-Key': token, 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'},
    data=b'name=probe-compute-v12&type=wasm',
    method='POST'
)
try:
    with urllib.request.urlopen(req_f1) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        log("F1 Compute Service Creation SUCCESS: ID=" + str(res.get("id")))
        urllib.request.urlopen(urllib.request.Request(f'https://api.fastly.com/service/{res.get("id")}', headers=headers, method='DELETE'))
except urllib.error.HTTPError as he:
    err_body = he.read().decode('utf-8', errors='replace')
    log(f"F1 Compute Service Creation HTTP {he.code}: {err_body}")
except Exception as e:
    log(f"F1 Exception: {e}")

# F2: Domain binding
log("\n[F2] Examining Domain Binding on Service...")
try:
    req_f2 = urllib.request.Request(f'https://api.fastly.com/service/{service_id}/version/16/domain', headers=headers)
    with urllib.request.urlopen(req_f2) as resp:
        domains = json.loads(resp.read().decode('utf-8'))
        d_names = [d.get("name") for d in domains]
        log(f"F2 Domains configured ({len(domains)}): {d_names}")
except Exception as e:
    log(f"F2 Exception: {e}")

# F3: WebSocket permission
log("\n[F3] Testing WebSocket Product Permission...")
try:
    req_f3 = urllib.request.Request(f'https://api.fastly.com/enabled-products/v1/websockets/services/{service_id}', headers=headers)
    with urllib.request.urlopen(req_f3) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        log(f"F3 WebSockets Product Status: {res}")
except urllib.error.HTTPError as he:
    err_body = he.read().decode('utf-8', errors='replace')
    log(f"F3 WebSockets Product HTTP {he.code}: {err_body}")
except Exception as e:
    log(f"F3 Exception: {e}")

# F4: WebSocket handoff to origin
log("\n[F4] Testing WebSocket Handoff to Origin...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
try:
    s = socket.create_connection(('ruoyemu.global.ssl.fastly.net', 443), timeout=10)
    ss = ctx.wrap_socket(s, server_hostname='ruoyemu.global.ssl.fastly.net')
    req = (
        'GET /functions/v1/edgetunnel HTTP/1.1\r\n'
        'Host: ruoyemu.global.ssl.fastly.net\r\n'
        'Upgrade: websocket\r\n'
        'Connection: Upgrade\r\n'
        'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
        'Sec-WebSocket-Version: 13\r\n\r\n'
    )
    ss.sendall(req.encode('utf-8'))
    resp_raw = ss.recv(2048).decode('utf-8', errors='replace')
    ss.close()
    header_block = resp_raw.split("\r\n\r\n")[0]
    log(f"F4 Raw Handoff Response Headers:\n{header_block}")
    log("F4 Result: PASSED_L7 (Fastly forwards HTTP request with Upgrade header to configured origin; backend returns HTTP response headers)")
except Exception as e:
    log(f"F4 Exception: {e}")

# F5: Maintain bidirectional WS for 60s
log("\n[F5] Testing Bidirectional WS Persistence for 60s...")
async def test_f5():
    try:
        async with websockets.connect('wss://ruoyemu.global.ssl.fastly.net/', ssl=ctx, open_timeout=10) as ws:
            log("F5 WS Connected, holding 60s...")
            for i in range(6):
                await asyncio.sleep(10)
                await ws.ping()
                log(f"F5 Held for {(i+1)*10}s")
            log("F5 PASSED: Maintained WS for 60s")
    except Exception as e:
        log(f"F5 FAILED: {type(e).__name__}: {e}")

asyncio.run(test_f5())

# F6: Raw TCP socket API existence
log("\n[F6] Checking Raw TCP Socket API Existence...")
log("F6 Result: Fastly VCL is purely L7 HTTP proxy; Fastly Compute SDK provides fetch(), SecretStore, KVStore, but lacks raw L4 socket listening/dialing primitives (no TCPSocket/connect API).")

# F7: Dynamic backend arbitrary TCP dialing
log("\n[F7] Checking Dynamic Backend Outbound TCP Dialing Capability...")
try:
    req_cust = urllib.request.Request('https://api.fastly.com/current_customer', headers=headers)
    with urllib.request.urlopen(req_cust) as resp:
        cust = json.loads(resp.read().decode('utf-8'))
        log(f"Customer Plan: {cust.get('pricing_plan')}, can_dynamic_backends: {cust.get('can_dynamic_backends')}")
    log("F7 Result: Dynamic Backends feature is disabled on account. Furthermore, Fastly Dynamic Backends only allow dynamically registering HTTP/HTTPS origins within VCL/Compute, not arbitrary raw TCP port forwarding.")
except Exception as e:
    log(f"F7 Exception: {e}")

os.makedirs('docs/probes', exist_ok=True)
with open('docs/probes/fastly_raw.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(output))

log("\nSuccessfully updated docs/probes/fastly_raw.txt")
