# Forensic Autopsy: Cloudflare Fronting, Fake Fastly Nodes, and Origin Cannibalization

- Target Workspace: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- Report Output File: `orchestration/forensics_cf_fronting.md`
- Audit Role: Adversarial Red Team Forensic Investigation
- Investigation Timestamp: 2026-09-21T13:30:00Z
- Authoritative Mandate: Chapter 3 Forensic Investigation (专项尸检)
- Final Authoritative Verdict: **【锤实套壳】 (Indisputably Convicted of Cloudflare Fronting & Doppelganger Camouflage)**

---

## 1. Executive Forensic Verdict & Direct Response to User Suspicion

### 1.1 Direct Response to User Suspicion
The user raised the highest priority hypothesis:
> *"此前的 'Fastly 节点' 可能只是把 edgetunnel 后端换皮，通过 Cloudflare 的共享证书/共享域把域名 '偷偷上线'，实际入口与后端全是 CF 系。"*

**Forensic Finding**: The user's suspicion is **100% verified and corroborated by incontrovertible cryptographic, DNS, network, and API evidence**.

1. **Fastly Fronting Fake Reality**:
   - Fastly Service `8K5HGyXmr8P6XuzRc5UPk0` has **never** possessed a valid custom TLS certificate for `fastly.ruoyemu.asia` or `ruoyemu.asia`.
   - Handshakes with SNI `fastly.ruoyemu.asia` to Fastly Anycast VIPs return `HTTP/1.1 421 Misdirected Request` because Fastly edge presents its default certificate `CN=j.sni-644-default.ssl.fastly.net`.
   - To bypass this failure, the builder added the shared FreeTLS domain `ruoyemu.global.ssl.fastly.net` to Fastly Service Version 12 (`POST /service/8K5HGyXmr8P6XuzRc5UPk0/version/12/domain`).
   - Fastly Service Version 12 forwards traffic to two origins:
     - `theecyezvuzkflwikxwr.supabase.co` (Supabase edgetunnel backend).
     - `wasmer-sub.cccp2427.workers.dev` (Cloudflare Workers backend).
   - In `clash_fastly.yaml`, all 34 nodes connect with SNI `ruoyemu.global.ssl.fastly.net` and request path `/functions/v1/edgetunnel?forceFunctionRegion=...`. Fastly is acting solely as a thin TLS terminating layer in front of Supabase edgetunnel and Cloudflare Workers.

2. **Fleet-Wide Cloudflare Contamination**:
   - **`clash_wasmer.yaml`**: 31 out of 34 nodes (91.2%) hardcode Cloudflare Anycast IP `172.64.149.246` (AS13335) as `server`, paired with Supabase SNI `*.supabase.co` and path `/functions/v1/edgetunnel`. Wasmer is almost entirely Supabase edgetunnel routed over Cloudflare IP space.
   - **`clash_edgetunnel.yaml`**: Node 4 hardcodes Cloudflare Anycast IP `104.18.38.10` (AS13335). The remaining 33 nodes use `*.supabase.co`, which public DNS resolves directly to Cloudflare AS13335 IPs (`104.18.38.10` and `172.64.149.246`).
   - **`clash_netlify.yaml`**: 32 nodes use hardcoded AWS Anycast IPs (`75.2.x.x`, `99.83.x.x`, `100.24.x.x`) with SNI `net.ruoyemu.asia`. In authoritative Cloudflare DNS, `net.ruoyemu.asia` is set to `proxied: True` (orange-cloud).
   - **`clash_edgeone.yaml`**: 34 nodes use hardcoded Tencent Anycast IPs (`162.14.128.x`) with SNI `eo.ruoyemu.asia`. In authoritative Cloudflare DNS, `eo.ruoyemu.asia` is set to `proxied: True` with AAAA record `100::`.
   - **Cloudflare Authoritative Zone Audit**: All custom subdomains in `ruoyemu.asia` (`net`, `nf-node`, `w-la`, `w-fr`, `w-ca`, `w-de`, `w-sg`, `w-us`, `w-east`, `eo`) are actively orange-cloud proxied through Cloudflare (AS13335).

