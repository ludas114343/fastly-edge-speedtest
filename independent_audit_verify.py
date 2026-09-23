import os
import sys
import json
import yaml
import socket
import ssl
import uuid
import struct
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
CLASH_YAML = os.path.join(REPO_DIR, "clash.yaml")

def build_vless_packet(user_uuid_str, target_host, target_port, payload):
    u = uuid.UUID(user_uuid_str)
    packet = bytearray()
    packet.append(0)  # version 0
    packet.extend(u.bytes)  # 16 bytes UUID
    packet.append(0)  # addons len 0
    packet.append(1)  # command 1 (TCP)
    packet.extend(struct.pack(">H", target_port))  # port 2 bytes
    host_bytes = target_host.encode("utf-8")
    packet.append(2)  # domain type
    packet.append(len(host_bytes))
    packet.extend(host_bytes)
    packet.extend(payload)
    return bytes(packet)

def make_ws_binary_frame(payload):
    length = len(payload)
    frame = bytearray()
    frame.append(0x82)  # FIN + binary opcode
    mask_key = b"\x12\x34\x56\x78"
    if length <= 125:
        frame.append(0x80 | length)
    elif length <= 65535:
        frame.append(0x80 | 126)
        frame.extend(struct.pack(">H", length))
    else:
        frame.append(0x80 | 127)
        frame.extend(struct.pack(">Q", length))
    frame.extend(mask_key)
    masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
    frame.extend(masked)
    return bytes(frame)

def parse_ws_frame(data):
    if len(data) < 2:
        return None, b""
    b1 = data[0]
    b2 = data[1]
    is_masked = (b2 & 0x80) != 0
    payload_len = b2 & 0x7F
    offset = 2
    if payload_len == 126:
        if len(data) < offset + 2:
            return None, data
        payload_len = struct.unpack(">H", data[offset:offset+2])[0]
        offset += 2
    elif payload_len == 127:
        if len(data) < offset + 8:
            return None, data
        payload_len = struct.unpack(">Q", data[offset:offset+8])[0]
        offset += 8
    if is_masked:
        if len(data) < offset + 4 + payload_len:
            return None, data
        mask = data[offset:offset+4]
        offset += 4
        raw = data[offset:offset+payload_len]
        unmasked = bytearray(b ^ mask[i % 4] for i, b in enumerate(raw))
        return bytes(unmasked), data[offset+payload_len:]
    else:
        if len(data) < offset + payload_len:
            return None, data
        return data[offset:offset+payload_len], data[offset+payload_len:]

def get_asn_info(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,regionName,city,isp,org,as,query"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                return {
                    "ip": ip,
                    "as": data.get("as", "UNKNOWN"),
                    "org": data.get("org", "UNKNOWN"),
                    "country": data.get("countryCode", "UNKNOWN")
                }
    except Exception:
        pass
    return {"ip": ip, "as": "UNKNOWN", "org": "UNKNOWN", "country": "UNKNOWN"}

def resolve_dns(domain):
    try:
        infos = socket.getaddrinfo(domain, 443, socket.AF_INET, socket.SOCK_STREAM)
        ips = list(set([item[4][0] for item in infos]))
        if not ips or any(ip.startswith("198.18.") or ip.startswith("127.") for ip in ips):
            try:
                url = f"https://223.5.5.5/resolve?name={domain}&type=A"
                req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    doh_ips = [ans["data"] for ans in data.get("Answer", []) if ans.get("type") == 1]
                    if doh_ips:
                        return doh_ips
            except Exception:
                pass
        return ips
    except Exception as e:
        return []

