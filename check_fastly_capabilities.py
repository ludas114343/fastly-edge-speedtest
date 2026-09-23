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
headers = {'Fastly-Key': token, 'Accept': 'application/json'}

def query(url, method='GET', data=None):
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        if data:
            req.data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as he:
        return {'error': he.code, 'msg': he.read().decode('utf-8', errors='replace')}
    except Exception as e:
        return {'error': str(e)}

print('=== 1. Current Customer / Account Info ===')
cust = query('https://api.fastly.com/current_customer')
print('Customer Name:', cust.get('name') if isinstance(cust, dict) else cust)
print('Pricing Plan:', cust.get('pricing_plan') if isinstance(cust, dict) else cust)
print('Can Compute:', cust.get('can_compute') if isinstance(cust, dict) else cust)

print('\n=== 2. List All Services ===')
services = query('https://api.fastly.com/service')
if isinstance(services, list):
    for s in services:
        print(f"Service ID={s.get('id')} Name={s.get('name')} Type={s.get('type')}")
else:
    print('Services:', services)

print('\n=== 3. Service 8K5HGyXmr8P6XuzRc5UPk0 Details ===')
svc = query('https://api.fastly.com/service/8K5HGyXmr8P6XuzRc5UPk0/details')
if isinstance(svc, dict) and 'active_version' in svc:
    act = svc['active_version']
    print(f"Active Version: {act.get('number')} (Deployed: {act.get('deployed')})")
    print(f"Backends ({len(act.get('backends', []))}):")
    for b in act.get('backends', []):
        print(f"  - {b.get('name')}: address={b.get('address')}:{b.get('port')} (override_host={b.get('override_host')})")
    print(f"Domains: {[d.get('name') for d in act.get('domains', [])]}")
    print(f"VCLs: {[v.get('name') for v in act.get('vcls', [])]}")
    print(f"Has Wasm Package: {'package' in act}")
else:
    print('Service details:', svc)
