import re

def update_database():
    with open('backend/membrane_database.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Remove NF membranes
    for nf in ["NF90-400", "NF270-400", "NF200-400"]:
        # We find the block starting with "NF...": { and ending with the next "
        pattern = rf'        "{nf}": {{.*?}},\n'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        
    # 2. Replace UF_MODULES
    with open('scratch/uf_modules_code.py', 'r', encoding='utf-8') as f:
        uf_code = f.read()
        
    pattern = r'    UF_MODULES = \{.*?\n    \}'
    content = re.sub(pattern, uf_code, content, flags=re.DOTALL)
    
    with open('backend/membrane_database.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_database()
