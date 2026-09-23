import socket
import ssl

for d in ['w-la.ruoyemu.asia', 'w-fr.ruoyemu.asia', 'w-east.ruoyemu.asia', 'w-us.ruoyemu.asia']:
    try:
        s = socket.create_connection((d, 443), timeout=5)
        ctx = ssl.create_default_context()
        tls = ctx.wrap_socket(s, server_hostname=d)
        cert = tls.getpeercert()
        sans = [item[1] for item in cert.get('subjectAltName', []) if item[0] == 'DNS']
        issuer = dict(x[0] for x in cert.get('issuer', []))
        print(f"{d}: SANs={sans} | Issuer={issuer.get('organizationName') or issuer.get('commonName')}")
        tls.close()
    except Exception as e:
        print(f"{d} error:", e)
