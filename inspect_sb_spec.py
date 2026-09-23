import urllib.request
import json

req = urllib.request.Request('https://api.supabase.com/api/v1-json')
with urllib.request.urlopen(req) as resp:
    spec = json.loads(resp.read().decode())
    for path, methods in spec.get('paths', {}).items():
        if 'functions' in path:
            print(path)
            for m, details in methods.items():
                summary = details.get("summary", "")
                print(f"  {m.upper()}: {summary}")
                if 'requestBody' in details:
                    print("    requestBody:", list(details['requestBody'].get('content', {}).keys()))
                    # print schema
                    for ctype, cval in details['requestBody'].get('content', {}).items():
                        schema = cval.get('schema', {})
                        print(f"      {ctype} schema: {json.dumps(schema)[:200]}")
