import re

def update_fallbacks():
    # 1. Update membrane_database.py
    with open('backend/membrane_database.py', 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('"IntegraTec-SFD-2880"', '"PERMA-UF-i0875s40"')
    with open('backend/membrane_database.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    # 2. Update system_engine.py
    with open('backend/system_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('"IntegraTec-SFD-2880"', '"PERMA-UF-i0875s40"')
    with open('backend/system_engine.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_fallbacks()
