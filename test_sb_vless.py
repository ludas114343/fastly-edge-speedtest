import socket
import ssl
import uuid
import json
import struct

def build_vless_packet(user_uuid_str, target_host, target_port, payload):
    u = uuid.UUID(user_uuid_str)
    packet = bytearray()
    packet.append(0) # version 0
    packet.extend(u.bytes) # 16 bytes UUID
    packet.append(0) # addons len 0
    packet.append(1) # command 1 (TCP)
    packet.extend(struct.pack('>H', target_port)) # port 2 bytes
    # Address type 2 (domain)
    host_bytes = target_host.encode('utf-8')
    packet.append(2)
    packet.append(len(host_bytes))
    packet.extend(host_bytes)
    # Payload
    packet.extend(payload)
    return bytes(packet)

def make_ws_binary_frame(payload):
    length = len(payload)
    frame = bytearray()
    frame.append(0x82) # FIN + binary opcode
    # Client to server MUST be masked (RFC 6455)
    mask_key = b'\x12\x34\x56\x78'
    if length <= 125:
        frame.append(0x80 | length)
    elif length <= 65535:
        frame.append(0x80 | 126)
        frame.extend(struct.pack('>H', length))
    else:
        frame.append(0x80 | 127)
        frame.extend(struct.pack('>Q', length))
    frame.extend(mask_key)
    masked_payload = bytearray(length)
    for i in range(length):
        masked_payload[i] = payload[i] ^ mask_key[i % 4]
    frame.extend(masked_payload)
    return bytes(frame)

def parse_ws_frame(data):
    if len(data) < 2:
        return None, b''
    b1 = data[0]
    b2 = data[1]
    is_masked = (b2 & 0x80) != 0
    payload_len = b2 & 0x7f
    offset = 2
    if payload_len == 126:
        payload_len = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
    elif payload_len == 127:
        payload_len = struct.unpack('>Q', data[offset:offset+8])[0]
        offset += 8
    if is_masked:
        mask = data[offset:offset+4]
        offset += 4
        raw = data[offset:offset+payload_len]
        unmasked = bytearray(len(raw))
        for i in range(len(raw)):
            unmasked[i] = raw[i] ^ mask[i % 4]
        return bytes(unmasked), data[offset+payload_len:]
    else:
        return data[offset:offset+payload_len], data[offset+payload_len:]


if __name__ == "__main__":
    print("Testing Supabase Singapore (theecyezvuzkflwikxwr.supabase.co)...")
    ctx = ssl.create_default_context()
    s = socket.create_connection(('theecyezvuzkflwikxwr.supabase.co', 443), timeout=15)
    ss = ctx.wrap_socket(s, server_hostname='theecyezvuzkflwikxwr.supabase.co')

    ws_req = (
        'GET /functions/v1/edgetunnel HTTP/1.1\r\n'
        'Host: theecyezvuzkflwikxwr.supabase.co\r\n'
        'Upgrade: websocket\r\n'
        'Connection: Upgrade\r\n'
        'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
        'Sec-WebSocket-Version: 13\r\n'
        'User-Agent: Mozilla/5.0\r\n\r\n'
    )
    ss.sendall(ws_req.encode())
    resp = ss.recv(2048).decode('utf-8', errors='replace')
    print("WS Handshake:\n", resp[:150])

    if "101 Switching Protocols" in resp:
        http_payload = b"GET /generate_204 HTTP/1.1\r\nHost: www.gstatic.com\r\nConnection: close\r\n\r\n"
        vless_pkt = build_vless_packet("21a1f940-25c6-488b-ac29-ae8e89d58b16", "www.gstatic.com", 80, http_payload)
        ws_frame = make_ws_binary_frame(vless_pkt)
        ss.sendall(ws_frame)

        raw_in = ss.recv(4096)
        payload, remainder = parse_ws_frame(raw_in)
        print("Frame 1 (VLESS Header):", payload)
        
        # Read response payload
        raw_in2 = ss.recv(4096)
        payload2, _ = parse_ws_frame(raw_in2)
        print("Frame 2 (Remote Target Response):\n", payload2.decode('utf-8', errors='replace') if payload2 else b'')
    ss.close()
