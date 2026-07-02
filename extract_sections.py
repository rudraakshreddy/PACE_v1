import sys

with open('ui_ux_design/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the aging tab section
idx = content.find('id="aging-tab"')
end_idx = content.find('id="report-tab"')
section = content[idx:min(idx+8000, end_idx)]

with open('html_aging_tab.txt', 'w', encoding='utf-8') as f:
    f.write(section)

print("Written", len(section), "chars")

# Also look for the calc tab
idx2 = content.find('id="calc-tab"')
end_idx2 = content.find('id="aging-tab"')
section2 = content[idx2:min(idx2+5000, end_idx2)]
with open('html_calc_tab.txt', 'w', encoding='utf-8') as f:
    f.write(section2)
print("Calc tab:", len(section2), "chars")
