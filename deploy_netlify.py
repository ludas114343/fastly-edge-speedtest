import os
import sys
import re
import subprocess
import time

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

deploy_dir = os.path.abspath('configs/netlify')
print(f'Deploying Netlify VLESS Gateway from {deploy_dir}...')

cmd = [
    'pnpm.cmd', 'dlx', 'netlify', 'deploy',
    '--prod',
    '--dir', os.path.join(deploy_dir, 'public'),
    '--site', site_id,
    '--auth', token,
    '--message', 'V11 Release: Hardened Deno.connect VLESS Edge Function'
]

proc = subprocess.Popen(cmd, cwd=deploy_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
for line in proc.stdout:
    safe_line = line.replace(token, '[REDACTED_TOKEN]')
    print(safe_line, end='', flush=True)

proc.wait()
print(f'\nNetlify deploy finished with code: {proc.returncode}')
sys.exit(proc.returncode)