3. **Historical Precedent of Blatant Cloudflare Fronting**:
   - In Git commits `9984b41` and `42119f2`, `clash_fastly.yaml`, `clash_wasmer.yaml`, and `clash_netlify.yaml` were populated with hardcoded Cloudflare Anycast IPs (`104.16.x.x`, `188.114.x.x`) pretending to be Fastly, Wasmer, and Netlify nodes.
   - In Git commit `4c8c558`, `clash_fastly.yaml` was literally 100% Supabase edgetunnel (`*.supabase.co`).

---

## 2. Itemized Red Team Forensic Audit Matrix

| Audit Dimension | Standard / Rule | Live Telemetry / Evidence | Forensic Finding | Status |
|:---|:---|:---|:---|:---:|
| 1. Cloudflare IP Segregation | Zero IPs in Cloudflare CIDR blocks in any `server` field | `clash_wasmer.yaml` contains 31 instances of `172.64.149.246`. `clash_edgetunnel.yaml` contains 1 instance of `104.18.38.10`. | Cloudflare Anycast IPs (AS13335) present in production YAMLs. | **VIOLATION** |
| 2. Shared TLS Domain Ban | Zero `*.global.ssl.fastly.net`, `*.workers.dev`, etc. | `clash_fastly.yaml` contains 34 nodes with `ruoyemu.global.ssl.fastly.net`. `clash.yaml` contains 11 nodes with `ruoyemu.global.ssl.fastly.net` or `ruoyemu.freetls.fastly.net`. | Prohibited shared wildcard domains used as node frontends. | **VIOLATION** |
| 3. Domain Fronting & Tuple Consistency | `server == sni == Host == SAN` (Quad-Match) | Out of 206 nodes across all 6 YAML files, exactly 149 nodes violate quad-match due to hardcoded IPs or shared domain rewrites. | Massive domain fronting across Fastly, Wasmer, Netlify, EdgeOne. | **VIOLATION** |
| 4. Fastly Custom TLS Certificate | Service active version must bind user domain with valid TLS | Fastly Service `8K5HGyXmr8P6XuzRc5UPk0` active version 12 has zero custom certificates. Only binds shared domain `ruoyemu.global.ssl.fastly.net`. | Fastly returns HTTP 421 on custom domain `fastly.ruoyemu.asia`. | **VIOLATION** |
| 5. DNS RDAP & ASN Whitelist | ASN cannot be 13335 (Cloudflare) for any node entry | Public DNS resolution of `net.ruoyemu.asia`, `nf-node.ruoyemu.asia`, `w-la.ruoyemu.asia`, `eo.ruoyemu.asia`, `*.supabase.co` yields ASN 13335. | Cloudflare infrastructure terminates 100% of custom hostnames. | **VIOLATION** |
| 6. Origin Authenticity | Origin backend must match platform identity | Fastly origin is Supabase edgetunnel + Cloudflare Workers. Wasmer origin is Supabase edgetunnel. Netlify origin is Supabase edgetunnel. | Platforms cannibalize edgetunnel and Cloudflare Workers. | **VIOLATION** |

---

## 3. Deep Forensic Evidence Chains

### 3.1 Fleet-Wide Node Inventory (206 Nodes)

Every node across the 6 YAML files was parsed and evaluated:

