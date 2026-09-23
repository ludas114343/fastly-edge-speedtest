import sys
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

for line in text.splitlines():
    if line.startswith('#'):
        print(line)
    elif any(k in line.lower() for k in ['wasmer', 'northflank', 'supabase', 'fastly', 'netlify', 'edgeone', 'cloudflare']):
        masked = re.sub(r'`[^`]+`', '`[REDACTED]`', line)
        print(masked)
