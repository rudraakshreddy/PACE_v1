import re

with open('script.js', 'r', encoding='utf-8') as f:
    code = f.read()

ions = ['temp', 'ph', 'ca', 'mg', 'na', 'cl', 'so4', 'hco3', 'sr', 'f', 'sio2', 'ba', 'k', 'nh4', 'co3', 'no3', 'al', 'fe', 'mn', 'po4']
for ion in ions:
    # replace document.getElementById('ion').value
    pattern = r"document\.getElementById\('" + ion + r"'\)\.value"
    replacement = r"(document.getElementById('" + ion + r"') || {}).value"
    code = re.sub(pattern, replacement, code)
    
    # replace document.getElementById("ion").value
    pattern2 = r'document\.getElementById\("' + ion + r'"\)\.value'
    replacement2 = r'(document.getElementById("' + ion + r'") || {}).value'
    code = re.sub(pattern2, replacement2, code)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(code)
print("Fix applied")