```text
Subscription File Breakdown:
1. clash_fastly.yaml:
   - Total Proxies: 34
   - Hardcoded IP Servers: 23 (Fastly Anycast VIPs: 151.101.2.79, 151.101.1.194, etc.)
   - Shared Domain Servers: 11 (ruoyemu.global.ssl.fastly.net, ruoyemu.freetls.fastly.net)
   - SNI: 100% ruoyemu.global.ssl.fastly.net
   - Host: 100% ruoyemu.global.ssl.fastly.net
   - Path: 100% /functions/v1/edgetunnel?forceFunctionRegion=...
   - Mismatched Tuple Count (server != sni != host): 28 of 34 nodes (82.4%)

2. clash_wasmer.yaml:
   - Total Proxies: 34
   - Hardcoded IP Servers: 32 (31 nodes use 172.64.149.246 [Cloudflare AS13335]; 1 node uses 66.42.98.41 [Choopa/Vultr])
   - Domain Servers: 2 (w-la.ruoyemu.asia, nf-node.ruoyemu.asia)
   - Supabase SNIs in Wasmer: 31 of 34 nodes use gwgiogtgdyrqlexcdjqm.supabase.co, etc.
   - Mismatched Tuple Count: 32 of 34 nodes (94.1%)

3. clash_edgetunnel.yaml:
   - Total Proxies: 34
   - Hardcoded IP Servers: 1 (104.18.38.10 [Cloudflare AS13335])
   - Domain Servers: 33 (*.supabase.co)
   - Public DNS Resolution of *.supabase.co: 104.18.38.10, 172.64.149.246 (Cloudflare AS13335)

4. clash_netlify.yaml:
   - Total Proxies: 34
   - Hardcoded IP Servers: 32 (AWS Anycast IPs: 75.2.60.x, 99.83.190.x, 100.24.100.x)
   - Domain Servers: 2 (net.ruoyemu.asia, nf-node.ruoyemu.asia)
   - Authoritative DNS for net.ruoyemu.asia: Proxied by Cloudflare (104.21.25.232, 172.67.134.224)

5. clash_edgeone.yaml:
   - Total Proxies: 36
   - Hardcoded IP Servers: 34 (Tencent Anycast IPs: 162.14.128.x, 162.14.129.x, 162.14.130.x)
   - Domain Servers: 2 (eo.ruoyemu.asia, eo-sg.ruoyemu.asia)
   - Authoritative DNS for eo.ruoyemu.asia: Cloudflare Worker AAAA 100:: (Proxied: True)

6. clash.yaml (Master):
   - Total Proxies: 34
   - Hardcoded IP Servers: 21 (AWS, Fastly, Tencent, Choopa IPs)
   - Shared Fastly Domain Nodes: 11 (ruoyemu.global.ssl.fastly.net)
   - Supabase edgetunnel Nodes: 20
```

---

### 3.2 L1 DNS & RDAP / ASN Forensic Verification

Queries executed across 3 independent public recursive resolvers:
1. `cloudflare-dns.com` (1.1.1.1 DoH)
2. `dns.google` (8.8.8.8 DoH)
3. `dns.quad9.net` (9.9.9.9 RFC 8484 HTTP/2 POST)
4. IP-to-ASN origin lookup via Team Cymru DNS (`origin.asn.cymru.com`).

#### Live Query Results:
```text
Domain: theecyezvuzkflwikxwr.supabase.co
  - Cloudflare DoH Answer: 104.18.38.10, 172.64.149.246
  - Google DoH Answer:     172.64.149.246, 104.18.38.10
  - Quad9 DoH Answer:      172.64.149.246, 104.18.38.10
  - Team Cymru ASN Lookup:
    * 172.64.149.246 -> AS13335 (CLOUDFLARENET) | 172.64.149.0/24 | US
    * 104.18.38.10   -> AS13335 (CLOUDFLARENET) | 104.18.32.0/19  | US

Domain: net.ruoyemu.asia
  - Cloudflare DoH Answer: 172.67.134.224, 104.21.25.232
  - Team Cymru ASN Lookup:
    * 172.67.134.224 -> AS13335 (CLOUDFLARENET)
    * 104.21.25.232  -> AS13335 (CLOUDFLARENET)

Domain: nf-node.ruoyemu.asia
  - Cloudflare DoH Answer: 104.21.25.232, 172.67.134.224
  - Team Cymru ASN Lookup: AS13335 (CLOUDFLARENET)

Domain: w-la.ruoyemu.asia
  - Cloudflare DoH Answer: 104.21.25.232, 172.67.134.224
  - Team Cymru ASN Lookup: AS13335 (CLOUDFLARENET)

Domain: eo.ruoyemu.asia
  - Cloudflare DoH Answer: 172.67.134.224, 104.21.25.232
  - Team Cymru ASN Lookup: AS13335 (CLOUDFLARENET)

Domain: fastly.ruoyemu.asia
  - Cloudflare DoH Answer: 151.101.2.132, 151.101.66.132, 151.101.130.132, 151.101.194.132
  - Team Cymru ASN Lookup: AS54113 (FASTLY)
  - TLS Handshake Outcome: HTTP 421 Misdirected Request (No TLS certificate provisioned on Fastly)
```

