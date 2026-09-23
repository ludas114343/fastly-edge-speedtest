# Task Card: agent-subscription-publisher (V13)

- Role: agent-subscription-publisher
- Subagent Type: DeepCoder
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - Public HTTPS subscription endpoints:
    1. https://speedtest.ludash.top/all (or workers.dev/raw GitHub pages/releases endpoint)
    2. https://speedtest.ludash.top/supabase
    3. https://speedtest.ludash.top/wasmer
    4. https://speedtest.ludash.top/northflank
    5. https://speedtest.ludash.top/cloudflare
    6. https://speedtest.ludash.top/fastly
    7. https://speedtest.ludash.top/netlify
    8. https://speedtest.ludash.top/edgeone
  - All 8 endpoints must return valid HTTP 200, valid TLS, valid YAML/Base64 format.
  - Zero-node platform endpoints must return valid YAML with proxies: [] and metadata.status: NO_VERIFIED_PROXY, unfinished: true.
  - Subscription metadata must contain full 40-character head_sha and run_id.

## Mandate & Scope
1. Implement and deploy atomic release structure (release/<run_id>/ and production/current.json).
2. Ensure endpoints are globally accessible via HTTPS, never local relative paths or localhost.
3. Verify that zero-node subscriptions explicitly state status: NO_VERIFIED_PROXY and unfinished: true.
4. Zero em-dash (\u2014) and zero en-dash (\u2013).
