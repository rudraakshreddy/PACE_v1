with open('ui_ux_design/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('runSystemCalculation')
print(f'First occurrence at: {idx}')

# Find all function defs containing this
for keyword in ['async function runSystemCalculation', 'function runSystemCalculation']:
    pos = content.find(keyword)
    if pos > 0:
        print(f'\n--- {keyword} at {pos} ---')
        print(content[pos:pos+3000])
        break

# Also find generateReportContent
idx2 = content.find('function generateReportContent')
print(f'\n--- generateReportContent at {idx2} ---')
print(content[idx2:idx2+2000])

# Find switchCalcSubTab  
idx3 = content.find('function switchCalcSubTab')
print(f'\n--- switchCalcSubTab at {idx3} ---')
print(content[idx3:idx3+800])
