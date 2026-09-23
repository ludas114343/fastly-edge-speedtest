import urllib.request
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Supabase.*?`([A-Za-z0-9_.-]{30,})`', text)
if not m:
    print('Supabase token not found')
    sys.exit(1)

token = m.group(1).strip()

req = urllib.request.Request('https://api.supabase.com/v1/projects', headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        projects = json.loads(resp.read().decode('utf-8'))
        print(f'Supabase Projects ({len(projects)}):')
        for p in projects:
            ref = p.get('id')
            print(f"Project: Ref={ref} Name={p.get('name')} Region={p.get('region')} Status={p.get('status')}")
            # Check edge functions
            try:
                req_fn = urllib.request.Request(f'https://api.supabase.com/v1/projects/{ref}/functions', headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'})
                with urllib.request.urlopen(req_fn) as resp_fn:
                    fns = json.loads(resp_fn.read().decode('utf-8'))
                    print(f"  Functions ({len(fns)}):")
                    for fn in fns:
                        print(f"    Name={fn.get('name')} Slug={fn.get('slug')} Status={fn.get('status')} Version={fn.get('version')}")
            except Exception as e_fn:
                print('  Functions error:', e_fn)
except Exception as e:
    print('Supabase API err:', e)
