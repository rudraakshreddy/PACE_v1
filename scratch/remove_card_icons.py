import re

filepath = 'ui_ux_design/index.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Regular expression to match card-title h2/h3 tags containing an i tag icon as the first child
pattern = re.compile(r'(<h[23]\s+[^>]*class="card-title"[^>]*>)\s*<i\s+[^>]*></i>\s*', re.IGNORECASE)

new_content, count = pattern.subn(r'\1', content)

print(f"Substituted {count} card title icons.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
