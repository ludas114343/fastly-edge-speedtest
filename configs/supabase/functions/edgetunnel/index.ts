// Hardened Production VLESS over WebSocket Adapter for Supabase Edge Functions
// Resolves Deno.connect async concurrency race condition, sends mandatory VLESS [version, 0x00] header, and prevents dangling socket leaks.

const TARGET_UUID_STR = (Deno.env.get("UUID") || "21a1f940-25c6-488b-ac29-ae8e89d58b16").toLowerCase().replace(/-/g, "");
const TARGET_UUID = new Uint8Array(TARGET_UUID_STR.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16)));
const CAMOUFLAGE_URL = Deno.env.get("CAMOUFLAGE_URL") || "https://edt-pages.github.io";

function constantTimeCompare(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a[i] ^ b[i];
  }
  return diff === 0;
}

interface VlessHeader {
  version: number;
  command: number;
  port: number;
  hostname: string;
  payload: Uint8Array;
}

function parseVlessHeader(buffer: Uint8Array): VlessHeader | null {
  if (buffer.length < 24) return null;

  const version = buffer[0];
  const incomingUuid = buffer.subarray(1, 17);
  if (!constantTimeCompare(incomingUuid, TARGET_UUID)) {
    return null;
  }

  const optLen = buffer[17];
  let cursor = 18 + optLen;
  if (buffer.length < cursor + 4) return null;

  const command = buffer[cursor++];
  if (command !== 1 && command !== 2) return null; // 1 = TCP, 2 = UDP

  const port = (buffer[cursor] << 8) | buffer[cursor + 1];
  cursor += 2;

  const addrType = buffer[cursor++];
  let hostname = "";

  if (addrType === 1) { // IPv4
    if (buffer.length < cursor + 4) return null;
    hostname = Array.from(buffer.subarray(cursor, cursor + 4)).join(".");
    cursor += 4;
  } else if (addrType === 2) { // Domain
    const domainLen = buffer[cursor++];
    if (buffer.length < cursor + domainLen) return null;
    hostname = new TextDecoder().decode(buffer.subarray(cursor, cursor + domainLen));
    cursor += domainLen;
  } else if (addrType === 3) { // IPv6
    if (buffer.length < cursor + 16) return null;
    const parts = [];
    for (let i = 0; i < 16; i += 2) {
      parts.push(((buffer[cursor + i] << 8) | buffer[cursor + i + 1]).toString(16));
    }
    hostname = parts.join(":");
    cursor += 16;
  } else {
    return null;
  }

  const payload = buffer.subarray(cursor);
  return { version, command, port, hostname, payload };
}

Deno.serve(async (req: Request) => {
  const upgrade = req.headers.get("upgrade") || "";
  if (upgrade.toLowerCase() !== "websocket") {
    // Camouflage HTTP Reverse Proxy
    try {
      const url = new URL(req.url);
      const target = new URL(CAMOUFLAGE_URL);
      const forwardReq = new Request(`${target.origin}${url.pathname}${url.search}`, {
        method: req.method,
        headers: req.headers,
        body: req.body
      });
      const resp = await fetch(forwardReq);
      return resp;
    } catch (_) {
      return new Response("<!DOCTYPE html><html><head><title>Welcome to nginx!</title></head><body><h1>Welcome to nginx!</h1></body></html>", {
        status: 200,
        headers: { "Content-Type": "text/html; charset=utf-8" }
      });
    }
  }

  let upgradeResult;
  try {
    upgradeResult = Deno.upgradeWebSocket(req);
  } catch (err: any) {
    return new Response("WebSocket upgrade failed: " + err.message, { status: 400 });
  }

  const { socket, response } = upgradeResult;

  let tcpConn: Deno.TcpConn | null = null;
  let isConnecting = false;
  let isClosed = false;
  const pendingQueue: Uint8Array[] = [];

  // Decode 0-RTT early data if present
  const secProtocol = req.headers.get("sec-websocket-protocol");
  let earlyDataBuffer: Uint8Array | null = null;
  if (secProtocol) {
    try {
      const normalized = secProtocol.replace(/-/g, "+").replace(/_/g, "/");
      const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
      const binStr = atob(padded);
      const bytes = new Uint8Array(binStr.length);
      for (let i = 0; i < binStr.length; i++) {
        bytes[i] = binStr.charCodeAt(i);
      }
      if (bytes.length >= 18) {
        earlyDataBuffer = bytes;
      }
    } catch (_) {}
  }

  socket.onopen = async () => {
    if (earlyDataBuffer) {
      await processFrame(earlyDataBuffer);
    }
  };

  async function processFrame(chunk: Uint8Array) {
    if (isClosed) return;

    if (tcpConn) {
      try {
        await tcpConn.write(chunk);
      } catch (_) {
        cleanup();
      }
      return;
    }

    if (isConnecting) {
      pendingQueue.push(chunk);
      return;
    }

    // First frame: parse VLESS protocol header
    isConnecting = true;
    const header = parseVlessHeader(chunk);
    if (!header) {
      try {
        socket.close(1008, "Invalid VLESS Header");
      } catch (_) {}
      cleanup();
      return;
    }

    try {
      const conn = await Deno.connect({
        hostname: header.hostname,
        port: header.port
      });

      if (isClosed) {
        conn.close();
        return;
      }

      tcpConn = conn;
      isConnecting = false;

      // 1. Send mandatory VLESS response header (version, addonsLen=0)
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(new Uint8Array([header.version, 0x00]));
      }

      // 2. Flush initial application payload
      if (header.payload.length > 0) {
        await tcpConn.write(header.payload);
      }

      // 3. Flush frames queued during async Deno.connect
      while (pendingQueue.length > 0) {
        const nextChunk = pendingQueue.shift()!;
        await tcpConn.write(nextChunk);
      }

      // 4. Start outbound TCP -> client WebSocket streaming loop
      (async () => {
        const readBuf = new Uint8Array(32768);
        try {
          while (tcpConn && !isClosed) {
            const n = await tcpConn.read(readBuf);
            if (n === null) break;
            if (socket.readyState === WebSocket.OPEN) {
              socket.send(readBuf.subarray(0, n));
            }
          }
        } catch (_) {
        } finally {
          cleanup();
        }
      })();
    } catch (e: any) {
      try {
        socket.close(1011, "TCP Dial Failed: " + e.message);
      } catch (_) {}
      cleanup();
    }
  }

  socket.onmessage = async (event) => {
    if (typeof event.data === "string") return;
    const chunk = new Uint8Array(event.data);
    await processFrame(chunk);
  };

  socket.onerror = () => {
    cleanup();
  };

  socket.onclose = () => {
    cleanup();
  };

  function cleanup() {
    isClosed = true;
    if (tcpConn) {
      try {
        tcpConn.close();
      } catch (_) {}
      tcpConn = null;
    }
    if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
      try {
        socket.close();
      } catch (_) {}
    }
  }

  return response;
});
