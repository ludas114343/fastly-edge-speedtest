import urllib.request
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Northflank.*?`([A-Za-z0-9_.-]{30,})`', text)
if not m:
    print('Northflank token not found')
    sys.exit(1)

token = m.group(1).strip()

req = urllib.request.Request('https://api.northflank.com/v1/projects', headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        projects = json.loads(resp.read().decode('utf-8')).get('data', [])
        print(f'Northflank Projects ({len(projects)}):')
        for p in projects:
            proj_id = p.get('id')
            print(f"Project: ID={proj_id} Name={p.get('name')} Region={p.get('region')}")
            # Check services in project
            try:
                req_svc = urllib.request.Request(f'https://api.northflank.com/v1/projects/{proj_id}/services', headers={'Authorization': f'Bearer {token}'})
                with urllib.request.urlopen(req_svc) as resp_svc:
                    svcs = json.loads(resp_svc.read().decode('utf-8')).get('data', {}).get('services', [])
                    print(f"  Services ({len(svcs)}):")
                    for s in svcs:
                        print(f"    Service: ID={s.get('id')} Name={s.get('name')} Status={s.get('status')} Domains={s.get('ports', [{}])[0].get('dnsData')}")
            except Exception as e_svc:
                print('  Services error:', e_svc)
except Exception as e:
    print('Northflank API err:', e)
