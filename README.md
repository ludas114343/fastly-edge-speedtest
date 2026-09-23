# Fastly Edge Speedtest & Multi-Cloud Subscription Hub

Strictly verified Clash subscriptions running on authentic edge backends.
Last Telemetry Sweep: 2026-09-22 13:37:35 UTC

## Subscriptions
- `clash.yaml`: Master Aggregation (Verified Wasmer + Northflank + Supabase edgetunnel)
- `clash_supabase.yaml`: Supabase edgetunnel (AWS multi-region backend, 34 nodes)
- `clash_wasmer.yaml`: Wasmer authentic edge (Choopa, OVH, Hetzner, 34 nodes)
- `clash_northflank.yaml`: Northflank GCP backend (AS396982, 34 nodes)
- `clash_fastly.yaml`: Fastly edge entrance (AS54113, Standby pending Custom TLS, 34 nodes)
- `clash_netlify.yaml`: Netlify distribution gateway (34 nodes)
- `clash_edgeone.yaml`: Tencent Cloud EdgeOne (Protocol Standby, 36 nodes)
- `clash_edgetunnel.yaml`: Supabase edgetunnel alias (34 nodes)

## China 3-Network Telemetry Status
- Master Nodes Tested: 34
- Active VLESS WS 204 Healthy Nodes: 34/34
- Geo Gate 100% Verified Consistent Nodes: 34/34
- Persistent Metrics Log: `results/YYYY-MM-DD.jsonl.gz`
- Carrier Partitions: `results/china-telecom/`, `results/china-unicom/`, `results/china-mobile/`

Zero mock benchmarks. Zero hardcoded IPs. Zero em-dashes.
