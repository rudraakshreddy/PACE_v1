import json
import base64
import re
import os
import shutil

log_path = r'C:\Users\Rudraaksh\.gemini\antigravity\brain\21f09c9b-3011-4b92-b822-7a71fe9c1602\.system_generated\logs\transcript_full.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in reversed(f.readlines()):
        try:
            data = json.loads(line)
        except:
            continue
        if data.get('type') == 'USER_INPUT' and 'go to permionics.com' in data.get('content', ''):
            s = json.dumps(data)
            # Find base64 encoded images
            b64_matches = re.findall(r'"base64":\s*"([^"]+)"', s)
            if b64_matches:
                dest = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\backend\assets\permionics_logo.png'
                with open(dest, 'wb') as img_f:
                    img_f.write(base64.b64decode(b64_matches[0]))
                print('Saved base64 logo')
                break
            
            # Find file URIs
            uri_matches = re.findall(r'file:///C:/Users/Rudraaksh/\.gemini/[^"]+', s)
            if uri_matches:
                uri = uri_matches[0]
                path = uri.replace('file:///', '').replace('/', '\\')
                if os.path.exists(path):
                    dest = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\backend\assets\permionics_logo.png'
                    shutil.copy2(path, dest)
                    print('Copied from URI:', path)
                    break
