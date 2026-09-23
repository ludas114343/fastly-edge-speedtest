import sys, re, json
with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as cred_f:
    text = cred_f.read()
bt = chr(96)
m_id = re.search(r'SecretId:\s*' + bt + r'([^' + bt + r']+)' + bt, text)
m_key = re.search(r'SecretKey:\s*' + bt + r'([^' + bt + r']+)' + bt, text)
if not m_id or not m_key:
    print('Failed to find credentials')
    sys.exit(1)
secret_id = m_id.group(1).strip()
secret_key = m_key.group(1).strip()
from tencentcloud.common import credential
from tencentcloud.teo.v20220901 import teo_client, models
cred = credential.Credential(secret_id, secret_key)
client = teo_client.TeoClient(cred, 'ap-guangzhou')
zone_id = 'zone-3td4th92xk0e'
print('=== 1. DescribeFunctions ===')
try:
    req = models.DescribeFunctionsRequest()
    req.ZoneId = zone_id
    print(client.DescribeFunctions(req).to_json_string())
except Exception as e:
    print('DescribeFunctions error:', e)
print('=== 2. DescribeFunctionRules ===')
try:
    req = models.DescribeFunctionRulesRequest()
    req.ZoneId = zone_id
    print(client.DescribeFunctionRules(req).to_json_string())
except Exception as e:
    print('DescribeFunctionRules error:', e)
print('=== 3. DescribeFunctionRuntimeEnvironment ===')
try:
    req = models.DescribeFunctionRuntimeEnvironmentRequest()
    req.ZoneId = zone_id
    print(client.DescribeFunctionRuntimeEnvironment(req).to_json_string())
except Exception as e:
    print('DescribeFunctionRuntimeEnvironment error:', e)
print('=== 4. DescribeL4Proxy ===')
try:
    req = models.DescribeL4ProxyRequest()
    req.ZoneId = zone_id
    print(client.DescribeL4Proxy(req).to_json_string())
except Exception as e:
    print('DescribeL4Proxy error:', e)
print('=== 5. DescribeApplicationProxy ===')
try:
    req = models.DescribeApplicationProxyRequest()
    req.ZoneId = zone_id
    print(client.DescribeApplicationProxy(req).to_json_string())
except Exception as e:
    print('DescribeApplicationProxy error:', e)
