import socket
import ssl
import json
import test_sb_vless
import urllib.request

ctx = ssl.create_default_context()
s = socket.create_connection(('nf-node.ruoyemu.asia', 443), timeout=15)
ss = ctx.wrap_socket(s, server_hostname='nf-node.ruoyemu.asia')

ws_req = (
    'GET /ws HTTP/1.1\r\n'
    'Host: nf-node.ruoyemu.asia\r\n'
    'Upgrade: websocket\r\n'
    'Connection: Upgrade\r\n'
    'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
    'Sec-WebSocket-Version: 13\r\n'
    'User-Agent: Mozilla/5.0\r\n\r\n'
)
ss.sendall(ws_req.encode())
resp = ss.recv(2048).decode('utf-8', errors='replace')
print("Northflank WS Handshake:\n", resp[:200])

if "101 Switching Protocols" in resp:
    # Test generate_204 via VLESS
    http_payload = b"GET /generate_204 HTTP/1.1\r\nHost: www.gstatic.com\r\nConnection: close\r\n\r\n"
    vless_pkt = test_sb_vless.build_vless_packet("c69d9310-66db-4614-b3b7-0fb01e68b4ec", "www.gstatic.com", 80, http_payload)
    ss.sendall(test_sb_vless.make_ws_binary_frame(vless_pkt))
    
    raw1 = ss.recv(4096)
    p1, rem1 = test_sb_vless.parse_ws_frame(raw1)
    print("Frame 1 (VLESS Response Header):", p1)
    
    if len(rem1) > 0:
        p2, _ = test_sb_vless.parse_ws_frame(rem1)
        print("Frame 2 from rem1:\n", p2.decode('utf-8', errors='replace') if p2 else '')
    else:
        raw2 = ss.recv(4096)
        p2, _ = test_sb_vless.parse_ws_frame(raw2)
        print("Frame 2 from raw2:\n", p2.decode('utf-8', errors='replace') if p2 else '')

ss.close()