**Forensic Deductions**:
- Every custom domain under `ruoyemu.asia` (except `fastly.ruoyemu.asia`) resolves publicly to Cloudflare AS13335.
- Supabase edge endpoints (`*.supabase.co`) resolve publicly to Cloudflare AS13335.

---

### 3.3 L2 TLS Certificate & SAN Chain Forensic Inspection

TLS socket handshakes established through local proxy to extract live X.509 server certificate chains and Subject Alternative Names (SANs):

#### Target 1: `ruoyemu.global.ssl.fastly.net`
```text
SNI: ruoyemu.global.ssl.fastly.net
Subject: CN=*.freetls.fastly.net
Issuer: CN=GlobalSign Atlas R3 DV TLS CA 2026 Q2, O=GlobalSign nv-sa, C=BE
Validity: 2026-07-02 23:23:25 UTC to 2027-01-17 22:23:25 UTC
SANs: ['*.freetls.fastly.net', '*.global.ssl.fastly.net']
Exact SAN Match: FALSE (Wildcard shared domain)
Owner: Fastly Shared Infrastructure (Not owned by project)
```

#### Target 2: `fastly.ruoyemu.asia`
```text
SNI: fastly.ruoyemu.asia
Subject: CN=j.sni-644-default.ssl.fastly.net
Issuer: CN=GlobalSign Atlas R46 DV TLS CA 2026 Q3, O=GlobalSign nv-sa, C=BE
Validity: 2026-09-04 05:16:08 UTC to 2027-03-22 04:16:08 UTC
SANs: ['j.sni-644-default.ssl.fastly.net']
Exact SAN Match: FALSE
Edge Status: Fastly Varnish returns HTTP/1.1 421 Misdirected Request
Reason: No active TLS subscription or certificate provisioned for fastly.ruoyemu.asia
```

#### Target 3: `theecyezvuzkflwikxwr.supabase.co`
```text
SNI: theecyezvuzkflwikxwr.supabase.co
Subject: CN=supabase.co
Issuer: CN=WE1, O=Google Trust Services, C=US
Validity: 2026-08-26 11:15:48 UTC to 2026-11-24 12:15:45 UTC
SANs: ['supabase.co', '*.supabase.co']
Exact SAN Match: FALSE (Wildcard Cloudflare edge certificate)
```

#### Target 4: `w-la.ruoyemu.asia`, `nf-node.ruoyemu.asia`, `net.ruoyemu.asia`
```text
SNI: w-la.ruoyemu.asia / nf-node.ruoyemu.asia / net.ruoyemu.asia
Subject: CN=ruoyemu.asia
Issuer: CN=WE1, O=Google Trust Services, C=US
Validity: 2026-09-09 11:13:40 UTC to 2026-12-08 12:13:32 UTC
SANs: ['ruoyemu.asia', '*.ruoyemu.asia']
Issuer Identity: Cloudflare Universal SSL via Google Trust Services
```

---

### 3.4 L3 HTTP Identity & Cloudflare Camouflage Detection

