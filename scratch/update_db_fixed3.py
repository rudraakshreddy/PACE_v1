import re

def update_database():
    with open('backend/membrane_database.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    search_str = '"NF200-400": {'
    start_idx = content.find(search_str)
    if start_idx != -1:
        # Move back to start of line to get indentation
        line_start = start_idx
        while line_start > 0 and content[line_start-1] not in ['\n', '\r']:
            line_start -= 1
            
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
            
        content = content[:line_start] + content[end_idx:]
            
    with open('backend/membrane_database.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_database()
