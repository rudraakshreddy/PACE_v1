import urllib.request
import json

try:
    req = urllib.request.Request('http://localhost:8000/api/membranes')
    req.add_header('Authorization', 'Basic dXNlcjpwYXNzd29yZDEyMw==')
    with urllib.request.urlopen(req) as response:
        html = response.read()
        data = json.loads(html)
        ro = data.get('ro_membranes', [])
        permionics = [m for m in ro if m.get('manufacturer', '').lower() == 'permionics']
        print(f"Found {len(permionics)} Permionics membranes:")
        for p in permionics[:3]:
            print(f"ID: {p['id']}, Material: {p.get('material')}")
except Exception as e:
    print("Error:", e)