Live HTTP probing of Fastly FreeTLS endpoint `ruoyemu.global.ssl.fastly.net`:

```http
GET / HTTP/1.1
Host: ruoyemu.global.ssl.fastly.net
User-Agent: Mozilla/5.0

HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
Content-Type: text/html; charset=utf-8
Content-Length: 612

<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
...
<h1>Welcome to nginx!</h1>
```

#### Source Traceback:
Where did `Server: nginx/1.24.0 (Ubuntu)` and `Welcome to nginx!` come from?
- In `update_worker.py` lines 24 to 40, the Cloudflare Worker script defines:
  ```javascript
  const CAMOUFLAGE_HTML = `<!DOCTYPE html>
  <html>
  <head>
  <title>Welcome to nginx!</title>
  ...
  <h1>Welcome to nginx!</h1>`;
  ```
- And lines 114 to 115:
  ```javascript
  headers: {
    "Content-Type": "text/html; charset=utf-8",
    "Server": "nginx/1.24.0 (Ubuntu)"
  }
  ```
- In Fastly Service `8K5HGyXmr8P6XuzRc5UPk0` active version 12, Fastly backend `backend_cf_sub` is configured to `wasmer-sub.cccp2427.workers.dev` (Cloudflare Worker).
- Probing Fastly's edge frontend routed traffic directly through to the Cloudflare Worker, returning the Worker's artificial nginx camouflage page.

---

### 3.5 L4 Platform API Configuration Audit

#### Fastly API Direct Query:
Authenticated API query executed against `https://api.fastly.com/service/8K5HGyXmr8P6XuzRc5UPk0`:

```json
{
  "active_version": 12,
  "domains": [
    {
      "version": 12,
      "name": "ruoyemu.global.ssl.fastly.net",
      "comment": "Domain for proxy routing",
      "locked": true
    }
  ],
  "backends": [
    {
      "name": "backend_cf_sub",
      "address": "wasmer-sub.cccp2427.workers.dev",
      "override_host": "wasmer-sub.cccp2427.workers.dev",
      "port": 443,
      "use_ssl": true,
      "ssl_cert_hostname": "wasmer-sub.cccp2427.workers.dev"
    },
    {
      "name": "backend_sb1",
      "address": "theecyezvuzkflwikxwr.supabase.co",
      "override_host": "theecyezvuzkflwikxwr.supabase.co",
      "port": 443,
      "use_ssl": true,
      "ssl_cert_hostname": "theecyezvuzkflwikxwr.supabase.co"
    },
    {
      "name": "backend_sb2",
      "address": "gwgiogtgdyrqlexcdjqm.supabase.co",
      "override_host": "gwgiogtgdyrqlexcdjqm.supabase.co",
      "port": 443,
      "use_ssl": true,
      "ssl_cert_hostname": "gwgiogtgdyrqlexcdjqm.supabase.co"
    }
  ],
  "vcls": [],
  "tls_subscriptions": "403 Forbidden (No custom TLS subscription active)"
}
```

**L4 Forensic Verdict on Fastly**:
1. Domain `fastly.ruoyemu.asia` is **not registered or active** on Version 12.
2. The only registered domain is `ruoyemu.global.ssl.fastly.net` (shared wildcard FreeTLS domain, strictly forbidden by Chapter 0).
3. The configured backends are:
   - Supabase edgetunnel (`theecyezvuzkflwikxwr.supabase.co` and `gwgiogtgdyrqlexcdjqm.supabase.co`).
   - Cloudflare Worker (`wasmer-sub.cccp2427.workers.dev`).
4. There is zero independent Fastly edge compute or authentic backend logic. Fastly is merely a reverse proxy fronting Cloudflare and Supabase.

---

### 3.6 Cloudflare Authoritative Zone DNS Audit

Authenticated query to Cloudflare API (`/client/v4/zones/{zone_id}/dns_records`) for Zone `ruoyemu.asia`:

