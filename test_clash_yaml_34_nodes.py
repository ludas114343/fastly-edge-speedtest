import os
import sys
import json
import yaml
import socket
import ssl
import uuid
import struct
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    # Address type 2 (domain)
    host_bytes = target_host.encode("utf-8")
    packet.append(2)
    packet.append(len(host_bytes))
    packet.extend(host_bytes)
    # Payload
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

def test_node_once(idx, p):
    name = p["name"]
    server = p["server"]
    port = p.get("port", 443)
    user_uuid = p["uuid"]
    sni = p.get("sni", server)
    ws_opts = p.get("ws-opts", {})
    path = ws_opts.get("path", "/")
    headers = ws_opts.get("headers", {})
    host_header = headers.get("Host", server)

    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        s = socket.create_connection((server, port), timeout=12)
        ss = ctx.wrap_socket(s, server_hostname=sni)

        ws_req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n\r\n"
        )
        ss.sendall(ws_req.encode())
        resp = ss.recv(2048).decode("utf-8", errors="replace")

        if "101 Switching Protocols" not in resp:
            status_line = resp.splitlines()[0] if resp else "EMPTY"
            ss.close()
            return idx, name, False, f"WS Upgrade failed: {status_line}", time.time() - t0

        http_payload = b"GET /generate_204 HTTP/1.1\r\nHost: www.gstatic.com\r\nConnection: close\r\n\r\n"
        vless_pkt = build_vless_packet(user_uuid, "www.gstatic.com", 80, http_payload)
        ws_frame = make_ws_binary_frame(vless_pkt)
        ss.sendall(ws_frame)

        # Receive responses (up to 4 chunks or timeout)
        ss.settimeout(10)
        accumulated_raw = bytearray()
        received_204 = False
        chunks_read = 0

        while chunks_read < 4:
            try:
                chunk = ss.recv(4096)
                if not chunk:
                    break
                accumulated_raw.extend(chunk)
                chunks_read += 1

                # Check if 204 is present in raw stream or parsed frames
                if b"204 No Content" in accumulated_raw or b"HTTP/1.1 204" in accumulated_raw:
                    received_204 = True
                    break

                # Try parsing WebSocket frame
                payload, rem = parse_ws_frame(bytes(accumulated_raw))
                if payload:
                    if b"204 No Content" in payload or b"HTTP/1.1 204" in payload:
                        received_204 = True
                        break
                    if rem and (b"204 No Content" in rem or b"HTTP/1.1 204" in rem):
                        received_204 = True
                        break
            except (socket.timeout, ssl.SSLEOFError, ssl.SSLError, ConnectionResetError, OSError):
                break

        ss.close()
        elapsed = time.time() - t0

        if not received_204 and (b"204 No Content" in accumulated_raw or b"HTTP/1.1 204" in accumulated_raw):
            received_204 = True

        if received_204:
            return idx, name, True, "204 No Content OK", elapsed
        else:
            return idx, name, False, f"No 204 response (received {len(accumulated_raw)} bytes)", elapsed

    except Exception as e:
        return idx, name, False, f"Exception: {str(e)}", time.time() - t0

def test_node(idx, p):
    for attempt in range(2):
        res = test_node_once(idx, p)
        if res[2]:
            return res
        time.sleep(0.5)
    return res

def main():
    with open(CLASH_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    proxies = data.get("proxies", [])
    print(f"Loaded {len(proxies)} proxies from {CLASH_YAML}")
    assert len(proxies) == data.get("metadata", {}).get("node_count", len(proxies))

    total_nodes = len(proxies)
    print(f"\n--- Starting Concurrent End-to-End Real Probe ({total_nodes} Nodes) ---")
    results = [None] * total_nodes

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(test_node, i, p): i for i, p in enumerate(proxies)}
        for future in as_completed(futures):
            idx, name, success, msg, elapsed = future.result()
            status_tag = "[PASS 204]" if success else "[FAIL]"
            print(f"{status_tag} [{idx+1:02d}/{total_nodes:02d}] {name} ({elapsed*1000:.1f}ms): {msg}")
            results[idx] = (name, success, msg, elapsed)

    passed_count = sum(1 for r in results if r[1])
    failed_count = len(results) - passed_count
    pass_rate = (passed_count / len(results)) * 100

    print("\n==================================================")
    print(f"SUMMARY: {passed_count}/{len(results)} PASS ({pass_rate:.1f}%)")
    print("==================================================")

    if failed_count > 0:
        print(f"\nFailed Nodes ({failed_count}):")
        for idx, (name, success, msg, elapsed) in enumerate(results):
            if not success:
                print(f"  #{idx+1:02d}: {name} -> {msg}")
        sys.exit(1)
    else:
        print(f"\nAll {passed_count}/{total_nodes} nodes achieved 100% authentic 204 No Content responses!")
        sys.exit(0)

if __name__ == "__main__":
    main()
