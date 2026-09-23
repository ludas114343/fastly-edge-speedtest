import sys
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m_id = re.search(r'SecretId:\s*`([^`]+)`', text)
m_key = re.search(r'SecretKey:\s*`([^`]+)`', text)

secret_id = m_id.group(1).strip()
secret_key = m_key.group(1).strip()

from tencentcloud.common import credential
from tencentcloud.teo.v20220901 import teo_client, models

cred = credential.Credential(secret_id, secret_key)
client = teo_client.TeoClient(cred, 'ap-guangzhou')

req = models.DescribeZonesRequest()
resp = client.DescribeZones(req)
data = json.loads(resp.to_json_string())

# Redact any sensitive tokens
def redact(obj):
    if isinstance(obj, dict):
        return {k: redact(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [redact(v) for v in obj]
    elif isinstance(obj, str) and len(obj) > 30 and ('sec' in obj.lower() or 'key' in obj.lower()):
        return '[REDACTED]'
    return obj

print(json.dumps(redact(data), indent=2, ensure_ascii=False))
