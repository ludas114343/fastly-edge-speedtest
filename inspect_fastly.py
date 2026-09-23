import urllib.request
import json
import re

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()
token = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text).group(1).strip()
headers = {'Fastly-Key': token, 'Accept': 'application/json'}
req = urllib.request.Request('https://api.fastly.com/service/8K5HGyXmr8P6XuzRc5UPk0/details', headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    act = data.get('active_version', {})
    print('Version:', act.get('number'))
    print('Domains:', [d.get('name') for d in act.get('domains', [])])
    print('Backends:', [{b.get('name'): f"{b.get('address')}:{b.get('port')}"} for b in act.get('backends', [])])
    print('Headers:', [h.get('name') for h in act.get('headers', [])])
    print('Request Settings:', [r.get('name') for r in act.get('request_settings', [])])
