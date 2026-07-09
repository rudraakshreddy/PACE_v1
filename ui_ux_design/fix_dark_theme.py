import re
txt = open('styles.css', encoding='utf-8').read()
idx = txt.find('[data-theme=dark]')
if idx != -1:
    txt = txt[:idx]

dark_theme = """
[data-theme="dark"] {
  --color-page-bg: #0f172a;
  --color-surface: #1e293b;
  --color-surface-container: #334155;
  --color-surface-container-low: #1e293b;
  --color-surface-container-high: #475569;
  --color-on-surface: #f8fafc;
  --color-on-surface-variant: #94a3b8;
  --color-outline: #64748b;
  --color-outline-variant: #475569;
  
  --bg-color: #0f172a;
  --card-bg: #1e293b;
  --card-border: #334155;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --input-bg: rgba(15, 23, 42, 0.6);
  --input-border: #475569;
}
"""
open('styles.css', 'w', encoding='utf-8').write(txt + dark_theme)
