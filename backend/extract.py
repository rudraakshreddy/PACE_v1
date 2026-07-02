import json
import re
import shutil

log_path = r'C:\Users\Rudraaksh\.gemini\antigravity\brain\21f09c9b-3011-4b92-b822-7a71fe9c1602\.system_generated\logs\transcript_full.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in reversed(f.readlines()):
        try:
            data = json.loads(line)
        except:
            continue
        if data.get('type') == 'USER_INPUT' and 'go to permionics.com' in data.get('content', ''):
            images = re.findall(r'<img[^>]+src=[\"\']([^\"\']+)[\"\']', data['content'])
            for img in images:
                print('Found image:', img)
                if img.startswith('file:///'):
                    path = img.replace('file:///', '').replace('/', '\\')
                    dest = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\backend\assets\permionics_logo.png'
                    shutil.copy2(path, dest)
                    print('COPIED!', dest)
            break
