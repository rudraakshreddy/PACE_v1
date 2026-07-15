import re

def update_database():
    with open('backend/membrane_database.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    for nf in ["NF200-400"]:
        search_str = f'        "{nf}": {{'
        start_idx = content.find(search_str)
        if start_idx != -1:
            braces = 0
            end_idx = start_idx
            # find first brace
            while content[end_idx] != '{':
                end_idx += 1
            braces = 1
            end_idx += 1
            while braces > 0 and end_idx < len(content):
                if content[end_idx] == '{':
                    braces += 1
                elif content[end_idx] == '}':
                    braces -= 1
                end_idx += 1
            # consume trailing whitespace/comma
            while end_idx < len(content) and content[end_idx] in [',', ' ', '\n', '\r']:
                end_idx += 1
            content = content[:start_idx] + content[end_idx:]
            
    with open('backend/membrane_database.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_database()
