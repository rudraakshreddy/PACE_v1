import re

def update_database():
    with open('backend/membrane_database.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find start of each NF membrane and remove it properly using brace counting
    for nf in ["NF90-400", "NF270-400", "NF200-400"]:
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
            # consume the trailing comma and newline
            while end_idx < len(content) and content[end_idx] in [',', ' ', '\n', '\r']:
                end_idx += 1
            content = content[:start_idx] + content[end_idx:]
            
    # Replace UF_MODULES
    with open('scratch/uf_modules_code.py', 'r', encoding='utf-8') as f:
        uf_code = f.read()
        
    start_uf = content.find("    UF_MODULES = {")
    end_uf = start_uf
    braces = 0
    while content[end_uf] != '{':
        end_uf += 1
    braces = 1
    end_uf += 1
    while braces > 0 and end_uf < len(content):
        if content[end_uf] == '{':
            braces += 1
        elif content[end_uf] == '}':
            braces -= 1
        end_uf += 1
        
    content = content[:start_uf] + uf_code + content[end_uf:]
    
    with open('backend/membrane_database.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_database()
