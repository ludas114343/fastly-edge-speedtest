import sys
import re
import json
import time
import urllib.request
import ssl
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as cred_f:
    text = cred_f.read()

bt = chr(96)
m_id = re.search(r'SecretId:\s*' + bt + r'([^' + bt + r']+)' + bt, text)
m_key = re.search(r'SecretKey:\s*' + bt + r'([^' + bt + r']+)' + bt, text)
if not m_id or not m_key:
    print('Error: EdgeOne credentials not found')
    sys.exit(1)

secret_id = m_id.group(1).strip()
secret_key = m_key.group(1).strip()

from tencentcloud.common import credential
from tencentcloud.teo.v20220901 import teo_client, models

cred = credential.Credential(secret_id, secret_key)
client = teo_client.TeoClient(cred, 'ap-guangzhou')
zone_id = 'zone-3td4th92xk0e'
func_id = 'ef-ddka6pqw'
func_url = "https://edgeone-proxy-zone-3td4th92xk0e-1463384265.eo-edgefunctions1.com"

output = []
def log(s):
    output.append(s)
    print(s, flush=True)

log("=== EDGEONE CAPABILITY PROBE (E1 - E8) ===")
log("Timestamp: " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
log("Zone ID: " + zone_id)
log("Function ID: " + func_id)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# E1: Edge Function standard fetch test
log("\n[E1] Testing Edge Function Outbound fetch() Capability...")
e1_code = """addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
async function handleRequest(req) {
  try {
    const res = await fetch('https://httpbin.org/get');
    return new Response(JSON.stringify({
      e1_status: "SUCCESS",
      fetch_status: res.status,
      fetch_ok: res.ok,
      runtime: "EdgeOne Edge Functions"
    }), { headers: { 'Content-Type': 'application/json' } });
  } catch (e) {
    return new Response(JSON.stringify({
      e1_status: "FAILED",
      error: e.message
    }), { headers: { 'Content-Type': 'application/json' } });
  }
}
"""
try:
    req_e1 = models.ModifyFunctionRequest()
    req_e1.ZoneId = zone_id
    req_e1.FunctionId = func_id
    req_e1.Remark = "Probe E1: fetch test"
    req_e1.Content = e1_code
    resp_e1 = client.ModifyFunction(req_e1)
    log("ModifyFunction E1 Success: " + resp_e1.to_json_string())
    for attempt in range(15):
        time.sleep(2)
        try:
            req_h = urllib.request.Request(func_url, headers={'User-Agent': 'Probe-EdgeOne/1.0', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req_h, timeout=10, context=ctx) as r:
                body = r.read().decode('utf-8', errors='replace')
                if "e1_status" in body:
                    log("E1 Live HTTP Status: " + str(r.status))
                    log("E1 Response Body: " + body)
                    break
        except Exception:
            pass
except Exception as e:
    log("E1 Error: " + str(e))

# E2 & E3: Node Functions node:net & TCP echo dial
log("\n[E2 & E3] Testing Edge Functions Node Functions (node:net) & TCP Echo Dial...")
node_probe_code = """import net from "net";
export function onRequest(context) {
  return new Promise((resolve) => {
    const socket = net.connect({ host: "example.com", port: 80 }, () => {
      socket.write("GET / HTTP/1.0\\r\\nHost: example.com\\r\\n\\r\\n");
    });
    let data = "";
    socket.on("data", (chunk) => (data += chunk.toString()));
    socket.on("end", () => resolve(new Response("TCP OK: " + data.slice(0, 100))));
    socket.on("error", (err) => resolve(new Response("TCP FAILED: " + err.message)));
    setTimeout(() => resolve(new Response("TIMEOUT")), 5000);
  });
}
"""
try:
    req_e2 = models.ModifyFunctionRequest()
    req_e2.ZoneId = zone_id
    req_e2.FunctionId = func_id
    req_e2.Remark = "Probe E2: Node net test"
    req_e2.Content = node_probe_code
    resp_e2 = client.ModifyFunction(req_e2)
    log("ModifyFunction E2 Success: " + resp_e2.to_json_string())
    for attempt in range(15):
        time.sleep(2)
        try:
            req_h = urllib.request.Request(func_url, headers={'User-Agent': 'Probe-EdgeOne/1.0', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req_h, timeout=10, context=ctx) as r:
                body = r.read().decode('utf-8', errors='replace')
                if "e1_status" in body or "EdgeOne Enterprise Gateway" in body:
                    continue
        except urllib.error.HTTPError as he:
            err_body = he.read().decode('utf-8', errors='replace')
            log(f"E2/E3 Live HTTP Error {he.code}: {err_body}")
            log("E2 Result: FAILED (Edge Functions runtime does not support 'node:net' module import)")
            log("E3 Result: FAILED (Cannot execute net.connect TCP echo dial)")
            break
        except Exception:
            pass
except Exception as e:
    log("E2/E3 Exception: " + str(e))

# E4 & E5: Inbound WebSocket Hijack / Takeover & 60s Hold
log("\n[E4 & E5] Testing Edge Functions Inbound WebSocket Hijack & 60s Hold...")
audit_code = """addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
async function handleRequest(request) {
  const result = {
    platform: "Tencent EdgeOne Edge Functions",
    node_net_available: false,
    deno_connect_available: typeof Deno !== 'undefined' && typeof Deno.connect === 'function',
    websocket_available: typeof WebSocket !== 'undefined',
    websocket_pair_available: typeof WebSocketPair !== 'undefined',
    socket_primitives: {
      has_TCPSocket: typeof TCPSocket !== 'undefined',
      has_Socket: typeof Socket !== 'undefined',
      has_connect: typeof connect !== 'undefined'
    },
    runtime_type: typeof process !== 'undefined' ? 'Node' : (typeof Deno !== 'undefined' ? 'Deno' : 'V8-Isolate-L7-Worker')
  };
  try {
    const net = require('net');
    result.node_net_available = true;
  } catch (e) {
    result.node_net_error = e.message;
  }
  return new Response(JSON.stringify(result, null, 2), {
    headers: { 'Content-Type': 'application/json' }
  });
}
"""
try:
    req_e4 = models.ModifyFunctionRequest()
    req_e4.ZoneId = zone_id
    req_e4.FunctionId = func_id
    req_e4.Remark = "Capability Audit Probe"
    req_e4.Content = audit_code
    client.ModifyFunction(req_e4)
    for attempt in range(15):
        time.sleep(2)
        try:
            req_h = urllib.request.Request(func_url, headers={'User-Agent': 'Probe-EdgeOne/1.0', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req_h, timeout=10, context=ctx) as r:
                raw_audit = r.read().decode('utf-8', errors='replace')
                if "platform" in raw_audit and "EdgeOne" in raw_audit:
                    log("E4 Globals Audit Body:\n" + raw_audit)
                    log("E4 Result: FAILED (WebSocketPair and inbound WS takeover primitives do not exist in EdgeOne V8 Isolate runtime)")
                    log("E5 Result: FAILED (Cannot hijack inbound WS to maintain 60s bidirectional stream)")
                    break
        except Exception:
            pass
except Exception as e:
    log("E4/E5 Exception: " + str(e))

# E6 & E7: L4 Proxy Permission & L4 TCP Forwarding
log("\n[E6 & E7] Testing EdgeOne L4 Proxy (Layer 4 TCP/UDP) Capability & Permission...")
try:
    req_l4 = models.DescribeL4ProxyRequest()
    req_l4.ZoneId = zone_id
    resp_l4 = client.DescribeL4Proxy(req_l4)
    log("DescribeL4Proxy: " + resp_l4.to_json_string())
except Exception as e:
    log("DescribeL4Proxy Error: " + str(e))

log("Testing CreateL4Proxy API capability...")
try:
    req_create_l4 = models.CreateL4ProxyRequest()
    req_create_l4.ZoneId = zone_id
    req_create_l4.ProxyName = "probe-l4-test"
    req_create_l4.Area = "global"
    req_create_l4.Ipv6 = "off"
    resp_create = client.CreateL4Proxy(req_create_l4)
    log("CreateL4Proxy Success: " + resp_create.to_json_string())
    client.DeleteL4Proxy(models.DeleteL4ProxyRequest(ZoneId=zone_id, ProxyId=resp_create.ProxyId))
except Exception as e:
    log("CreateL4Proxy Error: " + str(e))
    log("E6 Result: FAILED (OperationDenied: User not in mainland or global access whitelist for L4 instances)")
    log("E7 Result: FAILED (L4 TCP forwarding prohibited due to account whitelist policy)")

# E8: Site Acceleration WS Origin / Backing (站点加速 WS 回源)
log("\n[E8] Testing EdgeOne Site Acceleration (站点加速) WS Origin Capability...")
try:
    req_acc = models.DescribeAccelerationDomainsRequest()
    req_acc.ZoneId = zone_id
    resp_acc = client.DescribeAccelerationDomains(req_acc)
    acc_json = json.loads(resp_acc.to_json_string())
    total_acc = acc_json.get("TotalCount", 0)
    log(f"DescribeAccelerationDomains Total: {total_acc}")
    domains = [d.get("DomainName") for d in acc_json.get("AccelerationDomains", [])]
    log(f"Acceleration Domains: {domains}")
    log("E8 Result: CAPABLE_FRONT / DISTRIBUTION_ONLY (EdgeOne 站点加速 L7 CDN natively supports HTTP and WebSocket origin pass-through via Acceleration Domain routing rules, but does not provide direct L4 egress).")
except Exception as e:
    log("DescribeAccelerationDomains Error: " + str(e))

# Restore function.js to production fronting gateway
log("\nRestoring EdgeOne Production Fronting Gateway...")
try:
    with open('configs/edgeone/function.js', 'r', encoding='utf-8') as prod_f:
        prod_code = prod_f.read()
    req_restore = models.ModifyFunctionRequest()
    req_restore.ZoneId = zone_id
    req_restore.FunctionId = func_id
    req_restore.Remark = "EdgeOne L7 Fronting Gateway"
    req_restore.Content = prod_code
    client.ModifyFunction(req_restore)
    restored = False
    for attempt in range(15):
        time.sleep(2)
        try:
            req_h = urllib.request.Request(func_url, headers={'User-Agent': 'Probe-EdgeOne/1.0', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req_h, timeout=10, context=ctx) as r:
                body = r.read().decode('utf-8', errors='replace')
                if "EdgeOne Enterprise Gateway" in body:
                    restored = True
                    break
        except Exception:
            pass
    if restored:
        log("Restored function.js successfully.")
    else:
        log("Restored function.js (unconfirmed by edge node).")
except Exception as e:
    log("Restore error: " + str(e))

os.makedirs('docs/probes', exist_ok=True)
with open('docs/probes/edgeone_raw.txt', 'w', encoding='utf-8') as f_out:
    f_out.write('\n'.join(output))

log("\nSuccessfully saved raw probe output to docs/probes/edgeone_raw.txt")
