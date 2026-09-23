# V13 Route Proof Documentation and Methodology Specification

- Latest Run ID: `20260923_112251`
- Generated At: `2026-09-23T11:22:51.452643+00:00`
- Mode: `CHAINED_ESTIMATE`

## 1. Technical Limitation and Proxy Chain Overhead Disclaimer

> **DISCLAIMER**: The network latency, throughput, and reachability metrics collected by this pipeline operate strictly under the `CHAINED_ESTIMATE` paradigm. The test probes traverse an isolated multi-hop route topology incorporating TLS protocol handshakes, WebSocket frame encapsulation, and edge egress relays. This methodology incurs measurable intermediate proxy chain overhead (typically 10ms to 45ms added RTT and TCP window pacing overhead) and is **NOT equivalent to direct domestic end-user terminal measurement** conducted from physical broadband connections inside mainland China.

## 2. Ingress Route Proof (China 3-Network Entrance Echo)

| Carrier | Canonical ASN | Probe Target | Echo ASN | Echo ISP / Org | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| China Telecom (Chinanet Backbone) | AS4134 | `218.2.135.1:53` | `AS4134` | China Telecom | **VERIFIED** |
| China Unicom (China169 Backbone) | AS4837 | `219.158.0.1:53` | `AS4837` | China Unicom | **VERIFIED** |
| China Mobile Communications Group | AS9808 | `211.138.180.2:53` | `AS9808` | China Mobile | **VERIFIED** |

## 3. Verified Edge Egress Endpoints

