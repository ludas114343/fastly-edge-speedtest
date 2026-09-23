# V11 Full Platform Refactoring: Historical Context Recovery & Architecture Baseline

- **Target Workspace**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **Output Document**: `docs/context_recovery.md`
- **Role**: study (Source Porting Analyst Subagent)
- **Mandate**: TASK-004-PORTING-STUDY

---

## 1. Executive Summary and Purpose

This document establishes the authoritative historical and architectural recovery baseline for the V11 Full Platform Refactoring initiative. It reconciles past project milestones (V1 through V10), forensic post-mortems, credential vaults, local file assets, and adversarial red team audits into a single, cohesive source of truth.

The primary mandate of V11 is the total elimination of "Cloudflare Fronting" (套壳), fake latency calculations, hardcoded Anycast IPs, and shared wildcard domain dependencies. In their place, V11 installs verified native outbound backends (`CAPABLE_DIRECT`), disciplined frontends (`CAPABLE_FRONT`), and a rigorous, multi-tiered probing and selection engine.

---

## 2. Chronological Evolution & Forensic Autopsy

### 2.1 The Genesis (V1 to V7): Rapid Prototyping & Technical Debt Accumulation
During initial iterations, the repository aimed to establish multi-cloud edge acceleration across Fastly, Wasmer, Netlify, Supabase, and Tencent EdgeOne. However, shortcuts were introduced:
- Hardcoded Cloudflare Anycast IP addresses (`104.16.x.x`, `172.64.149.246`, `104.18.38.10`) were embedded into YAML subscription nodes pretending to be independent cloud providers.
- Shared wildcard domains (e.g. `ruoyemu.global.ssl.fastly.net`, `ruoyemu.freetls.fastly.net`) were used as node SNIs to bypass custom TLS certificate provisioning.
- `speedtest.py` assigned arbitrary static bandwidth numbers (e.g. `avg_rtt < 60 -> 35Mbps`) rather than measuring actual payload throughput.
- All custom subdomains in `ruoyemu.asia` (`net`, `w-la`, `w-fr`, `eo`, `nf-node`) were proxied through Cloudflare Orange Cloud (AS13335).

### 2.2 The 2026-09-21 Forensic Autopsy (`forensics_cf_fronting.md`)
On September 21, 2026, an adversarial Red Team forensic investigation (`orchestration/forensics_cf_fronting.md`) thoroughly investigated user suspicions that "Fastly and other edge nodes were merely reskinned Cloudflare proxies":

1. **Fastly Doppelganger Reality**:
   - Fastly Service `8K5HGyXmr8P6XuzRc5UPk0` had never possessed a valid custom TLS certificate for `fastly.ruoyemu.asia`. Direct handshakes returned `HTTP/1.1 421 Misdirected Request`.
   - The configuration relied on shared FreeTLS domain `ruoyemu.global.ssl.fastly.net`, routing directly into Supabase edgetunnel and Cloudflare Workers.
2. **Fleet-Wide AS13335 Contamination**:
   - `clash_wasmer.yaml`: 31 out of 34 nodes (91.2%) hardcoded Cloudflare Anycast IP `172.64.149.246` (AS13335).
   - `clash_netlify.yaml`: Nodes used AWS Anycast IPs with SNI `net.ruoyemu.asia`, which was orange-cloud proxied through Cloudflare.
   - `clash_edgeone.yaml`: Subdomain `eo.ruoyemu.asia` was orange-cloud proxied with AAAA record `100::`.
3. **Official Red Team Verdict**:
   - The implementation was formally convicted of Cloudflare Fronting and Doppelganger Camouflage ("锤实套壳").

### 2.3 The V8 DeepCoder Reconstruction (`V8_deepcoder_report.md`)
In response to the forensic autopsy, the V8 reconstruction executed four emergency decontamination steps:
1. **Cloudflare Grey-Clouding (`proxied: false`)**: Set all custom subdomains (`w-la`, `w-fr`, `w-east`, `w-us`, `nf-node`, `net`) to grey-cloud direct DNS. Public DNS resolution shifted immediately to authentic host IPs:
   - `w-la.ruoyemu.asia` -> `45.32.93.23` (Choopa / Vultr AS20473, US West / Los Angeles)
   - `w-fr.ruoyemu.asia` -> `91.134.68.236` (OVH AS16276, France / Paris)
   - `w-east.ruoyemu.asia` -> `5.161.23.223` (Hetzner AS213230, US East / Ashburn)
   - `w-us.ruoyemu.asia` -> `5.78.30.216` (Hetzner AS212317, US West / Hillsboro)
   - `nf-node.ruoyemu.asia` -> `35.193.113.78` (Google Cloud Platform AS15169, Northflank)
2. **Reconstruction of Clash Subscriptions**: Eradicated hardcoded IPs, wiped out shared wildcard domains, and enforced Quad-Match (`server == sni == Host == SAN`).
3. **Speedtest Sanitization**: Removed simulated latency tables and placeholder benchmark routines.
4. **Subscription Partitioning**: Formally separated operational direct backends (Wasmer, Northflank, Supabase) from frozen frontends (Fastly pending custom TLS, Netlify standby, EdgeOne standby).

