import sys
import re
import json
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Supabase.*?`([A-Za-z0-9_.-]{30,})`', text)
if not m:
    print('Supabase token not found')
    sys.exit(1)

token = m.group(1).strip()

with open(r'configs/supabase/functions/edgetunnel/index.ts', 'r', encoding='utf-8') as f:
    source_code = f.read()

projects = [
    {'ref': 'theecyezvuzkflwikxwr', 'name': 'Singapore ap-southeast-1 (sb.ruoyemu.asia)'},
    {'ref': 'gwgiogtgdyrqlexcdjqm', 'name': 'Tokyo ap-northeast-1 (sb2.ruoyemu.asia)'}
]

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

for p in projects:
    ref = p['ref']
    print(f"\nDeploying Edge Function to Supabase project {ref} ({p['name']})...")
    payload = {
        'name': 'EdgeTunnel',
        'body': source_code,
        'verify_jwt': False
    }
    req = urllib.request.Request(
        f'https://api.supabase.com/v1/projects/{ref}/functions/edgetunnel',
        headers=headers,
        data=json.dumps(payload).encode('utf-8'),
        method='PATCH'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Deploy Success! Status: {resp.status}, Function ID: {data.get('id')}, Version: {data.get('version')}, Status: {data.get('status')}")
    except urllib.error.HTTPError as he:
        print(f"HTTPError {he.code}: {he.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"Error: {e}")
