import urllib.request
import json
import re

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

token = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text).group(1).strip()
service_id = '8K5HGyXmr8P6XuzRc5UPk0'
headers = {'Fastly-Key': token, 'Accept': 'application/json'}

for item in ['snippet', 'vcl', 'request_settings', 'header']:
    req = urllib.request.Request(f'https://api.fastly.com/service/{service_id}/version/16/{item}', headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f'=== {item} ({len(data)}) ===')
            print(json.dumps(data, indent=2)[:600])
    except Exception as e:
        print(item, e)
