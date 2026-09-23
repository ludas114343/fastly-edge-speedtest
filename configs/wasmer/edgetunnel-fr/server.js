// Hardened Production VLESS over WebSocket Gateway for Wasmer Edge / Node.js
// Resolves data frame fragmentation accumulator and net.connect async state machine hazards.

const http = require('http');
const https = require('https');
const net = require('net');
const crypto = require('crypto');

const PORT = process.env.PORT || 8080;
const PRIMARY_UUID_STR = (process.env.UUID || '78174327-45d8-42ef-a61d-abf885950d9d').toLowerCase().replace(/-/g, '');
const PRIMARY_UUID = Buffer.from(PRIMARY_UUID_STR, 'hex');
const LEGACY_UUID_STR = 'c69d9310-66db-4614-b3b7-0fb01e68b4ec'.toLowerCase().replace(/-/g, '');
const LEGACY_UUID = Buffer.from(LEGACY_UUID_STR, 'hex');
const CAMOUFLAGE_URL = process.env.CAMOUFLAGE || 'https://edt-pages.github.io';

console.log('[Wasmer Gateway] Initializing with primary UUID:', PRIMARY_UUID_STR);

// 1. Camouflage HTTP reverse proxy
function handleHttpRequest(req, res) {
  try {
    const targetUrl = new URL(CAMOUFLAGE_URL);
    const options = {
      hostname: targetUrl.hostname,
      port: targetUrl.port || 443,
      path: req.url,
      method: req.method,
      headers: {
        ...req.headers,
        host: targetUrl.hostname,
      }
    };

    const proxyReq = https.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res, { end: true });
    });

    proxyReq.on('error', () => {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end('<!DOCTYPE html><html><head><title>Edge Gateway</title></head><body><h1>Wasmer Edge Gateway</h1><p>Status: Operational</p></body></html>');
    });

    req.pipe(proxyReq, { end: true });
  } catch (_) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end('<!DOCTYPE html><html><head><title>Edge Gateway</title></head><body><h1>Wasmer Edge Gateway</h1><p>Status: Operational</p></body></html>');
  }
}

// 2. RFC 6455 WebSocket helper functions
function makeWsFrame(payload) {
  const len = payload.length;
  let header;
  if (len <= 125) {
    header = Buffer.from([0x82, len]);
  } else if (len <= 65535) {
    header = Buffer.alloc(4);
    header[0] = 0x82;
    header[1] = 126;
    header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x82;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(len), 2);
  }
  return Buffer.concat([header, payload]);
}

// Stream buffering frame accumulator
class WsParser {
  constructor(onBinaryMessage, onClose) {
    this.buffer = Buffer.alloc(0);
    this.onBinaryMessage = onBinaryMessage;
    this.onClose = onClose;
  }

  feed(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    while (this.buffer.length >= 2) {
      const byte1 = this.buffer[0];
      const byte2 = this.buffer[1];
      const opcode = byte1 & 0x0f;
      const isMasked = (byte2 & 0x80) !== 0;
      let payloadLen = byte2 & 0x7f;
      let offset = 2;

      if (payloadLen === 126) {
        if (this.buffer.length < offset + 2) return;
        payloadLen = this.buffer.readUInt16BE(offset);
        offset += 2;
      } else if (payloadLen === 127) {
        if (this.buffer.length < offset + 8) return;
        payloadLen = Number(this.buffer.readBigUInt64BE(offset));
        offset += 8;
      }

      let mask = null;
      if (isMasked) {
        if (this.buffer.length < offset + 4) return;
        mask = this.buffer.slice(offset, offset + 4);
        offset += 4;
      }

      if (this.buffer.length < offset + payloadLen) return;

      const payload = this.buffer.slice(offset, offset + payloadLen);
      this.buffer = this.buffer.slice(offset + payloadLen);

      if (isMasked && mask) {
        for (let i = 0; i < payload.length; i++) {
          payload[i] ^= mask[i % 4];
        }
      }

      if (opcode === 0x08) {
        if (this.onClose) this.onClose();
        return;
      } else if (opcode === 0x02 || opcode === 0x01) {
        if (this.onBinaryMessage) this.onBinaryMessage(payload);
      }
    }
  }
}

