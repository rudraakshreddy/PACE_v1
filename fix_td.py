import re

with open('ui_ux_design/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# We need to remove the 4th td from the tbody rows inside the Ionic Data section
start_idx = html.find('<!-- Ionic Data Combined Table -->')
end_idx = html.find('</section>', start_idx) + 10

section_html = html[start_idx:end_idx]

# Pattern to find a tr, and inside it find the 4th td and remove it.
# Actually, since it's just <td><span id="...-caco3">—</span></td>, let's just regex remove it.
new_section_html = re.sub(r'<td><span id="[a-z0-9]+-caco3">.*?</span></td>\s*', '', section_html)

# Put it back
html = html[:start_idx] + new_section_html + html[end_idx:]

with open('ui_ux_design/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done")
