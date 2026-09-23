import sys
import re
import urllib.request
import json
import ssl

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Wasmer
m_wasmer = re.search(r'Wasmer.*?`([^`]+)`', text)
if m_wasmer:
    wasmer_tok = m_wasmer.group(1).strip()
    print(f"Wasmer token loaded: len={len(wasmer_tok)}, prefix={wasmer_tok[:4]}")
    # Wasmer GraphQL API
    req = urllib.request.Request(
        "https://registry.wasmer.io/graphql",
        headers={"Authorization": f"Bearer {wasmer_tok}", "Content-Type": "application/json"},
        data=json.dumps({"query": "{ viewer { username email apps(first: 10) { edges { node { id name activeVersion { id version createdAt } } } } } }"}).encode()
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            print("Wasmer GraphQL apps:", json.dumps(data, indent=2))
    except Exception as e:
        print("Wasmer GraphQL error:", e)

# 2. Supabase
m_sb = re.search(r'Supabase.*?`([A-Za-z0-9_.-]{30,})`', text)
if m_sb:
    sb_tok = m_sb.group(1).strip()
    print(f"Supabase token loaded: len={len(sb_tok)}")

# 3. Northflank
m_nf = re.search(r'Northflank.*?`([A-Za-z0-9_.-]{30,})`', text)
if m_nf:
    nf_tok = m_nf.group(1).strip()
    print(f"Northflank token loaded: len={len(nf_tok)}")

# 4. Fastly
m_fastly = re.search(r'Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`', text)
if m_fastly:
    fastly_tok = m_fastly.group(1).strip()
    print(f"Fastly token loaded: len={len(fastly_tok)}")

# 5. Netlify
m_net = re.search(r'Netlify.*?`([A-Za-z0-9_-]{30,})`', text)
if m_net:
    net_tok = m_net.group(1).strip()
    print(f"Netlify token loaded: len={len(net_tok)}")

# 6. EdgeOne
m_id = re.search(r'SecretId:\s*`([^`]+)`', text)
m_key = re.search(r'SecretKey:\s*`([^`]+)`', text)
if m_id and m_key:
    print(f"EdgeOne SecretId/SecretKey loaded: id_len={len(m_id.group(1).strip())}")
