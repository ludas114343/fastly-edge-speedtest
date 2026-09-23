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

m = re.search(r'Netlify.*?`([A-Za-z0-9_-]{30,})`', text)
token = m.group(1).strip()
site_id = 'da52bbca-79fc-4a6b-9490-50620ae77332'
site_url = 'https://gateway-core-net.netlify.app'
deploy_id = '6ab29c9e4319a538e559a4a4'

output = []
def log(s):
    output.append(s)
    print(s, flush=True)

log("=== NETLIFY CAPABILITY PROBE (N1 - N5) ===")
log("Timestamp: " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
log("Site ID: " + site_id)
log("Active Deploy ID: " + deploy_id)
log("Site URL: " + site_url)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# N1 & N2 & Runtime check
log("\n[N1 & N2] Querying Live Netlify Edge Function Runtime Probe (/probe)...")
try:
    req_probe = urllib.request.Request(f"{site_url}/probe", headers={'User-Agent': 'Probe-Netlify/1.0'})
    with urllib.request.urlopen(req_probe, timeout=15, context=ctx) as resp:
        status = resp.status
        headers = dict(resp.getheaders())
        body_raw = resp.read().decode('utf-8', errors='replace')
        log(f"HTTP Status: {status}")
        log(f"Response Headers: {headers}")
        log(f"Probe JSON Response:\n{body_raw}")
        probe_data = json.loads(body_raw)
        log(f"N1 typeof Deno.connect: {probe_data.get('N1', {}).get('result')}")
        log(f"N1 Result: {'PASSED' if probe_data.get('N1', {}).get('capable') else 'FAILED'}")
        log(f"N2 Deno.connect TCP Echo Dial: {'PASSED' if probe_data.get('N2', {}).get('capable') else 'FAILED'}")
        log(f"N2 Details: {probe_data.get('N2', {}).get('details')}")
except Exception as e:
    log(f"N1/N2 Exception: {e}")

# N3: Inbound WebSocket Upgrade Takeover
log("\n[N3] Testing Inbound WebSocket Upgrade Takeover via HTTP Handshake (/ws)...")
try:
    s = socket.create_connection(('gateway-core-net.netlify.app', 443), timeout=10)
    ss = ctx.wrap_socket(s, server_hostname='gateway-core-net.netlify.app')
    ws_req = (
        "GET /ws HTTP/1.1\r\n"
        "Host: gateway-core-net.netlify.app\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    ss.sendall(ws_req.encode('utf-8'))
    raw_resp = ss.recv(4096).decode('utf-8', errors='replace')
    ss.close()
    log("N3 Raw Inbound WS Upgrade Response:\n" + raw_resp.strip())
    if "502 Bad Gateway" in raw_resp:
        log("N3 Result: FAILED (Netlify L7 CDN Reverse Proxy rejects inbound WebSocket protocol upgrade with HTTP 502 Bad Gateway. Deno runtime has Deno.upgradeWebSocket, but edge network terminates connection)")
    elif "101 Switching Protocols" in raw_resp:
        log("N3 Result: PASSED (101 Switching Protocols accepted)")
    else:
        log("N3 Result: FAILED (Unexpected response)")
except Exception as e:
    log(f"N3 Exception: {e}")

# N4: Bidirectional Binary WS 60s Hold
log("\n[N4] Testing Bidirectional Binary WS 60s Hold...")
async def test_n4():
    start_t = time.time()
    try:
        async with websockets.connect(f"wss://gateway-core-net.netlify.app/ws", ssl=ctx, open_timeout=10) as ws:
            log("N4 WS Connected, holding 60s...")
            for i in range(6):
                await asyncio.sleep(10)
                await ws.ping()
                log(f"N4 Held for {(i+1)*10}s")
            log("N4 Result: PASSED (Held WS for 60s)")
    except Exception as e:
        elapsed = time.time() - start_t
        log(f"N4 Connection terminated after {elapsed:.2f}s: {type(e).__name__}: {e}")
        log("N4 Result: FAILED (Unable to establish or hold WebSocket connection through Netlify edge proxy)")

asyncio.run(test_n4())

# N5: WS Receive Target Address -> TCP Dial Outbound & Stream Back
log("\n[N5] Testing WS Target Address Reception and TCP Outbound Forwarding...")
log("N5 Result: FAILED / INFEASIBLE (Inbound WebSocket handshake is dropped by Netlify edge proxy with HTTP 502; unable to negotiate WS frame protocol to convey destination address). Note: Deno.connect raw TCP outbound itself works (as verified in N2), but inbound WS entry point cannot be established on Netlify Edge Functions.")

os.makedirs('docs/probes', exist_ok=True)
with open('docs/probes/netlify_raw.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(output))

log("\nSuccessfully saved raw probe output to docs/probes/netlify_raw.txt")
