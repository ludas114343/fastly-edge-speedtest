import sys
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m_id = re.search(r'SecretId:\s*`([^`]+)`', text)
m_key = re.search(r'SecretKey:\s*`([^`]+)`', text)

from tencentcloud.common import credential
from tencentcloud.teo.v20220901 import teo_client, models

cred = credential.Credential(m_id.group(1).strip(), m_key.group(1).strip())
client = teo_client.TeoClient(cred, 'ap-guangzhou')

# Check what methods exist for AccelerationDomain
acc_methods = [m for m in dir(teo_client.TeoClient) if 'Acceleration' in m]
print('Acceleration methods:', acc_methods)
