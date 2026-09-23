import re
import json
from tencentcloud.common import credential
from tencentcloud.teo.v20220901 import teo_client, models

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

secret_id = re.search(r'SecretId:\s*`([^`]+)`', text).group(1).strip()
secret_key = re.search(r'SecretKey:\s*`([^`]+)`', text).group(1).strip()

cred = credential.Credential(secret_id, secret_key)
client = teo_client.TeoClient(cred, 'ap-guangzhou')
zone_id = 'zone-3td4th92xk0e'

# 1. Check Zone details
req_zone = models.DescribeZonesRequest()
req_zone.Filters = [models.AdvancedFilter()]
req_zone.Filters[0].Name = "zone-id"
req_zone.Filters[0].Values = [zone_id]
resp_zone = client.DescribeZones(req_zone)
print("Zone:", resp_zone.Zones[0].ZoneName, resp_zone.Zones[0].Status)

# 2. Check Acceleration Domains
req_dom = models.DescribeAccelerationDomainsRequest()
req_dom.ZoneId = zone_id
resp_dom = client.DescribeAccelerationDomains(req_dom)
print(f"Acceleration Domains ({len(resp_dom.AccelerationDomains)}):")
for d in resp_dom.AccelerationDomains:
    print(f"  - {d.DomainName}: Status={d.DomainStatus}, OriginType={d.OriginDetail.OriginType}, Origin={d.OriginDetail.Origin}")

# 3. Check Functions
req_fn = models.DescribeFunctionRequest()
req_fn.ZoneId = zone_id
resp_fn = client.DescribeFunction(req_fn)
print(f"Functions ({len(resp_fn.FunctionList)}):")
for f in resp_fn.FunctionList:
    print(f"  - {f.FunctionId} ({f.Name}): Status={f.FunctionType}")

# 4. Check Function Rules
req_rule = models.DescribeFunctionRulesRequest()
req_rule.ZoneId = zone_id
resp_rule = client.DescribeFunctionRules(req_rule)
print(f"Function Rules ({len(resp_rule.FunctionRules)}):")
for r in resp_rule.FunctionRules:
    print(f"  - {r.RuleId} ({r.FunctionId}): Priority={r.Priority}, Conditions={r.FunctionRuleConditions}")