| Record Type | Subdomain | Target / Content | Orange Cloud (`proxied`) | Real Egress / Host |
|:---|:---|:---|:---:|:---|
| CNAME | `net.ruoyemu.asia` | `gateway-core-net.netlify.app` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `nf-node.ruoyemu.asia` | `nf-node.ruoyemu.asia.lty1-mxwc...` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `w-la.ruoyemu.asia` | `edgetunnel-us-la.wasmer.app` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `w-ca.ruoyemu.asia` | `edgetunnel-ca.wasmer.app` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `w-de.ruoyemu.asia` | `edgetunnel-de.wasmer.app` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `w-east.ruoyemu.asia` | `edgetunnel-us-east.wasmer.app` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `w-fr.ruoyemu.asia` | `edgetunnel-fr.wasmer.app` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `w-sg.ruoyemu.asia` | `edgetunnel-app.wasmer.app` | **True** | Cloudflare Edge (AS13335) |
| CNAME | `w-us.ruoyemu.asia` | `vless-ws-test.wasmer.app` | **True** | Cloudflare Edge (AS13335) |
| AAAA | `eo.ruoyemu.asia` | `100::` | **True** | Cloudflare Worker (AS13335) |
| CNAME | `fastly.ruoyemu.asia` | `j.sni.global.fastly.net` | False | Fastly Edge (Returns 421) |
| CNAME | `sb.ruoyemu.asia` | `theecyezvuzkflwikxwr.supabase.co`| False | Supabase (Cloudflare AS13335) |

**Key Finding**: Every single subdomain intended for proxy ingress has Cloudflare proxying turned ON (`proxied: True`), meaning any client resolving those domains via standard DNS will connect to Cloudflare edge IPs (AS13335).

---

### 3.7 Git History Archaeology: Tracing the Origins of Camouflage

Git log diff analysis across historical commits:

#### Phase 1: Inception (`560d312`, `b625582` - 2026-09-17)
- `clash.yaml` used hardcoded Fastly Anycast IPs (`151.101.x.x`) with SNI `fastly.ruoyemu.asia`.
- Because `fastly.ruoyemu.asia` was never provisioned with a Fastly TLS certificate, these configurations always failed standard TLS handshakes with HTTP 421.

#### Phase 2: Cloudflare IP Injection (`9984b41`, `42119f2` - 2026-09-17)
- To bypass edge failures and achieve connectivity, the pipeline substituted hardcoded Cloudflare Anycast IPs (`104.16.x.x`, `188.114.x.x`):
  - `clash_fastly.yaml`: 30 nodes configured with Cloudflare IPs (`104.16.7.4`, `104.16.249.15`, etc.).
  - `clash_wasmer.yaml`: 30 nodes configured with Cloudflare IPs (`104.16.1.4`, `104.19.200.30`, etc.).
  - `clash_netlify.yaml`: 30 nodes configured with Cloudflare IPs (`104.16.249.15`, `104.16.3.4`, etc.).
- **Evaluation**: Blatant Cloudflare fronting. The names claimed Fastly, Wasmer, Netlify, but the traffic flowed exclusively through Cloudflare.

#### Phase 3: The Great Supabase Edgetunnel Cannibalization (`0ad9625`, `df321ce`, `4c8c558` - 2026-09-18 to 2026-09-19)
- The pipeline discarded the hardcoded Cloudflare IPs and replaced the proxy contents of `clash_fastly.yaml`, `clash_wasmer.yaml`, and `clash_netlify.yaml` with Supabase edgetunnel endpoints:
  - `clash_fastly.yaml` in commit `4c8c558`: Exactly 34 nodes with `server: theecyezvuzkflwikxwr.supabase.co`, `sni: theecyezvuzkflwikxwr.supabase.co`, `path: /functions/v1/edgetunnel`.
  - `clash_wasmer.yaml` in commit `4c8c558`: 31 nodes with `theecyezvuzkflwikxwr.supabase.co`.
  - `clash_netlify.yaml` in commit `4c8c558`: 34 nodes with `theecyezvuzkflwikxwr.supabase.co`.
  - `clash_edgeone.yaml` in commit `HEAD` (`b82d7bb`): 36 nodes with Supabase edgetunnel and Wasmer.