### 2.4 The V11 Full Platform Refactoring Charter
The V11 refactoring (`orchestration/ledger.md`) codifies an absolute adversarial methodology governed by the rule: **"Default Untrusted" (默认不可信)**. All previous claims of "deployed", "tested", or "operational" were reset to zero. Progress requires physical evidence, subagent execution, taskcards, and independent auditor signoff.

---

## 3. V11 Architectural Principles & Non-Negotiable Red Lines

1. **Definition of Done (DoD) Enforced**:
   - Writing code is never completion. Every component must be verified with active terminal executions (exit code 0). Oral claims of completion are strictly prohibited.
2. **Three-State Platform Classification**:
   - `CAPABLE_DIRECT`: Backend possesses native outbound TCP sockets and public ingress. Mandated for Supabase (Deno), Wasmer (Node.js), and Northflank (Go).
   - `CAPABLE_FRONT`: Edge platform serves exclusively as an Anycast CDN L7 reverse proxy. Must be transparently labeled as "Frontend -> True Backend" and never misrepresented as an independent physical egress.
   - `INCAPABLE`: Platform sandbox completely forbids outbound raw sockets and WebSocket upgrades (e.g. EdgeOne standard Node functions without L4).
3. **Strict Quad-Match Requirement**:
   `server == sni == Host == SAN`. Zero domain fronting or CNAME disguises across all node definitions.
4. **Zero Cloudflare AS13335 Bleed-Through**:
   Zero Cloudflare IPs permitted in Wasmer, Northflank, Fastly, Netlify, or EdgeOne subscription configurations.
5. **Zero-Detour Geo Gate Standard**:
   A node declared as Hong Kong, Japan, Singapore, or Germany must physically exit from an IP geolocated in that exact country. Trans-oceanic routing detours result in instant disqualification.
6. **Zero Credential Leakage & Token Security**:
   All GitHub OAuth tokens, API keys, and platform passwords must be read from external stores (`D:\Obsidian\CollegeAid\planning\平台凭据速查.md`) into ephemeral memory variables only. Zero cleartext secrets may be written to disk, committed to Git, or output to console logs.
7. **Absolute Host Network Safety**:
   The host machine's local network, Clash Verge instance, TUN adapter, and proxy ports (e.g. 7897) must remain completely untouched. All active testing is confined to dedicated high loopback sandbox ports (39950 to 39953).

---

## 4. Local Workspace File Asset Inventory

The repository `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest` is organized as follows:

```
fastly-edge-speedtest/
├── docs/                                 # Architectural & Porting Documentation (TASK-004)
│   ├── edgetunnel_porting_map.md         # zizifn & cmliu _worker.js function-level mapping
│   ├── denovless_porting_map.md          # Tintac-CN Deno & Supabase Edge Functions mapping
│   ├── runtime_direct_map.md             # Wasmer Node.js & Northflank Go direct paradigms
│   ├── trace_web_porting_map.md          # Trace-Web layered probing & scoring engine mapping
│   ├── trace_web_study.md                # In-depth analysis of trace.py algorithms
│   └── context_recovery.md               # Historical baseline & architectural recovery (this doc)
├── orchestration/                        # Governance, Ledgers, and Adversarial Audit Reports
│   ├── ledger.md                         # Master execution ledger for all V11 stages
│   ├── bootstrap_report.md               # S0 bootstrap environment check report
│   ├── forensics_cf_fronting.md          # Chapter 3 forensic autopsy of Cloudflare fronting
│   ├── V8_deepcoder_report.md            # V8 reconstruction & sanitization report
│   ├── S1_audit_report.md / _v2.md       # S1 code auditor reviews
│   ├── S1_redteam_report.md / _v2.md     # S1 adversarial red team challenges
│   ├── S2_backend_report.md / _v2.md     # S2 backend deployment reports
│   └── S2_redteam_report.md / _v2.md     # S2 backend adversarial penetration reviews
├── taskcards/                            # Formal Subagent Task Cards
│   ├── TASK-000-DISPATCH-CHECK.md        # Gate 0 Subagent dispatch probe
│   ├── TASK-001-PLATFORM-CAPABILITY-PROBE.md # Stage A platform capability probing
│   ├── TASK-002-DIRECT-BACKEND-DEPLOY.md # Stage B direct backend deployment
│   ├── TASK-003-FRONT-OR-DIRECT-DEPLOY.md# Stage B frontend/relay deployment
│   ├── TASK-004-PORTING-STUDY.md         # Stage S1/Porting documentation study
│   ├── TASK-005-CHINA-SPEEDTEST-PIPELINE.md # Stage C multi-carrier China speedtest
│   ├── TASK-006-AUDIT-CODE-AND-SECURITY.md # Stage D code & security audit
│   └── TASK-007-AUDIT-NET-AND-REDTEAM.md # Stage D network & red team audit
├── configs/                              # Platform Configurations and Deployment Blueprints
│   ├── supabase/                         # Deno TypeScript edge function configs
│   ├── wasmer/                           # Node.js / WASIX gateway server configs
│   └── northflank/                       # Go singbox-lite service and Dockerfile
├── results/                              # Benchmarking and Telemetry Storage
│   └── china-telecom/ / unicom/ / mobile/# Multi-carrier China-line test logs
├── sandbox_geogate/                      # Ephemeral Isolated Mihomo Sandbox (Ports 39950-39953)
├── speedtest.py                          # Multi-tier physical probe & benchmark engine
├── geo_gate_verify.py                    # Egress country consistency & detour verification gate
├── generate_all_pools.py                 # Multi-platform candidate aggregator & subnet slimmer
├── build_reconstructed_yamls.py          # Strict Quad-Match Clash YAML synthesizer
├── budget_watchdog.py                    # Quota monitor and node replacement watchdog
├── cf_dns_manager.py                     # Automated Cloudflare DNS grey-cloud API controller
├── uuid_config.json                      # Segregated UUID mapping per platform
├── quota_guard.json                      # Geographic node quota constraints (34/36 nodes)
├── clash_wasmer.yaml                     # Wasmer 34-node verified subscription
├── clash_edgetunnel.yaml                 # Supabase edgetunnel 34-node subscription
├── clash_fastly.yaml                     # Fastly 34-node subscription (Frozen pending Custom TLS)
├── clash_netlify.yaml                    # Netlify 34-node subscription (Fronting Gateway)
├── clash_edgeone.yaml                    # Tencent EdgeOne 36-node subscription (L7 Gateway)
└── clash.yaml                            # Master aggregated 34-node subscription
```

