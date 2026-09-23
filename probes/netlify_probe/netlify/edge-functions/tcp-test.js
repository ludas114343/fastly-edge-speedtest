export default async (request, context) => {
  try {
    const conn = await Deno.connect({ hostname: "example.com", port: 80 });
    await conn.write(new TextEncoder().encode("GET / HTTP/1.0\r\nHost: example.com\r\n\r\n"));
    const buf = new Uint8Array(64);
    const n = await conn.read(buf);
    conn.close();
    return new Response("TCP OK: " + new TextDecoder().decode(buf.slice(0, n)));
  } catch (e) {
    return new Response("TCP FAILED: " + e.message);
  }
};
export const config = { path: "/tcp-test" };
