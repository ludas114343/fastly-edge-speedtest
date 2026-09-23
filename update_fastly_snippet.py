import urllib.request
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

token = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text).group(1).strip()
service_id = '8K5HGyXmr8P6XuzRc5UPk0'
version = 16

headers = {
    'Fastly-Key': token,
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
}

new_routing_vcl = """
# 1. If subscription requested: route to Netlify real backend
if (req.url ~ "^/clash" || req.url ~ "^/sub") {
    set req.backend = F_backend_netlify;
    set req.http.Host = "gateway-core-net.netlify.app";
    return (pass);
}

# 2. If not websocket: deliver synthetic authentic Nginx disguise page
if (req.http.Upgrade !~ "(?i)websocket") {
    error 700 "Nginx Camouflage";
}

# 3. WebSocket proxy routing by regional path and real backends
if (req.url ~ "^/net" || req.url ~ "(?i)backend=netlify") {
    set req.backend = F_backend_netlify;
    set req.http.Host = "gateway-core-net.netlify.app";
} else if (req.url ~ "^/wasmer" || req.url ~ "^/w-la" || req.url ~ "(?i)backend=wasmer") {
    set req.backend = F_backend_wasmer;
    set req.http.Host = "edgetunnel-us-la.wasmer.app";
} else if (req.url ~ "^/de" || req.url ~ "(?i)country=de") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-central-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/fr" || req.url ~ "(?i)country=fr") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-west-3";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/uk" || req.url ~ "^/gb" || req.url ~ "(?i)country=gb") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-west-2";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/ch" || req.url ~ "(?i)country=ch") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-central-2";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/ie" || req.url ~ "(?i)country=ie") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=eu-west-1";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/jp" || req.url ~ "(?i)country=jp") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-northeast-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/kr" || req.url ~ "(?i)country=kr") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-northeast-2";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/sg" || req.url ~ "(?i)country=sg") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-southeast-1";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
} else if (req.url ~ "^/au" || req.url ~ "(?i)country=au") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ap-southeast-2";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/ca" || req.url ~ "(?i)country=ca") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=ca-central-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else if (req.url ~ "^/usw" || req.url ~ "(?i)country=usw") {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=us-west-1";
    set req.backend = F_backend_sb2;
    set req.http.Host = "gwgiogtgdyrqlexcdjqm.supabase.co";
} else {
    set req.url = "/functions/v1/edgetunnel?forceFunctionRegion=us-east-1";
    set req.backend = F_backend_sb1;
    set req.http.Host = "theecyezvuzkflwikxwr.supabase.co";
}

return (pass);
"""

# Update snippet
import urllib.parse
data = urllib.parse.urlencode({'content': new_routing_vcl}).encode('utf-8')
req = urllib.request.Request(
    f'https://api.fastly.com/service/{service_id}/version/{version}/snippet/edgetunnel_routing',
    headers=headers,
    data=data,
    method='PUT'
)
try:
    with urllib.request.urlopen(req) as resp:
        print("Update Snippet Status:", resp.status)
except urllib.error.HTTPError as he:
    print("Update Snippet Error:", he.code, he.read().decode())
    sys.exit(1)

# Validate
req_val = urllib.request.Request(
    f'https://api.fastly.com/service/{service_id}/version/{version}/validate',
    headers=headers
)
with urllib.request.urlopen(req_val) as resp:
    val_res = json.loads(resp.read().decode())
    print("Validate Status:", json.dumps(val_res, indent=2))

if val_res.get('status') == 'ok':
    # Activate
    req_act = urllib.request.Request(
        f'https://api.fastly.com/service/{service_id}/version/{version}/activate',
        headers=headers,
        method='PUT'
    )
    with urllib.request.urlopen(req_act) as resp:
        act_res = json.loads(resp.read().decode())
        print(f"Version {version} Successfully Activated!", json.dumps(act_res, indent=2))