def execute_vless_transaction(server, port, user_uuid, sni, host_header, path, target_host, target_port, payload_bytes, timeout=12):
    t_start = time.time()
    tls_handshake_ms = 0
    ws_handshake_ms = 0
    total_ms = 0
    
    try:
        t0 = time.time()
        ctx = ssl.create_default_context()
        raw_sock = socket.create_connection((server, port), timeout=timeout)
        tls_sock = ctx.wrap_socket(raw_sock, server_hostname=sni)
        tls_handshake_ms = (time.time() - t0) * 1000

        t1 = time.time()
        ws_req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n\r\n"
        )
        tls_sock.sendall(ws_req.encode())
        ws_resp = tls_sock.recv(4096).decode("utf-8", errors="replace")
        ws_handshake_ms = (time.time() - t1) * 1000

        if "101 Switching Protocols" not in ws_resp:
            status_line = ws_resp.splitlines()[0] if ws_resp else "EMPTY_RESP"
            tls_sock.close()
            return {
                "success": False,
                "tls_ms": tls_handshake_ms,
                "ws_ms": ws_handshake_ms,
                "total_ms": (time.time() - t_start) * 1000,
                "error": f"WS Upgrade Failed: {status_line}",
                "raw_response": b""
            }

        vless_pkt = build_vless_packet(user_uuid, target_host, target_port, payload_bytes)
        ws_frame = make_ws_binary_frame(vless_pkt)
        tls_sock.sendall(ws_frame)

        tls_sock.settimeout(timeout)
        accumulated = bytearray()
        chunks = 0
        while chunks < 6:
            try:
                chunk = tls_sock.recv(4096)
                if not chunk:
                    break
                accumulated.extend(chunk)
                chunks += 1
                if b"HTTP/1.1 204" in accumulated or b"204 No Content" in accumulated or b"HTTP/1.1 200" in accumulated:
                    break
            except socket.timeout:
                break

        tls_sock.close()
        total_ms = (time.time() - t_start) * 1000
        return {
            "success": True,
            "tls_ms": tls_handshake_ms,
            "ws_ms": ws_handshake_ms,
            "total_ms": total_ms,
            "error": None,
            "raw_response": bytes(accumulated)
        }

    except Exception as e:
        total_ms = (time.time() - t_start) * 1000
        return {
            "success": False,
            "tls_ms": tls_handshake_ms,
            "ws_ms": ws_handshake_ms,
            "total_ms": total_ms,
            "error": str(e),
            "raw_response": b""
        }

def probe_node_204(idx, node_cfg):
    name = node_cfg["name"]
    server = node_cfg["server"]
    port = node_cfg.get("port", 443)
    user_uuid = node_cfg["uuid"]
    sni = node_cfg.get("sni", server)
    ws_opts = node_cfg.get("ws-opts", {})
    path = ws_opts.get("path", "/")
    headers = ws_opts.get("headers", {})
    host_header = headers.get("Host", server)

    http_204_req = b"GET /generate_204 HTTP/1.1\r\nHost: www.gstatic.com\r\nConnection: close\r\n\r\n"
    res = execute_vless_transaction(server, port, user_uuid, sni, host_header, path, "www.gstatic.com", 80, http_204_req, timeout=12)

    raw_bytes = res["raw_response"]
    has_204 = (b"204 No Content" in raw_bytes or b"HTTP/1.1 204" in raw_bytes)
    
    # Absorb transient serverless cold starts / handshake resets
    if not has_204:
        time.sleep(0.5)
        retry_res = execute_vless_transaction(server, port, user_uuid, sni, host_header, path, "www.gstatic.com", 80, http_204_req, timeout=12)
        retry_raw = retry_res["raw_response"]
        if b"204 No Content" in retry_raw or b"HTTP/1.1 204" in retry_raw:
            res = retry_res
            raw_bytes = retry_raw
            has_204 = True

    status_code = None
    if has_204:
        status_code = 204
    elif b"HTTP/1.1 " in raw_bytes:
        try:
            part = raw_bytes.split(b"HTTP/1.1 ")[1][:3].decode("ascii", errors="replace")
            status_code = int(part)
        except Exception:
            pass

    return {
        "index": idx,
        "name": name,
        "server": server,
        "port": port,
        "uuid": user_uuid,
        "path": path,
        "success": has_204,
        "status_code": status_code,
        "tls_ms": round(res["tls_ms"], 1),
        "ws_ms": round(res["ws_ms"], 1),
        "total_ms": round(res["total_ms"], 1),
        "error": res["error"] if not has_204 else None,
        "bytes_received": len(raw_bytes)
    }

