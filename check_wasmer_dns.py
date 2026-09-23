import urllib.request
import json

domains = [
    "w-la.ruoyemu.asia",
    "w-fr.ruoyemu.asia",
    "w-east.ruoyemu.asia",
    "w-us.ruoyemu.asia"
]

for d in domains:
    for resolver in ["https://1.1.1.1/dns-query?name=", "https://dns.google/resolve?name="]:
        url = f"{resolver}{d}&type=A"
        req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                answers = [a.get("data") for a in data.get("Answer", []) if a.get("type") == 1]
                cnames = [a.get("data") for a in data.get("Answer", []) if a.get("type") == 5]
                print(f"{d} via {resolver.split('/')[2]}: CNAME={cnames} A={answers}")
        except Exception as e:
            print(f"Error {d}:", e)
