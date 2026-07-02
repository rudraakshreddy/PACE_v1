content = open('ui_ux_design/index.html', encoding='utf-8').read()
cnt = content.count('cx="55" cy="85"')
print(f"Occurrences of cx=55 cy=85: {cnt}")
