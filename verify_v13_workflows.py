import os
import sys
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

expected = [
    "deploy-supabase.yml",
    "deploy-wasmer.yml",
    "deploy-northflank.yml",
    "deploy-cloudflare.yml",
    "deploy-fastly.yml",
    "deploy-netlify.yml",
    "deploy-edgeone.yml",
    "discover-candidates.yml",
    "smoke-test.yml",
    "optimize-three-carriers.yml",
    "publish-subscriptions.yml",
    "external-blackbox-audit.yml",
    "watchdog.yml"
]

repo_dir = os.path.dirname(os.path.abspath(__file__))
wf_dir = os.path.join(repo_dir, ".github", "workflows")
actual = sorted(os.listdir(wf_dir))

print(f"Total workflows in .github/workflows/: {len(actual)}")
assert actual == sorted(expected), f"Mismatch! Expected {sorted(expected)}, got {actual}"
print(f"[PASS] All 13 expected workflow files present.")

for wf in actual:
    p = os.path.join(wf_dir, wf)
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    assert "\u2014" not in text, f"Em-dash detected in {wf}"
    assert "\u2013" not in text, f"En-dash detected in {wf}"
    
    parsed = yaml.safe_load(text)
    assert parsed is not None, f"YAML parsing failed for {wf}"
    assert "name" in parsed, f"Missing name in {wf}"
    assert "jobs" in parsed, f"Missing jobs in {wf}"
    assert "permissions" in parsed, f"Missing permissions in {wf}"
    
    on_trigger = parsed.get("on") or parsed.get(True)
    assert on_trigger is not None, f"Missing on trigger in {wf}"
    
    if isinstance(on_trigger, dict) and "schedule" in on_trigger:
        for s in on_trigger["schedule"]:
            cron = s.get("cron", "")
            minute = cron.split()[0]
            print(f"  {wf:30} cron: {cron:15} (minute: {minute})")
            assert minute != "0" and not minute.startswith("0/"), f"Top of the hour cron in {wf}: {cron}"

print("\n[SUCCESS] ALL 13 WORKFLOWS FULLY VALIDATED!")