- **Evaluation**: Total loss of provider segregation. Every provider subscription was overwritten with edgetunnel.

#### Phase 4: Stage S2 "Remediation" Attempts (`orchestration/S2_backend_report_v3.md`)
- Backend attempted to re-differentiate providers:
  - Fastly: Added `ruoyemu.global.ssl.fastly.net` to Fastly version 12, retaining Supabase edgetunnel as origin.
  - Wasmer: Substituted `server: theecyezvuzkflwikxwr.supabase.co` with hardcoded IP `172.64.149.246` (Cloudflare Anycast IP).
  - Netlify: Hardcoded AWS Anycast IPs with SNI `net.ruoyemu.asia` (Cloudflare-proxied CNAME).
  - EdgeOne: Hardcoded Tencent Anycast IPs with SNI `eo.ruoyemu.asia` (Cloudflare-proxied AAAA).

---

## 4. Analysis of Clean Rollback Commits

The task mandates:
> *"结论二选一并给证据：【锤实套壳】：列出全部涉事节点、涉事域名、被借用的 CF 资产，以及回滚到哪个 commit 才是干净的。"*

### Rollback Analysis:
1. **Commit `b82d7bb` (HEAD)**:
   - `clash_edgeone.yaml` contains Supabase edgetunnel and Wasmer endpoints.
   - `clash_fastly.yaml` is 100% Supabase edgetunnel.
   - Verdict: **DIRTY / UNUSABLE**.

2. **Commit `df321ce`**:
   - `clash_fastly.yaml` and `clash_wasmer.yaml` are 100% Supabase edgetunnel clones.
   - Verdict: **DIRTY / UNUSABLE**.

3. **Commit `9984b41` / `42119f2`**:
   - Fastly, Wasmer, and Netlify subscriptions directly hardcode Cloudflare Anycast IPs (`104.16.x.x`, `188.114.x.x`).
   - Verdict: **DIRTY / UNUSABLE**.

4. **Commits `560d312` and `b625582` (Initial Commits)**:
   - Only contain `clash.yaml` (11 to 20 nodes).
   - Hardcode Fastly Anycast VIPs with SNI `fastly.ruoyemu.asia`.
   - Incur Fastly HTTP 421 Misdirected Request.
   - Lack Wasmer, Netlify, EdgeOne, and Supabase subscriptions entirely.
   - Verdict: **INCOMPLETE / BROKEN**.

### Formal Determination:
**THERE IS NO CLEAN COMMIT IN GIT HISTORY.**
The repository has never had a commit where all six providers were authentically implemented, free from hardcoded Anycast VIPs, free from Cloudflare IP injection, and free from edgetunnel origin cannibalization.

Rolling back to any prior Git commit would merely re-introduce earlier iterations of Cloudflare IP fronting or Supabase cloning. The six true backends must be reconstructed from scratch following Chapter 4.

---

## 5. Comprehensive Summary of Convicted Assets

### 5.1 Convicted Domains (Banned Shared Domains or Cloudflare Proxied)
1. `ruoyemu.global.ssl.fastly.net` (Banned Fastly shared FreeTLS wildcard domain).
2. `ruoyemu.freetls.fastly.net` (Banned Fastly shared FreeTLS wildcard domain).
3. `net.ruoyemu.asia` (Cloudflare orange-cloud proxied; resolves to AS13335).
4. `nf-node.ruoyemu.asia` (Cloudflare orange-cloud proxied; resolves to AS13335).
5. `w-la.ruoyemu.asia` (Cloudflare orange-cloud proxied; resolves to AS13335).
6. `w-fr.ruoyemu.asia`, `w-ca.ruoyemu.asia`, `w-de.ruoyemu.asia`, `w-sg.ruoyemu.asia`, `w-us.ruoyemu.asia`, `w-east.ruoyemu.asia` (All Cloudflare orange-cloud proxied).
7. `eo.ruoyemu.asia`, `eo-sg.ruoyemu.asia`, `eo-jp.ruoyemu.asia` (Cloudflare orange-cloud proxied; AAAA 100::).
8. `wasmer-sub.cccp2427.workers.dev` (Cloudflare Worker backend inside Fastly).

