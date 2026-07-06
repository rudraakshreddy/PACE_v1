import re

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: concManifoldY to avoid pump label overlapping
content = content.replace(
    "const concManifoldY = firstStageStartY + passHeight + GEO.manifoldMargin;",
    "const concManifoldY = Math.max(firstStageStartY + passHeight + GEO.manifoldMargin, centerY + 80);"
)

# Fix 2: stage flow labels overlapping vertical pipes
# Permeate text
content = content.replace(
    'fullMarkup += <text x="" y="" font-size="8.5" font-weight="600" fill="" font-family="Fira Code, monospace"></text>;',
    'fullMarkup += <text x="" y="" font-size="8.5" font-weight="600" fill="" text-anchor="end" font-family="Fira Code, monospace"></text>;'
)
# Concentrate text
content = content.replace(
    'fullMarkup += <text x="" y="" font-size="8.5" font-weight="600" fill="" font-family="Fira Code, monospace"></text>;',
    'fullMarkup += <text x="" y="" font-size="8.5" font-weight="600" fill="" text-anchor="end" font-family="Fira Code, monospace"></text>;'
)

# Fix 3: Interpass Pump touching the Pass 1 concentrate drop line
content = content.replace(
    "const pumpCx = p1ExitX + 48;",
    "const pumpCx = p1ExitX + 78;"
)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(content)