---

## 5. Historical Red Team Findings & Resolution Ledger

| Audit Finding / Vulnerability | Evidence Source | Affected Component | V11 Resolution & Status |
| :--- | :--- | :--- | :--- |
| **Cloudflare Fronting via Shared TLS Domains** | `forensics_cf_fronting.md` | `clash_fastly.yaml` (`ruoyemu.global.ssl.fastly.net`) | Completely banned shared domains. Frozen Fastly until authentic Custom TLS cert is provisioned. **RESOLVED** |
| **Cloudflare Anycast IP Pollution (AS13335)** | `forensics_cf_fronting.md` | `clash_wasmer.yaml` (31 nodes on `172.64.149.246`) | Grey-clouded all domains via CF API. Replaced IPs with authentic Wasmer direct hostnames. **RESOLVED** |
| **Deno Adapter Concurrency Race Condition** | `S1_redteam_report_v2.md` | Supabase Deno adapter | Added `isConnecting` state flag and FIFO `pendingQueue: Uint8Array[]` buffer in `denovless_porting_map.md`. **RESOLVED** |
| **Missing VLESS Response Header in Deno** | `S1_redteam_report_v2.md` | Supabase Deno adapter | Explicitly emit `socket.send(new Uint8Array([version, 0x00]))` before entering read loop. **RESOLVED** |
| **Socket Leak on Early Client Disconnect** | `S1_redteam_report_v2.md` | Supabase Deno adapter | Added `isClosed` flag and post-connection cancellation check in `denovless_porting_map.md`. **RESOLVED** |
| **Static Pseudo-Bandwidth Formula** | `S1_redteam_report.md` | `speedtest.py` (`avg_rtt < 60 -> 35Mbps`) | Repudiated static formula. Replaced with genuine chunked HTTP download timing and Trace-Web composite score. **RESOLVED** |
| **Lack of WebSocket 101 Probing** | `S1_redteam_report.md` | `speedtest.py` (TLS-only probing) | Engineered full Layer 4 RFC 6455 HTTP 101 upgrade probe in `trace_web_porting_map.md`. **RESOLVED** |

---

## 6. Execution Status & Next Subagent Dependencies

1. **Stage S0 (Bootstrap)**: Completed and verified in `orchestration/bootstrap_report.md`.
2. **Stage S1 / Study (This Assignment)**:
   - All 5 required porting and context documents authored, validated, and saved to `docs/`:
     * `docs/edgetunnel_porting_map.md` (cmliu/zizifn line-level analysis & 6-column mapping table)
     * `docs/denovless_porting_map.md` (Tintac Deno bridge & hardened Supabase blueprint)
     * `docs/runtime_direct_map.md` (Wasmer Node.js & Northflank Go direct paradigms)
     * `docs/trace_web_porting_map.md` (Trace-Web layered probing & 5-column mapping table)
     * `docs/context_recovery.md` (Historical baseline & architectural recovery)
   - Zero em-dashes verified across all documents.
3. **Immediate Downstream Handoffs**:
   - **TASK-001 (probe)**: Execute live platform capability probes against Netlify, Fastly, and EdgeOne.
   - **TASK-002 (backend)**: Real deployment of Supabase, Wasmer, and Northflank direct backends.
   - **TASK-003 (backend)**: Deployment of fronting/relay services based on TASK-001 probe outcomes.
   - **TASK-005 (speed)**: Multi-carrier China speedtest pipeline across 4000+ candidates.
   - **TASK-006 & TASK-007**: Code, security, network, and red team adversarial verification.