def probe_egress_ip(server, port, user_uuid, sni, host_header, path):
    http_ip_req = b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nConnection: close\r\n\r\n"
    import re
    for attempt in range(2):
        res = execute_vless_transaction(server, port, user_uuid, sni, host_header, path, "api.ipify.org", 80, http_ip_req, timeout=12)
        raw = res["raw_response"]
        
        text = ""
        payload, rem = parse_ws_frame(raw)
        if payload:
            text += payload.decode("latin1", errors="replace")
        if rem:
            text += rem.decode("latin1", errors="replace")
        text += raw.decode("latin1", errors="replace")

        ip_matches = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        valid_ips = [ip for ip in ip_matches if not ip.startswith("0.") and not ip.startswith("127.") and not ip == "1.1.1.1" and not ip.startswith("198.18.")]
        if valid_ips:
            return valid_ips[-1]
        if attempt == 0:
            time.sleep(0.5)
    return None

def main():
    print("==================================================================")
    print("STAGE B INDEPENDENT BLACK-BOX NETWORK AUDIT AND VERIFICATION")
    print("==================================================================")

    with open(CLASH_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    proxies = data.get("proxies", [])
    print(f"Loaded {len(proxies)} nodes from {CLASH_YAML}")

    print("\n--- [PART 1] Concurrently Probing All 34 Nodes in clash.yaml ---")
    results = [None] * len(proxies)
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(probe_node_204, i, p): i for i, p in enumerate(proxies)}
        for fut in as_completed(futures):
            res = fut.result()
            results[res["index"]] = res
            status_str = "[PASS 204]" if res["success"] else "[FAIL]"
            print(f"{status_str} #{res['index']+1:02d}: {res['name']} | RTT: {res['total_ms']}ms | Code: {res['status_code']} | Err: {res['error']}")

    pass_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - pass_count
    print("\n------------------------------------------------------------------")
    print(f"Part 1 Result: {pass_count}/{len(results)} nodes PASS ({pass_count/len(results)*100:.1f}%)")
    print("------------------------------------------------------------------")

    print("\n--- [PART 2] Server Domain Ingress DNS & ASN 13335 Check ---")
    unique_servers = list(set([p["server"] for p in proxies]))
    server_dns_report = {}
    for s in unique_servers:
        ips = resolve_dns(s)
        asns = [get_asn_info(ip) for ip in ips]
        server_dns_report[s] = {"ips": ips, "asns": asns}
        cf_hit = any("13335" in a.get("as", "") or "Cloudflare" in a.get("org", "") for a in asns)
        print(f"Domain: {s} -> IPs: {ips} | ASN: {[a.get('as') for a in asns]} | CF ASN 13335 HIT: {cf_hit}")

    print("\n--- [PART 3] Wasmer 4 Gateways Dual-UUID Full-Matrix Probe ---")
    wasmer_gateways = [
        ("w-la", "w-la.ruoyemu.asia"),
        ("w-fr", "w-fr.ruoyemu.asia"),
        ("w-east", "w-east.ruoyemu.asia"),
        ("w-us", "w-us.ruoyemu.asia")
    ]
    test_uuids = [
        ("Primary UUID (78174327...)", "78174327-45d8-42ef-a61d-abf885950d9d"),
        ("Compatible UUID (c69d9310...)", "c69d9310-66db-4614-b3b7-0fb01e68b4ec")
    ]
    wasmer_matrix_results = []
    http_204_req = b"GET /generate_204 HTTP/1.1\r\nHost: www.gstatic.com\r\nConnection: close\r\n\r\n"
    for gw_tag, gw_dom in wasmer_gateways:
        for uuid_tag, u_str in test_uuids:
            res = execute_vless_transaction(gw_dom, 443, u_str, gw_dom, gw_dom, "/?ed=2560", "www.gstatic.com", 80, http_204_req, timeout=10)
            raw = res["raw_response"]
            has_204 = (b"204 No Content" in raw or b"HTTP/1.1 204" in raw)
            egress_ip = None
            if has_204:
                egress_ip = probe_egress_ip(gw_dom, 443, u_str, gw_dom, gw_dom, "/?ed=2560")
            
            entry = {
                "gateway": gw_tag,
                "domain": gw_dom,
                "uuid_tag": uuid_tag,
                "uuid": u_str,
                "success": has_204,
                "rtt_ms": round(res["total_ms"], 1),
                "error": res["error"] if not has_204 else None,
                "egress_ip": egress_ip
            }
            wasmer_matrix_results.append(entry)
            status_tag = "[PASS 204]" if has_204 else "[FAIL]"
            print(f"{status_tag} Wasmer {gw_tag} ({gw_dom}) + {uuid_tag} -> RTT: {res['total_ms']:.1f}ms | 204: {has_204} | Egress IP: {egress_ip} | Err: {res['error']}")

    print("\n--- [PART 4] Northflank (nf-node.ruoyemu.asia) End-to-End Probe ---")
    nf_dom = "nf-node.ruoyemu.asia"
    nf_uuid = "c69d9310-66db-4614-b3b7-0fb01e68b4ec"
    nf_res = execute_vless_transaction(nf_dom, 443, nf_uuid, nf_dom, nf_dom, "/ws", "www.gstatic.com", 80, http_204_req, timeout=10)
    nf_has_204 = (b"204 No Content" in nf_res["raw_response"] or b"HTTP/1.1 204" in nf_res["raw_response"])
    nf_egress_ip = probe_egress_ip(nf_dom, 443, nf_uuid, nf_dom, nf_dom, "/ws")
    nf_asn = get_asn_info(nf_egress_ip) if nf_egress_ip else {}
    print(f"Northflank 204 Status: {'PASS' if nf_has_204 else 'FAIL'} | RTT: {nf_res['total_ms']:.1f}ms")
    print(f"Northflank Egress IP: {nf_egress_ip}")
    print(f"Northflank Egress ASN: {nf_asn.get('as')} | Org: {nf_asn.get('org')} | Country: {nf_asn.get('country')}")

    nf_primary_res = execute_vless_transaction(nf_dom, 443, "78174327-45d8-42ef-a61d-abf885950d9d", nf_dom, nf_dom, "/ws", "www.gstatic.com", 80, http_204_req, timeout=8)
    nf_primary_204 = (b"204 No Content" in nf_primary_res["raw_response"] or b"HTTP/1.1 204" in nf_primary_res["raw_response"])
    print(f"Northflank with Primary UUID (78174327...): 204: {nf_primary_204} (Expected: False/Rejected)")

    print("\n--- [PART 5] Supabase Dual Accounts Verification ---")
    sb_accounts = [
        ("sb1", "theecyezvuzkflwikxwr.supabase.co"),
        ("sb2", "gwgiogtgdyrqlexcdjqm.supabase.co")
    ]
    sb_uuid = "21a1f940-25c6-488b-ac29-ae8e89d58b16"
    sb_audit_accounts = {}
    for sb_tag, sb_dom in sb_accounts:
        path_default = "/functions/v1/edgetunnel"
        res = execute_vless_transaction(sb_dom, 443, sb_uuid, sb_dom, sb_dom, path_default, "www.gstatic.com", 80, http_204_req, timeout=12)
        has_204 = (b"204 No Content" in res["raw_response"] or b"HTTP/1.1 204" in res["raw_response"])
        if not has_204:
            time.sleep(0.5)
            res = execute_vless_transaction(sb_dom, 443, sb_uuid, sb_dom, sb_dom, path_default, "www.gstatic.com", 80, http_204_req, timeout=12)
            has_204 = (b"204 No Content" in res["raw_response"] or b"HTTP/1.1 204" in res["raw_response"])

        egress_ip = probe_egress_ip(sb_dom, 443, sb_uuid, sb_dom, sb_dom, path_default)
        asn_info = get_asn_info(egress_ip) if egress_ip else {}
        print(f"Supabase {sb_tag} ({sb_dom}) -> 204: {has_204} | RTT: {res['total_ms']:.1f}ms | Egress: {egress_ip} | ASN: {asn_info.get('as')} | Org: {asn_info.get('org')}")

        path_jp = "/functions/v1/edgetunnel?forceFunctionRegion=ap-northeast-1"
        res_jp = execute_vless_transaction(sb_dom, 443, sb_uuid, sb_dom, sb_dom, path_jp, "www.gstatic.com", 80, http_204_req, timeout=12)
        jp_204 = (b"204 No Content" in res_jp["raw_response"] or b"HTTP/1.1 204" in res_jp["raw_response"])
        if not jp_204:
            time.sleep(0.5)
            res_jp = execute_vless_transaction(sb_dom, 443, sb_uuid, sb_dom, sb_dom, path_jp, "www.gstatic.com", 80, http_204_req, timeout=12)
            jp_204 = (b"204 No Content" in res_jp["raw_response"] or b"HTTP/1.1 204" in res_jp["raw_response"])

        jp_egress = probe_egress_ip(sb_dom, 443, sb_uuid, sb_dom, sb_dom, path_jp)
        jp_asn = get_asn_info(jp_egress) if jp_egress else {}
        print(f"Supabase {sb_tag} (forceFunctionRegion=ap-northeast-1) -> 204: {jp_204} | RTT: {res_jp['total_ms']:.1f}ms | Egress: {jp_egress} | Country: {jp_asn.get('country')} | ASN: {jp_asn.get('as')}")

        sb_audit_accounts[sb_tag] = {
            "domain": sb_dom,
            "default_egress": {
                "ip": egress_ip,
                "as": asn_info.get("as", "UNKNOWN"),
                "org": asn_info.get("org", "UNKNOWN"),
                "country": asn_info.get("country", "UNKNOWN"),
                "rtt_ms": round(res["total_ms"], 1),
                "status_code": 204 if has_204 else None,
                "success": has_204,
                "error": res["error"] if not has_204 else None
            },
            "tokyo_egress": {
                "region": "ap-northeast-1",
                "ip": jp_egress,
                "as": jp_asn.get("as", "UNKNOWN"),
                "org": jp_asn.get("org", "UNKNOWN"),
                "country": jp_asn.get("country", "UNKNOWN"),
                "rtt_ms": round(res_jp["total_ms"], 1),
                "status_code": 204 if jp_204 else None,
                "success": jp_204,
                "error": res_jp["error"] if not jp_204 else None
            }
        }

    sb_nodes = [r for r in results if r and (r.get("uuid") == sb_uuid or "supabase.co" in r.get("server", ""))]
    sb_nodes_passed = sum(1 for r in sb_nodes if r.get("success"))
    sb_nodes_in_clash = len(sb_nodes)
    sb_pass_rate = round(sb_nodes_passed / sb_nodes_in_clash * 100, 1) if sb_nodes_in_clash else 0.0
    sb_all_operational = (sb_nodes_passed == sb_nodes_in_clash) and all(
        a.get("default_egress", {}).get("status_code") == 204 and a.get("tokyo_egress", {}).get("status_code") == 204
        for a in sb_audit_accounts.values()
    )
    sb_regional_verified = all(
        a.get("tokyo_egress", {}).get("country") == "JP" for a in sb_audit_accounts.values()
    )
    sb_dual_standby = len(sb_audit_accounts) >= 2 and all(
        a.get("default_egress", {}).get("status_code") == 204 and a.get("tokyo_egress", {}).get("status_code") == 204
        for a in sb_audit_accounts.values()
    )

    os.makedirs("results", exist_ok=True)
    audit_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "clash_yaml_results": results,
        "clash_summary": {
            "total": len(results),
            "passed": pass_count,
            "failed": fail_count,
            "pass_rate": round(pass_count / len(results) * 100, 2)
        },
        "dns_inspection": server_dns_report,
        "wasmer_matrix": wasmer_matrix_results,
        "northflank": {
            "domain": nf_dom,
            "uuid": nf_uuid,
            "success": nf_has_204,
            "rtt_ms": round(nf_res["total_ms"], 1),
            "egress_ip": nf_egress_ip,
            "asn": nf_asn,
            "primary_uuid_rejected": not nf_primary_204
        },
        "supabase": {
            "uuid": sb_uuid,
            "status": "OPERATIONAL" if sb_all_operational else "DEGRADED",
            "nodes_in_clash_yaml": sb_nodes_in_clash,
            "nodes_passed": sb_nodes_passed,
            "pass_rate": sb_pass_rate,
            "accounts": sb_audit_accounts,
            "regional_routing_verified": sb_regional_verified,
            "dual_account_hot_standby": sb_dual_standby
        }
    }
    with open("results/stage_b_independent_verification.json", "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)
    print("\nSaved full audit data to results/stage_b_independent_verification.json")

if __name__ == "__main__":
    main()
