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

zid = "zone-3td4th92xk0e"

req = models.CreateAccelerationDomainRequest()
req.ZoneId = zid
req.DomainName = "eo.ruoyemu.asia"
req.OriginProtocol = "FOLLOW"
req.HttpOriginPort = 80
req.HttpsOriginPort = 443
req.IPv6Status = "follow"

# OriginInfo
origin = models.OriginInfo()
origin.OriginType = "IP_DOMAIN"
origin.Origin = "1.1.1.1" # Dummy origin for edge function or CDN
req.OriginInfo = origin

try:
    resp = client.CreateAccelerationDomain(req)
    print("CreateAccelerationDomain SUCCESS:", resp.to_json_string())
except Exception as e:
    print("CreateAccelerationDomain error:", e)
