import urllib.request
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text)
if not m:
    print('Fastly token not found')
    sys.exit(1)

token = m.group(1).strip()
service_id = '8K5HGyXmr8P6XuzRc5UPk0'
url = f'https://api.fastly.com/service/{service_id}/version/active'
req = urllib.request.Request(url, headers={'Fastly-Key': token, 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        active_ver = data.get('number')
        print(f'Fastly Service {service_id} Active Version: {active_ver}')
        
        # Check domains
        url_dom = f'https://api.fastly.com/service/{service_id}/version/{active_ver}/domain'
        req_dom = urllib.request.Request(url_dom, headers={'Fastly-Key': token, 'Accept': 'application/json'})
        with urllib.request.urlopen(req_dom) as resp_dom:
            domains = json.loads(resp_dom.read().decode('utf-8'))
            print('Domains:', [d.get('name') for d in domains])
            
        # Check backends
        url_be = f'https://api.fastly.com/service/{service_id}/version/{active_ver}/backend'
        req_be = urllib.request.Request(url_be, headers={'Fastly-Key': token, 'Accept': 'application/json'})
        with urllib.request.urlopen(req_be) as resp_be:
            bes = json.loads(resp_be.read().decode('utf-8'))
            for b in bes:
                print(f"Backend: Name={b.get('name')} Address={b.get('address')} Port={b.get('port')} HostHeader={b.get('override_host')}")
except Exception as e:
    print('Fastly API err:', e)