| Node ID | Name | Provider | Egress IP | Egress ASN | Region / Org | Echo Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `supabase-op-01` | 🇯🇵 日本东京 01 [edgetunnel · AWS ap-northeast-1] | supabase | `13.231.74.41` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-northeast-1) (JP) | HTTP 204 |
| `supabase-op-02` | 🇯🇵 日本东京 02 [edgetunnel · AWS ap-northeast-1] | supabase | `13.231.74.41` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-northeast-1) (JP) | HTTP 204 |
| `supabase-op-03` | 🇯🇵 日本东京 03 [edgetunnel · AWS ap-northeast-1] | supabase | `13.231.74.41` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-northeast-1) (JP) | HTTP 204 |
| `supabase-op-04` | 🇰🇷 韩国首尔 01 [edgetunnel · AWS ap-northeast-2] | supabase | `52.78.109.224` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-northeast-2) (KR) | HTTP 204 |
| `supabase-op-05` | 🇰🇷 韩国首尔 02 [edgetunnel · AWS ap-northeast-2] | supabase | `52.78.109.224` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-northeast-2) (KR) | HTTP 204 |
| `supabase-op-06` | 🇰🇷 韩国首尔 03 [edgetunnel · AWS ap-northeast-2] | supabase | `52.78.109.224` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-northeast-2) (KR) | HTTP 204 |
| `supabase-op-07` | 🇸🇬 新加坡 01 [edgetunnel · AWS ap-southeast-1] | supabase | `13.214.33.239` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-southeast-1) (SG) | HTTP 204 |
| `supabase-op-08` | 🇸🇬 新加坡 02 [edgetunnel · AWS ap-southeast-1] | supabase | `13.214.33.239` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-southeast-1) (SG) | HTTP 204 |
| `supabase-op-09` | 🇸🇬 新加坡 03 [edgetunnel · AWS ap-southeast-1] | supabase | `13.214.33.239` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-southeast-1) (SG) | HTTP 204 |
| `supabase-op-10` | 🇩🇪 德国法兰克福 01 [edgetunnel · AWS eu-central-1] | supabase | `63.182.173.66` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-central-1) (DE) | HTTP 204 |
| `supabase-op-11` | 🇩🇪 德国法兰克福 02 [edgetunnel · AWS eu-central-1] | supabase | `63.182.173.66` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-central-1) (DE) | HTTP 204 |
| `supabase-op-12` | 🇩🇪 德国法兰克福 03 [edgetunnel · AWS eu-central-1] | supabase | `63.182.173.66` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-central-1) (DE) | HTTP 204 |
| `wasmer-op-13` | 🇫🇷 法国巴黎 01 [Wasmer · OVH AS16276] | wasmer | `91.134.68.236` | AS16276 OVH SAS | OVH (FR) | HTTP 204 |
| `wasmer-op-14` | 🇫🇷 法国巴黎 02 [Wasmer · OVH AS16276] | wasmer | `91.134.68.236` | AS16276 OVH SAS | OVH (FR) | HTTP 204 |
| `supabase-op-15` | 🇫🇷 法国巴黎 03 [edgetunnel · AWS eu-west-3] | supabase | `35.180.43.183` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-west-3) (FR) | HTTP 204 |
| `supabase-op-16` | 🇫🇷 法国巴黎 04 [edgetunnel · AWS eu-west-3] | supabase | `35.180.43.183` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-west-3) (FR) | HTTP 204 |
| `supabase-op-17` | 🇬🇧 英国伦敦 01 [edgetunnel · AWS eu-west-2] | supabase | `18.170.78.114` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-west-2) (GB) | HTTP 204 |
| `supabase-op-18` | 🇬🇧 英国伦敦 02 [edgetunnel · AWS eu-west-2] | supabase | `18.170.78.114` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-west-2) (GB) | HTTP 204 |
| `supabase-op-19` | 🇨🇭 瑞士苏黎世 01 [edgetunnel · AWS eu-central-2] | supabase | `16.62.2.232` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-central-2) (CH) | HTTP 204 |
| `supabase-op-20` | 🇨🇭 瑞士苏黎世 02 [edgetunnel · AWS eu-central-2] | supabase | `16.62.2.232` | AS16509 Amazon.com, Inc. | AWS EC2 (eu-central-2) (CH) | HTTP 204 |
| `wasmer-op-21` | 🇺🇸 美国美西 01 [Wasmer · Choopa AS20473] | wasmer | `66.42.98.41` | AS20473 The Constant Company, LLC | Choopa (US) | HTTP 204 |
| `wasmer-op-22` | 🇺🇸 美国美西 02 [Wasmer · Choopa AS20473] | wasmer | `66.42.98.41` | AS20473 The Constant Company, LLC | Choopa (US) | HTTP 204 |
| `wasmer-op-23` | 🇺🇸 美国美西 03 [Wasmer · Choopa AS20473] | wasmer | `66.42.98.41` | AS20473 The Constant Company, LLC | Choopa (US) | HTTP 204 |
| `wasmer-op-24` | 🇺🇸 美西俄勒冈 04 [Wasmer · Hetzner AS212317] | wasmer | `5.78.138.69` | AS212317 Hetzner Online GmbH | Hetzner (US) | HTTP 204 |
| `supabase-op-25` | 🇺🇸 美国美西 05 [edgetunnel · AWS us-west-1] | supabase | `54.177.67.165` | AS16509 Amazon.com, Inc. | AWS EC2 (us-west-1) (US) | HTTP 204 |
| `northflank-op-26` | 🇺🇸 美国美东 01 [Northflank · GCP AS396982] | northflank | `35.232.207.236` | AS396982 Google LLC | Google Cloud (US) | HTTP 204 |
| `wasmer-op-27` | 🇺🇸 美国美东 02 [Wasmer · Hetzner AS213230] | wasmer | `5.161.213.176` | AS213230 Hetzner Online GmbH | Hetzner (US) | HTTP 204 |
| `supabase-op-28` | 🇺🇸 美国美东 03 [edgetunnel · AWS us-east-1] | supabase | `98.92.186.16` | AS14618 Amazon.com, Inc. | AWS EC2 (us-east-1) (US) | HTTP 204 |
| `supabase-op-29` | 🇺🇸 美国美东 04 [edgetunnel · AWS us-east-1] | supabase | `98.92.186.16` | AS14618 Amazon.com, Inc. | AWS EC2 (us-east-1) (US) | HTTP 204 |
| `supabase-op-30` | 🇨🇦 加拿大 01 [edgetunnel · AWS ca-central-1] | supabase | `3.98.116.55` | AS16509 Amazon.com, Inc. | AWS EC2 (ca-central-1) (CA) | HTTP 204 |
| `supabase-op-31` | 🇨🇦 加拿大 02 [edgetunnel · AWS ca-central-1] | supabase | `3.98.116.55` | AS16509 Amazon.com, Inc. | AWS EC2 (ca-central-1) (CA) | HTTP 204 |
| `supabase-op-32` | 🇦🇺 澳大利亚 01 [edgetunnel · AWS ap-southeast-2] | supabase | `3.25.229.4` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-southeast-2) (AU) | HTTP 204 |
| `supabase-op-33` | 🇦🇺 澳大利亚 02 [edgetunnel · AWS ap-southeast-2] | supabase | `3.25.229.4` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-southeast-2) (AU) | HTTP 204 |
| `supabase-op-34` | 🇦🇺 澳大利亚 03 [edgetunnel · AWS ap-southeast-2] | supabase | `3.25.229.4` | AS16509 Amazon.com, Inc. | AWS EC2 (ap-southeast-2) (AU) | HTTP 204 |

## 4. Verification Policy

- Zero em-dash (\u2014) and zero en-dash (\u2013) policy strictly enforced.
- Sandbox isolation guaranteed: host proxy ports (7897, 7890) sanitized and untouched.
