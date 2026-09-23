import sys
import re
import json
import time
import urllib.request
import ssl
from tencentcloud.common import credential
from tencentcloud.teo.v20220901 import teo_client, models

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

secret_id = re.search(r'SecretId:\s*`([^`]+)`', text).group(1).strip()
secret_key = re.search(r'SecretKey:\s*`([^`]+)`', text).group(1).strip()

cred = credential.Credential(secret_id, secret_key)
client = teo_client.TeoClient(cred, 'ap-guangzhou')
zone_id = 'zone-3td4th92xk0e'
func_id = 'ef-ddka6pqw'

with open(r'configs/edgeone/function.js', 'r', encoding='utf-8') as f:
    eo_function_code = f.read()

print(f"Deploying EdgeOne function {func_id} to zone {zone_id}...")
req_mod = models.ModifyFunctionRequest()
req_mod.ZoneId = zone_id
req_mod.FunctionId = func_id
req_mod.Remark = "V11 Release: Hardened L7 Fronting Reverse Proxy"
req_mod.Content = eo_function_code

try:
    resp = client.ModifyFunction(req_mod)
    print("ModifyFunction Success:", resp.to_json_string())
except Exception as e:
    print("ModifyFunction Error:", e)
    sys.exit(1)

time.sleep(3)
func_url = "https://edgeone-proxy-zone-3td4th92xk0e-1463384265.eo-edgefunctions1.com"
print(f"Testing EdgeOne function endpoint: {func_url} ...")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    req_http = urllib.request.Request(func_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_http, timeout=10, context=ctx) as r:
        print(f"HTTP Status: {r.status}")
        print(f"Headers: {dict(r.getheaders())}")
        print(f"Body: {r.read().decode('utf-8', errors='replace')[:200]}")
except Exception as e:
    print(f"Test error: {e}")
