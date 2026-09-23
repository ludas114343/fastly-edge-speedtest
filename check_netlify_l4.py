import urllib.request
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Netlify.*?`([A-Za-z0-9_-]{30,})`', text)
if not m:
    print('Netlify token not found')
    sys.exit(1)

token = m.group(1).strip()

req = urllib.request.Request('https://api.netlify.com/api/v1/sites', headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        sites = json.loads(resp.read().decode('utf-8'))
        print(f'Netlify Sites ({len(sites)}):')
        for s in sites:
            print(f"Site: ID={s.get('id')} Name={s.get('name')} Url={s.get('url')} CustomDomain={s.get('custom_domain')}")
            # Check functions for each site
            site_id = s.get('id')
            try:
                req_fn = urllib.request.Request(f'https://api.netlify.com/api/v1/sites/{site_id}/functions', headers={'Authorization': f'Bearer {token}'})
                with urllib.request.urlopen(req_fn) as resp_fn:
                    fns = json.loads(resp_fn.read().decode('utf-8'))
                    print(f"  Functions ({len(fns)}): {fns}")
            except Exception as e_fn:
                print('  Functions error:', e_fn)
except Exception as e:
    print('Netlify API err:', e)
