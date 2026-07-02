import re

content = open('ui_ux_design/index.html', encoding='utf-8').read()
content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

# Find all div opening and closing tags, or other elements
tokens = re.findall(r'<div[^>]*>|</div>|<body[^>]*>|</body>|<html[^>]*>|</html>|id="global-loader"', content_no_comments)

stack = []
found = False
for token in tokens:
    if 'id="global-loader"' in token:
        found = True
        break
    elif token.startswith('<div'):
        # extract class/id if any
        m = re.search(r'class="([^"]+)"', token)
        cls = m.group(1) if m else ""
        m2 = re.search(r'id="([^"]+)"', token)
        id_attr = m2.group(1) if m2 else ""
        stack.append(f"div#{id_attr}.{cls}")
    elif token == '</div>':
        if stack:
            stack.pop()
    elif token.startswith('<body'):
        stack.append("body")
    elif token == '</body>':
        if stack:
            stack.pop()

if found:
    print("Parent chain of #global-loader:")
    print(" -> ".join(stack))
else:
    print("global-loader not found!")
