import re

with open('ui_ux_design/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I will just write a python script to replace the table structure safely.
# Find the start of Ionic Data Combined Table
start_idx = html.find('<!-- Ionic Data Combined Table -->')
end_idx = html.find('</section>', start_idx) + 10

original_table = html[start_idx:end_idx]

# Let's extract the rows
cations = [
    'Sodium (Na⁺)', 'Calcium (Ca²⁺)', 'Magnesium (Mg²⁺)', 'Potassium (K⁺)', 
    'Ammonium (NH₄⁺)', 'Barium (Ba²⁺)', 'Strontium (Sr²⁺)'
]
anions = [
    'Chloride (Cl⁻)', 'Sulphate (SO₄²⁻)', 'Total Alkalinity (as CaCO3)', 
    'Carbonate (CO₃²⁻)', 'Nitrate (NO₃⁻)', 'Fluoride (F⁻)', 'Phosphate (PO₄³⁻)',
    'Silica (SiO₂)*'
]

def extract_row(ion_name, table_html):
    pattern = r'<tr>\s*<td>' + re.escape(ion_name) + r'</td>.*?</tr>'
    match = re.search(pattern, table_html, re.DOTALL)
    if match:
        return match.group(0)
    return ""

cation_rows = "\n".join([extract_row(c, original_table) for c in cations])
anion_rows = "\n".join([extract_row(a, original_table) for a in anions])

new_html = f'''<!-- Ionic Data Combined Table -->
                <section class="card" style="grid-column: span 2;">
                    <div class="card-header">
                        <h2 class="card-title"><i class="fa-solid fa-table-list"></i> Ionic Data</h2>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                        <div class="table-container">
                            <table class="ion-table">
                                <thead>
                                    <tr>
                                        <th style="color: #60a5fa;">Cations (+)</th>
                                        <th>mg/L</th>
                                        <th>meq/L</th>
                                    </tr>
                                </thead>
                                <tbody>
{cation_rows}
                                </tbody>
                            </table>
                        </div>
                        <div class="table-container">
                            <table class="ion-table">
                                <thead>
                                    <tr>
                                        <th style="color: #f87171;">Anions (-) & Neutral</th>
                                        <th>mg/L</th>
                                        <th>meq/L</th>
                                    </tr>
                                </thead>
                                <tbody>
{anion_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="table-container" style="margin-top: 1.5rem;">
                        <table class="ion-table">
                            <tfoot>
                                <tr class="total-row">
                                    <td>Totals</td>
                                    <td><span id="total-mgl">0.00</span> mg/L</td>
                                    <td><span id="total-meq">0.0000</span> meq/L</td>
                                    <td><span id="total-caco3">0.00</span> ppm CaCO₃</td>
                                </tr>
                                <tr id="cbe-row">
                                    <td colspan="4" style="text-align: right;">
                                        <strong>Cation-Anion Balance Error:</strong> 
                                        <span id="cbe-display" style="font-weight: 700; font-size: 1.1rem; margin-left: 1rem;">0.00%</span>
                                        <span id="cbe-status" style="margin-left: 1rem; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem;"></span>
                                    </td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </section>'''

# Replace in the main html
html = html[:start_idx] + new_html + html[end_idx:]

with open('ui_ux_design/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done")
