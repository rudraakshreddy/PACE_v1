import os
import shutil

for filename in ['index.html', 'script.js']:
    print(f"Fixing {filename}...")
    shutil.copy(filename, filename + '.bak')
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed = []
    changes = 0
    # Try converting each character. If it's a sequence that got mangled via cp1252, it will convert.
    # Actually, it's easier to encode the whole string to cp1252 and decode as utf-8.
    # But since there might be SOME valid utf-8 characters that weren't mangled (if any were added later),
    # it's safer to just do a string replacement of known mangled characters.
    replacements = {
        'Â³': '³',
        'Â°': '°',
        'â‚„': '₄',
        'â‚‚': '₂',
        'â‚ƒ': '₃',
        'â‚…': '₅',
        'â »': '⁻',
        'â‚¹': '₹',
        'â†“': '↓',
        'â€”': '—',
        'â†”': '↔',
        'â€¢': '•',
        'Âµ': 'µ',
        'Ã—': '×',
        'â‰¤': '≤',
        'â‰¥': '≥',
        'âˆ†': '∆'
    }

    for bad, good in replacements.items():
        if bad in content:
            changes += content.count(bad)
            content = content.replace(bad, good)
            
    if changes > 0:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {changes} occurrences in {filename}")
    else:
        print(f"No changes needed for {filename}")
