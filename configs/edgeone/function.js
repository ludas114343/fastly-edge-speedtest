// EdgeOne L7 Fronting Gateway with Dynamic Supabase Dual-Account Hot Switching and Failover
// Zone: zone-3td4th92xk0e, Function: ef-ddka6pqw
// Fronting Role: Tencent Anycast Edge -> Real Backends (Supabase Dual Account / Wasmer / Netlify / Northflank)

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

const ORIGINS = {
  netlify: "gateway-core-net.netlify.app",
  wasmer: "edgetunnel-us-la.wasmer.app",
  northflank: "nf-node.ruoyemu.asia",
  fastly: "ruoyemu.global.ssl.fastly.net",
  sb1: "theecyezvuzkflwikxwr.supabase.co", // Singapore (ap-southeast-1)
  sb2: "gwgiogtgdyrqlexcdjqm.supabase.co"   // Tokyo (ap-northeast-1)
};

async function forwardTo(request, host, targetPath) {
  try {
    const targetUrl = new URL(request.url);
    targetUrl.hostname = host;
    targetUrl.protocol = "https:";
    targetUrl.port = "443";
    if (targetPath) {
      targetUrl.pathname = targetPath;
    }

    const headers = new Headers(request.headers);
    headers.set("Host", host);

    const forwardReq = new Request(targetUrl.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
      redirect: "manual"
    });

    const resp = await fetch(forwardReq);
    return resp;
  } catch (err) {
    return new Response("Forwarding error to " + host + ": " + err.message, {
      status: 502,
      headers: { "Content-Type": "text/plain; charset=utf-8" }
    });
  }
}

async function handleRequest(request) {
  const url = new URL(request.url);
  
  // Non-websocket root request: return camouflage HTML
  const isWs = (request.headers.get("upgrade") || "").toLowerCase() === "websocket";
  if (!isWs && url.pathname === "/") {
    return new Response(
      '<!DOCTYPE html><html><head><title>EdgeOne Enterprise Gateway</title></head><body><h1>EdgeOne Edge Gateway</h1><p>Status: Operational</p></body></html>',
      { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } }
    );
  }

  // 1. Explicit target selection with appropriate backend path rewriting
  if (url.pathname.startsWith("/sb1") || url.searchParams.get("backend") === "sb1") {
    const r1 = await forwardTo(request, ORIGINS.sb1, "/functions/v1/edgetunnel");
    if (r1.status >= 500) {
      return forwardTo(request, ORIGINS.fastly, "/functions/v1/edgetunnel?forceFunctionRegion=ap-southeast-1");
    }
    return r1;
  }
  if (url.pathname.startsWith("/sb2") || url.searchParams.get("backend") === "sb2") {
    const r2 = await forwardTo(request, ORIGINS.sb2, "/functions/v1/edgetunnel");
    if (r2.status >= 500) {
      return forwardTo(request, ORIGINS.fastly, "/functions/v1/edgetunnel?forceFunctionRegion=ap-northeast-1");
    }
    return r2;
  }
  if (url.pathname.startsWith("/wasmer") || url.searchParams.get("backend") === "wasmer") {
    return forwardTo(request, ORIGINS.wasmer, "/");
  }
  if (url.pathname.startsWith("/nf") || url.searchParams.get("backend") === "northflank") {
    return forwardTo(request, ORIGINS.northflank, "/ws");
  }

  // 2. Supabase Dual Account Dynamic Hot Failover
  if (url.pathname.startsWith("/sb") || url.pathname.includes("/edgetunnel") || url.searchParams.get("backend") === "supabase") {
    const resp1 = await forwardTo(request, ORIGINS.sb1, "/functions/v1/edgetunnel");
    if (resp1.status >= 200 && resp1.status < 500) {
      return resp1;
    }
    const resp2 = await forwardTo(request, ORIGINS.sb2, "/functions/v1/edgetunnel");
    if (resp2.status >= 200 && resp2.status < 500) {
      return resp2;
    }
    return forwardTo(request, ORIGINS.fastly, "/functions/v1/edgetunnel");
  }

  // 3. Default: Netlify
  return forwardTo(request, ORIGINS.netlify, url.pathname);
}
