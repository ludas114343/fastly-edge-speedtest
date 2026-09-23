import sys
import re
import json
import time
import urllib.request
import ssl
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m_id = re.search(r'SecretId:\s*`([^`]+)`', text)
m_key = re.search(r'SecretKey:\s*`([^`]+)`', text)
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

output = []

def log(s):
    output.append(s)
    print(s)

log("=== EDGEONE CAPABILITY PROBE ===")

# --- Part 1: Node Functions Probe (import net from "net") ---
log("\n[Part 1] EdgeOne Node Functions tcp-test Deployment Test...")

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
    req_mod = models.ModifyFunctionRequest()
    req_mod.ZoneId = zone_id
    req_mod.FunctionId = func_id
    req_mod.Remark = "Probe A3: Node Functions node:net"
    req_mod.Content = node_probe_code
    resp_mod = client.ModifyFunction(req_mod)
    log(f"ModifyFunction Success: {resp_mod.to_json_string()}")
except Exception as e:
    log(f"ModifyFunction Error: {str(e)}")

# Query endpoint to observe runtime reaction to Node syntax
time.sleep(3)
func_url = "https://edgeone-proxy-zone-3td4th92xk0e-1463384265.eo-edgefunctions1.com"
log(f"\nQuerying EdgeOne Function endpoint: {func_url} ...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    req_http = urllib.request.Request(func_url, headers={'User-Agent': 'Probe-EdgeOne/1.0'})
    with urllib.request.urlopen(req_http, timeout=10, context=ctx) as r:
        log(f"HTTP Status: {r.status}")
        log(f"Headers: {dict(r.getheaders())}")
        body = r.read().decode('utf-8', errors='replace')
        log(f"Response Body:\n{body}")
except urllib.error.HTTPError as he:
    log(f"HTTP Error {he.code}: {he.read().decode('utf-8', errors='replace')}")
except Exception as e:
    log(f"Request Error: {str(e)}")

# --- Part 2: Edge Functions Global Environment Audit ---
log("\n[Part 2] Edge Functions Native Capability & Global Environment Audit...")
# Re-check baseline globals probe that was executed earlier
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
    req_audit = models.ModifyFunctionRequest()
    req_audit.ZoneId = zone_id
    req_audit.FunctionId = func_id
    req_audit.Remark = "Capability Audit Probe"
    req_audit.Content = audit_code
    client.ModifyFunction(req_audit)
    time.sleep(3)
    req_h = urllib.request.Request(func_url, headers={'User-Agent': 'Probe-EdgeOne/1.0'})
    with urllib.request.urlopen(req_h, timeout=10, context=ctx) as r2:
        log(f"Audit Probe Status: {r2.status}")
        log(f"Audit Probe Body:\n{r2.read().decode('utf-8', errors='replace')}")
except Exception as e:
    log(f"Audit Probe Error: {str(e)}")

# --- Part 3: L4 Proxy Capability Test ---
log("\n[Part 3] EdgeOne L4 Proxy (Layer 4 TCP/UDP) Capability Test...")
try:
    req_l4 = models.DescribeL4ProxyRequest()
    req_l4.ZoneId = zone_id
    resp_l4 = client.DescribeL4Proxy(req_l4)
    log(f"DescribeL4Proxy: {resp_l4.to_json_string()}")
except Exception as e:
    log(f"DescribeL4Proxy Error: {str(e)}")

# Test CreateL4Proxy capability
log("\nTesting CreateL4Proxy API capability...")
try:
    req_create_l4 = models.CreateL4ProxyRequest()
    req_create_l4.ZoneId = zone_id
    req_create_l4.ProxyName = "probe-l4-test"
    req_create_l4.Area = "global"
    req_create_l4.Ipv6 = "off"
    resp_create = client.CreateL4Proxy(req_create_l4)
    log(f"CreateL4Proxy Success: {resp_create.to_json_string()}")
    # Delete if created
    new_proxy_id = resp_create.ProxyId
    req_del_l4 = models.DeleteL4ProxyRequest()
    req_del_l4.ZoneId = zone_id
    req_del_l4.ProxyId = new_proxy_id
    client.DeleteL4Proxy(req_del_l4)
    log(f"Deleted test L4 proxy {new_proxy_id}")
except Exception as e:
    log(f"CreateL4Proxy Error: {str(e)}")

os.makedirs('docs/probes', exist_ok=True)
with open('docs/probes/edgeone_raw.txt', 'w', encoding='utf-8') as f_out:
    f_out.write("\n".join(output))

log("\nSaved raw output to docs/probes/edgeone_raw.txt")