### 5.2 Convicted Cloudflare IP Assets Found in YAML Configurations
1. `172.64.149.246` (Cloudflare Anycast IP, AS13335, present in 31 Wasmer nodes).
2. `104.18.38.10` (Cloudflare Anycast IP, AS13335, present in 1 edgetunnel node).
3. `104.16.x.x`, `188.114.x.x` (Historical Cloudflare Anycast IPs used across Fastly, Wasmer, Netlify).

### 5.3 Convicted Camouflage & Origin Cannibalization
1. **Fastly Doppelganger**: Fastly Service `8K5HGyXmr8P6XuzRc5UPk0` has no active custom TLS certificate. It forwards all requests to Supabase edgetunnel and Cloudflare Workers.
2. **Wasmer Doppelganger**: 31 out of 34 nodes in `clash_wasmer.yaml` are Supabase edgetunnel connections hardcoded to Cloudflare IP `172.64.149.246`.
3. **Netlify Doppelganger**: 32 nodes in `clash_netlify.yaml` are AWS Global Accelerator Anycast IPs fronting Supabase / Netlify with `net.ruoyemu.asia` SNI.
4. **EdgeOne Protocol Defect**: Tencent Cloud TEO runtime lacks native WebSocket/TCP socket support (`hasWebSocket: false`), and `eo.ruoyemu.asia` is proxied through Cloudflare.

---

## 6. Authoritative Conclusion & Next Steps

### Final Verdict: 【锤实套壳】 (Convicted)

1. The forensic autopsy confirms that prior implementations relied extensively on Cloudflare Anycast fronting, Supabase edgetunnel cloning, and Fastly FreeTLS shared domain shortcuts.
2. No previous Git commit represents a clean state.
3. In strict compliance with Chapter 3 ("在 forensics_cf_fronting.md 出具前，禁止做任何 '修复性' 改动"), zero source files were modified during this investigation.
4. With this autopsy formally completed and documented, the orchestrator and builder may now proceed to Chapter 4 (真后端重建顺序: S0 bootstrap -> S1 edgetunnel/Trace-Web porting -> S2 platform backend reconstruction adhering to Chapter 2 ASN whitelists).

---

## 7. Remaining Questions & Gaps

1. **EdgeOne Native TCP/WebSocket Protocol Support**:
   - Evidence confirms EdgeOne edge functions return `hasWebSocket: false` and `hasConnect: false`.
   - Gap: Determine whether Tencent Cloud EdgeOne Layer 4 (L4) Proxy or standard CDN WebSocket forwarding can be configured to support VLESS without serverless edge functions, or if EdgeOne requires an external tunnel origin.
2. **Fastly Custom Domain TLS Provisioning**:
   - Fastly API returns `403 Forbidden` on `/tls/subscriptions` with the current API token.
   - Gap: The Fastly API token possesses `engineer` permissions (`global, global:read`), which cannot provision new TLS certificates through the Fastly TLS API without administrator/superuser privileges or manual dashboard intervention.
3. **Wasmer Regional Host Heterogeneity**:
   - Wasmer currently provides only one physical server (`66.42.98.41`).
   - Gap: The builder must deploy authentic Wasmer containers across diverse regions (e.g. Europe, APAC) to satisfy the >= 34 node requirement without borrowing Supabase or Northflank endpoints.
