import os
import sys
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
NF_YAML = os.path.join(REPO_DIR, "clash_northflank.yaml")

def build_vless_packet(user_uuid_str, target_host, target_port, payload):
    u = uuid.UUID(user_uuid_str)
    packet = bytearray()
    packet.append(0)
    packet.extend(u.bytes)
    packet.append(0)
    packet.append(1)
    packet.extend(struct.pack(">H", target_port))
    host_bytes = target_host.encode("utf-8")
    packet.append(2)
    packet.append(len(host_bytes))
    packet.extend(host_bytes)
    packet.extend(payload)
    return bytes(packet)

def make_ws_binary_frame(payload):
    length = len(payload)
    frame = bytearray([0x82])
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

def probe_node(p, retries=3):
    name = p["name"]
    server = p["server"]
    port = p["port"]
    sni = p["sni"]
    path = p["ws-opts"]["path"]
    host = p["ws-opts"]["headers"]["Host"]
    u = p["uuid"]

    last_err = ""
    for attempt in range(retries):
        t0 = time.time()
        s = None
        try:
            ctx = ssl.create_default_context()
            s = socket.create_connection((server, port), timeout=10)
            ss = ctx.wrap_socket(s, server_hostname=sni)
            req = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "User-Agent: Mozilla/5.0\r\n\r\n"
            )
            ss.sendall(req.encode())
            resp = ss.recv(1024).decode("utf-8", errors="replace")
            if "101" not in resp:
                status_line = resp.splitlines()[0] if resp else "empty response"
                ss.close()
                last_err = f"WS handshake failed: {status_line}"
                time.sleep(0.3)
                continue

            http_payload = b"GET /generate_204 HTTP/1.1\r\nHost: www.gstatic.com\r\nConnection: close\r\n\r\n"
            vless_pkt = build_vless_packet(u, "www.gstatic.com", 80, http_payload)
            ss.sendall(make_ws_binary_frame(vless_pkt))
            raw = ss.recv(4096)
            ss.close()
            elapsed_ms = (time.time() - t0) * 1000

            if b"204 No Content" in raw:
                return name, True, f"204 No Content OK ({elapsed_ms:.1f}ms)"
            else:
                last_err = f"Unexpected payload: {raw[:40]}"
        except Exception as e:
            last_err = str(e)
            if s:
                try:
                    s.close()
                except Exception:
                    pass
        time.sleep(0.5)

    return name, False, f"FAILED: {last_err}"

def main():
    assert os.path.exists(NF_YAML), f"Missing {NF_YAML}"
    with open(NF_YAML, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    proxies = cfg.get("proxies", [])
    print(f"Loaded {len(proxies)} proxies from {NF_YAML}")
    assert len(proxies) == 1, f"Expected exactly 1 authentic Northflank proxy, got {len(proxies)}"

    print("\n--- Starting Controlled End-to-End Real Probe (Authentic Northflank Node) ---")
    results = []
    for p in proxies:
        name, ok, msg = probe_node(p)
        results.append((name, ok, msg))
        status = "PASS 204" if ok else "FAIL"
        print(f"[{status}] [01/01] {name}: {msg}")

    pass_count = sum(1 for _, ok, _ in results if ok)
    print("\n==================================================")
    print(f"SUMMARY: {pass_count}/1 PASS ({pass_count/1*100:.1f}%)")
    print("==================================================")
    if pass_count == 1:
        print("Authentic Northflank node achieved 100% 204 No Content response!")
        sys.exit(0)
    else:
        print(f"FAILED: Northflank node failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
