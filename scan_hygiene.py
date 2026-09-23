import os
import json

BASE_DIR = r"C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest"
with open(os.path.join(BASE_DIR, "uuid_config.json"), "r", encoding="utf-8") as f:
    cfg = json.load(f)
RETIRED_UUID = cfg.get("retired_uuid", "")

exts = [".py", ".yaml", ".json", ".js", ".md", ".sh", ".yml"]
violations = []

for root, dirs, files in os.walk(BASE_DIR):
    if ".git" in root or "__pycache__" in root or "sandbox_geogate" in root:
        continue
    for f in files:
        if any(f.endswith(ext) for ext in exts):
            fpath = os.path.join(root, f)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                rel = os.path.relpath(fpath, BASE_DIR)
                if "\u2014" in content:
                    violations.append(f"{rel}: contains em-dash (\\u2014) count={content.count(chr(0x2014))}")
                if "\u2013" in content:
                    violations.append(f"{rel}: contains en-dash (\\u2013) count={content.count(chr(0x2013))}")
                if RETIRED_UUID and RETIRED_UUID in content:
                    violations.append(f"{rel}: contains retired UUID {RETIRED_UUID}")
                if f.endswith(".yaml") and ("香港" in content or "\U0001f1ed\U0001f1f0" in content):
                    violations.append(f"{rel}: YAML contains HK node!")
            except Exception as e:
                violations.append(f"{f}: read error {e}")

print(f"Total checked files. Violations count: {len(violations)}")
for v in violations:
    print("  VIOLATION:", v)
