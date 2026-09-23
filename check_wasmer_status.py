import urllib.request
import json
import re

with open(r"C:\Users\ludas\.wasmer\wasmer.toml", "r", encoding="utf-8") as f:
    text = f.read()

m = re.search(r'token = "([^"]+)"', text)
token = m.group(1) if m else ""

q = """
query {
  viewer {
    apps(first: 30) {
      edges {
        node {
          id
          name
          activeVersion {
            id
            version
            createdAt
            yamlConfig
          }
        }
      }
    }
  }
}
"""
req = urllib.request.Request(
    "https://registry.wasmer.io/graphql",
    data=json.dumps({"query": q}).encode(),
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        for e in data.get("data", {}).get("viewer", {}).get("apps", {}).get("edges", []):
            node = e["node"]
            if node["name"] == "edgetunnel-us-east":
                print(f"=== {node['name']} ({node['id']}) ===")
                print(node.get("activeVersion", {}).get("yamlConfig"))
except Exception as e:
    print(f"Error: {e}")


