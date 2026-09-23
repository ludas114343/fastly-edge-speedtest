import urllib.request
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text)
if not m:
    print('Fastly token not found')
    sys.exit(1)

token = m.group(1).strip()
service_id = '8K5HGyXmr8P6XuzRc5UPk0'
headers = {
    'Fastly-Key': token,
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
}

def api_call(url, data=None, method=None):
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as he:
        body = he.read().decode(errors='replace')
        return he.code, body

# 1. Get current active version
status, svc = api_call(f'https://api.fastly.com/service/{service_id}/details', method='GET')
active_ver = svc.get('active_version', {}).get('number')
print(f"Current Active Version: {active_ver}")

# 2. Clone active version
status, clone_data = api_call(f'https://api.fastly.com/service/{service_id}/version/{active_ver}/clone', data=b'', method='PUT')
if status != 200:
    print(f"Failed to clone version: {status} {clone_data}")
    sys.exit(1)

new_ver = clone_data.get('number')
print(f"Cloned Version {active_ver} -> New Draft Version: {new_ver}")

# 3. Add domain fastly.ruoyemu.asia if not present
status, dom_res = api_call(
    f'https://api.fastly.com/service/{service_id}/version/{new_ver}/domain',
    data=b'name=fastly.ruoyemu.asia',
    method='POST'
)
print(f"Add domain fastly.ruoyemu.asia: {status}")

# 4. Remove backend_cf_sub (eliminate Cloudflare fronting)
status, del_res = api_call(
    f'https://api.fastly.com/service/{service_id}/version/{new_ver}/backend/backend_cf_sub',
    method='DELETE'
)
print(f"Delete backend_cf_sub: {status}")

# 5. Add backend_netlify (Netlify real backend)
netlify_data = (
    b'name=backend_netlify&address=gateway-core-net.netlify.app&port=443&'
    b'ssl_cert_hostname=gateway-core-net.netlify.app&ssl_sni_hostname=gateway-core-net.netlify.app&'
    b'override_host=gateway-core-net.netlify.app&use_ssl=1'
)
status, b_net = api_call(
    f'https://api.fastly.com/service/{service_id}/version/{new_ver}/backend',
    data=netlify_data,
    method='POST'
)
print(f"Add backend_netlify: {status}")

# 6. Add backend_wasmer (Wasmer real backend)
wasmer_data = (
    b'name=backend_wasmer&address=edgetunnel-us-la.wasmer.app&port=443&'
    b'ssl_cert_hostname=edgetunnel-us-la.wasmer.app&ssl_sni_hostname=edgetunnel-us-la.wasmer.app&'
    b'override_host=edgetunnel-us-la.wasmer.app&use_ssl=1'
)
status, b_was = api_call(
    f'https://api.fastly.com/service/{service_id}/version/{new_ver}/backend',
    data=wasmer_data,
    method='POST'
)
print(f"Add backend_wasmer: {status}")

# 7. Validate version
status, val_res = api_call(
    f'https://api.fastly.com/service/{service_id}/version/{new_ver}/validate',
    method='GET'
)
print(f"Validate Version {new_ver}: {status} {val_res}")

# 8. Activate new version
status, act_res = api_call(
    f'https://api.fastly.com/service/{service_id}/version/{new_ver}/activate',
    method='PUT'
)
print(f"Activate Version {new_ver}: {status} {act_res}")
