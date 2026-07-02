import re
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()
matches = re.findall(r'onclick="([^"]+)"', content)
for m in set(matches):
    print(m)
