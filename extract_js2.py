import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('ui_ux_design/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the rest of runSystemCalculation after the payload
idx = content.find('async function runSystemCalculation')
end_idx = idx + 9000

print("=== REST OF runSystemCalculation ===")
print(content[idx+5500:end_idx])

print("\n=== getFeedWaterData function ===")
idx2 = content.find('function getFeedWaterData')
print(content[idx2:idx2+800])

print("\n=== switchCalcSubTab occurrence ===")
idx3 = content.find('switchCalcSubTab')
print(content[idx3:idx3+600])
