import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Change grid columns
html = html.replace('grid-template-columns: repeat(6, 1fr); gap: 1rem; padding: 0.5rem 1rem 1rem 1rem;">', 'grid-template-columns: repeat(7, 1fr); gap: 1rem; padding: 0.5rem 1rem 1rem 1rem;">')

# Add the new telemetry card right after Interstage Conditioning
new_card = '''                                         <div class="telemetry-card" style="min-height: 80px; padding: 0.8rem 0.5rem; display: flex; flex-direction: column; justify-content: center;">
                                             <div class="telemetry-label" style="margin-bottom: 0.15rem; color: #6ee7b7;">Interpass Pump Power</div>
                                             <div class="telemetry-val" style="font-size: 1.4rem; color: #10b981;"><span id="calc-2p-p2-pump">-</span> <span style="font-size: 0.75rem; font-weight: normal; color: #10b981;">kW</span></div>
                                         </div>'''

# Find the Interstage conditioning card and append the new one
cond_card = '''<div class="telemetry-card" style="min-height: 80px; padding: 0.8rem 0.5rem; display: flex; flex-direction: column; justify-content: center;">
                                             <div class="telemetry-label" style="margin-bottom: 0.15rem; color: #6ee7b7;">Interstage Conditioning</div>
                                             <div class="telemetry-val" style="font-size: 0.85rem; font-weight: 600; line-height: 1.2; color: #10b981;"><span id="calc-2p-cond-desc">None</span></div>
                                         </div>'''

if cond_card in html:
    html = html.replace(cond_card, cond_card + "\n" + new_card)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('script.js', 'r', encoding='utf-8') as f:
    script = f.read()

script = script.replace(
    "setT('#calc-2p-p2-sec',          p2sum.sec_kwh_m3.toFixed(2));",
    "setT('#calc-2p-p2-sec',          p2sum.sec_kwh_m3.toFixed(2));\n                        setT('#calc-2p-p2-pump',         (p2sum.hp_pump_power_kw || 0).toFixed(1));"
)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(script)
