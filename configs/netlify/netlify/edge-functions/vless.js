// Netlify Edge Function: Direct VLESS-over-WebSocket Gateway
// Powered by Deno Edge Runtime with native Deno.connect L4 egress

const TARGET_UUID_STR = "99e7f538ec884e96bd9daeb56c04f7fc";
const TARGET_UUID = new Uint8Array(TARGET_UUID_STR.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)));

function constantTimeCompare(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a[i] ^ b[i];
  }
  return diff === 0;
}

function parseVlessHeader(buffer) {
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

export default async (req, context) => {
  const url = new URL(req.url);
  const hasUpgrade = (req.headers.get("upgrade") || "").toLowerCase() === "websocket";
  const hasSecKey = req.headers.has("sec-websocket-key");
  const isWs = hasUpgrade || hasSecKey;

  if (!isWs) {
    if (url.pathname === "/status" || url.pathname === "/probe") {
      const n1_type = typeof Deno !== "undefined" && typeof Deno.connect;
      const n3_type = typeof Deno !== "undefined" && typeof Deno.upgradeWebSocket;
      let tcpEcho = { success: false, bytes_sent: 0, bytes_recv: 0, echo_preview: "", error: null };
      try {
        const conn = await Deno.connect({ hostname: "example.com", port: 80 });
        const reqData = new TextEncoder().encode("GET / HTTP/1.0\r\nHost: example.com\r\n\r\n");
        await conn.write(reqData);
        tcpEcho.bytes_sent = reqData.length;
        const buf = new Uint8Array(128);
        const n = await conn.read(buf);
        conn.close();
        if (n && n > 0) {
          tcpEcho.success = true;
          tcpEcho.bytes_recv = n;
          tcpEcho.echo_preview = new TextDecoder().decode(buf.slice(0, n));
        }
      } catch (e) {
        tcpEcho.error = e.message;
      }
      return new Response(JSON.stringify({
        probe: "Netlify Edge Function N1-N5 Probe",
        timestamp: new Date().toISOString(),
        N1: {
          test: "typeof Deno.connect",
          result: n1_type,
          capable: n1_type === "function"
        },
        N2: {
          test: "Deno.connect dial TCP echo",
          target: "example.com:80",
          capable: tcpEcho.success,
          details: tcpEcho
        },
        N3_runtime: {
          test: "typeof Deno.upgradeWebSocket",
          result: n3_type,
          runtime_present: n3_type === "function"
        }
      }, null, 2), {
        headers: { "Content-Type": "application/json" }
      });
    }
    // Normal HTTP request: pass through to static camouflage site
    return context.next();
  }

  let wsReq = req;
  if (!hasUpgrade) {
    try {
      const h = new Headers(req.headers);
      h.set("upgrade", "websocket");
      h.set("connection", "Upgrade");
      wsReq = new Request(req.url, {
        method: req.method,
        headers: h,
        body: req.body
      });
    } catch (_) {}
  }

  let upgradeResult;
  try {
    upgradeResult = Deno.upgradeWebSocket(wsReq);
  } catch (err) {
    return new Response("WebSocket upgrade failed: " + err.message, { status: 400 });
  }

  const { socket, response } = upgradeResult;

  let tcpConn = null;
  let isConnecting = false;
  let isClosed = false;
  const pendingQueue = [];

  // Parse 0-RTT early data if present
  const secProtocol = req.headers.get("sec-websocket-protocol");
  let earlyDataBuffer = null;
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

  async function processFrame(chunk) {
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
        port: header.port,
      });

      if (isClosed) {
        conn.close();
        return;
      }

      tcpConn = conn;
      isConnecting = false;

      // 1. Send VLESS response header (version, addonsLen=0)
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(new Uint8Array([header.version, 0x00]));
      }

      // 2. Flush initial application payload
      if (header.payload.length > 0) {
        await tcpConn.write(header.payload);
      }

      // 3. Flush frames queued during async Deno.connect
      while (pendingQueue.length > 0) {
        const nextChunk = pendingQueue.shift();
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
    } catch (e) {
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
};

export const config = { path: "/*" };
