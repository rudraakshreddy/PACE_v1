import urllib.request
import re
import os

url = 'https://permionics.com'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'<img[^>]+src=[\"\']([^\"\']+)[\"\'][^>]*>', html)
        for src in matches:
            if 'logo' in src.lower() or 'permionics' in src.lower():
                print('Found logo URL:', src)
                if not src.startswith('http'):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://permionics.com' + src
                    else:
                        src = 'https://permionics.com/' + src
                dest = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\backend\assets\permionics_logo.png'
                urllib.request.urlretrieve(src, dest)
                print('Downloaded logo to', dest)
                break
except Exception as e:
    print('ERROR:', e)
