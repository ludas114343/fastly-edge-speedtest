import os
import sys
import re
import subprocess
import time
import urllib.request
import ssl

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'Netlify.*?`([A-Za-z0-9_-]{30,})`', text)
if not m:
    print('Error: Netlify token not found')
    sys.exit(1)

token = m.group(1).strip()
site_id = 'da52bbca-79fc-4a6b-9490-50620ae77332'

env = os.environ.copy()
env['NETLIFY_AUTH_TOKEN'] = token

probe_dir = os.path.abspath('probes/netlify_probe')
print(f'Starting Netlify deploy from {probe_dir}...')

cmd = [
    'pnpm.cmd', 'dlx', 'netlify', 'deploy',
    '--prod',
    '--dir', os.path.join(probe_dir, 'public'),
    '--site', site_id,
    '--auth', token,
    '--message', 'Probe A1: Netlify Edge Function tcp-test'
]

proc = subprocess.Popen(cmd, cwd=probe_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
stdout_lines = []
for line in proc.stdout:
    # Mask token if it appears anywhere in output
    safe_line = line.replace(token, '[REDACTED_TOKEN]')
    stdout_lines.append(safe_line)
    print(safe_line, end='', flush=True)

proc.wait()
stdout_text = ''.join(stdout_lines)

if proc.returncode != 0:
    print(f'Netlify deploy exited with code {proc.returncode}')

# Wait for deployment propagation
time.sleep(5)

# Test endpoint
endpoints = [
    'https://gateway-core-net.netlify.app/tcp-test',
    'https://net.ruoyemu.asia/tcp-test'
]

raw_output = []
raw_output.append(f"Deploy Return Code: {proc.returncode}")
raw_output.append(f"Deploy Output Summary:\n{stdout_text}\n")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for ep in endpoints:
    raw_output.append(f"--- Querying Endpoint: {ep} ---")
    try:
        req = urllib.request.Request(ep, headers={'User-Agent': 'Probe-Netlify/1.0'})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            status = resp.status
            headers = dict(resp.getheaders())
            body = resp.read().decode('utf-8', errors='replace')
            raw_output.append(f"HTTP Status: {status}")
            raw_output.append(f"Response Headers: {headers}")
            raw_output.append(f"Response Body:\n{body}")
            print(f"Success from {ep}: Status {status}, Body: {body[:200]}")
    except urllib.error.HTTPError as he:
        status = he.code
        body = he.read().decode('utf-8', errors='replace')
        raw_output.append(f"HTTP Error {status}: {body}")
        print(f"HTTP Error {status} from {ep}: {body[:200]}")
    except Exception as e:
        raw_output.append(f"Request Exception: {str(e)}")
        print(f"Exception from {ep}: {e}")

result_text = "\n".join(raw_output)
os.makedirs('docs/probes', exist_ok=True)
with open('docs/probes/netlify_raw.txt', 'w', encoding='utf-8') as out_f:
    out_f.write(result_text)

print("Saved raw output to docs/probes/netlify_raw.txt")