// 3. VLESS over WebSocket upgrade handler with explicit async connection queue
function handleWebSocketUpgrade(req, clientSocket, head) {
  const wsKey = req.headers['sec-websocket-key'];
  if (!wsKey) {
    clientSocket.destroy();
    return;
  }

  const acceptValue = crypto
    .createHash('sha1')
    .update(wsKey + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
    .digest('base64');

  const secProtocol = req.headers['sec-websocket-protocol'];
  let responseHeaders = [
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    `Sec-WebSocket-Accept: ${acceptValue}`
  ];

  if (secProtocol) {
    responseHeaders.push(`Sec-WebSocket-Protocol: ${secProtocol}`);
  }
  responseHeaders.push('\r\n');

  clientSocket.write(responseHeaders.join('\r\n'));

  let remoteSocket = null;
  let isConnecting = false;
  let isConnected = false;
  let isClosed = false;
  const pendingFrames = [];
  let firstPacketBuffer = Buffer.alloc(0);

  // Parse early data if Sec-WebSocket-Protocol exists
  if (secProtocol) {
    try {
      const decodedEarly = Buffer.from(secProtocol, 'base64url');
      if (decodedEarly.length >= 18) {
        firstPacketBuffer = decodedEarly;
      }
    } catch (_) {}
  }

  function cleanup() {
    isClosed = true;
    if (remoteSocket) {
      try { remoteSocket.destroy(); } catch (_) {}
      remoteSocket = null;
    }
    try { clientSocket.destroy(); } catch (_) {}
  }

  const parser = new WsParser((binaryPayload) => {
    if (isClosed) return;

    if (isConnected && remoteSocket && !remoteSocket.destroyed) {
      remoteSocket.write(binaryPayload);
      return;
    }

    if (isConnecting) {
      pendingFrames.push(binaryPayload);
      return;
    }

    // First packet: VLESS header parsing
    firstPacketBuffer = Buffer.concat([firstPacketBuffer, binaryPayload]);
    if (firstPacketBuffer.length < 18) return;

    const version = firstPacketBuffer[0];
    const incomingUuid = firstPacketBuffer.slice(1, 17);

    // Verify UUID constant time (supports primary isolated UUID and backwards-compatible legacy UUID)
    const isPrimary = crypto.timingSafeEqual(incomingUuid, PRIMARY_UUID);
    const isLegacy = crypto.timingSafeEqual(incomingUuid, LEGACY_UUID);
    if (!isPrimary && !isLegacy) {
      cleanup();
      return;
    }

    const addonLen = firstPacketBuffer[17];
    let cursor = 18 + addonLen;
    if (firstPacketBuffer.length < cursor + 4) return;

    const command = firstPacketBuffer[cursor++]; // 1 = TCP
    if (command !== 1) {
      cleanup();
      return;
    }

    const port = firstPacketBuffer.readUInt16BE(cursor);
    cursor += 2;
    const addrType = firstPacketBuffer[cursor++];

    let targetHost = '';
    if (addrType === 1) { // IPv4
      if (firstPacketBuffer.length < cursor + 4) return;
      targetHost = Array.from(firstPacketBuffer.slice(cursor, cursor + 4)).join('.');
      cursor += 4;
    } else if (addrType === 2) { // Domain
      const domainLen = firstPacketBuffer[cursor++];
      if (firstPacketBuffer.length < cursor + domainLen) return;
      targetHost = firstPacketBuffer.slice(cursor, cursor + domainLen).toString('ascii');
      cursor += domainLen;
    } else if (addrType === 3) { // IPv6
      if (firstPacketBuffer.length < cursor + 16) return;
      targetHost = firstPacketBuffer.slice(cursor, cursor + 16).toString('hex').match(/.{1,4}/g).join(':');
      cursor += 16;
    } else {
      cleanup();
      return;
    }

    const rawData = firstPacketBuffer.slice(cursor);
    isConnecting = true;

    // Connect to remote target with net.connect state machine
    try {
      remoteSocket = net.connect({ host: targetHost, port: port }, () => {
        if (isClosed) {
          if (remoteSocket) remoteSocket.destroy();
          return;
        }

        isConnected = true;
        isConnecting = false;

        // 1. Send VLESS response header (version, addons len 0)
        clientSocket.write(makeWsFrame(Buffer.from([version, 0x00])));

        // 2. Flush initial application payload
        if (rawData.length > 0) {
          remoteSocket.write(rawData);
        }

        // 3. Flush frames accumulated while awaiting net.connect
        while (pendingFrames.length > 0) {
          const nextFrame = pendingFrames.shift();
          remoteSocket.write(nextFrame);
        }
      });

      remoteSocket.on('data', (data) => {
        if (!isClosed) {
          clientSocket.write(makeWsFrame(data));
        }
      });

      remoteSocket.on('error', () => cleanup());
      remoteSocket.on('close', () => cleanup());
    } catch (_) {
      cleanup();
    }
  }, () => cleanup());

  clientSocket.on('data', (chunk) => parser.feed(chunk));
  clientSocket.on('close', () => cleanup());
  clientSocket.on('error', () => cleanup());

  if (head && head.length > 0) {
    parser.feed(head);
  }
}

// 4. Create and start HTTP server
const server = http.createServer(handleHttpRequest);
server.on('upgrade', (req, socket, head) => {
  handleWebSocketUpgrade(req, socket, head);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[Wasmer Gateway] Server running on 0.0.0.0:${PORT}`);
});
