import re

html_path = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\ui_ux_design\index.html'
js_path = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\ui_ux_design\script.js'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Remove Download Word Report button
html = re.sub(r'<button class="btn" id="calc-report-btn".*?</button>', '', html, flags=re.DOTALL)

# 2. Extract calc-results-container
calc_match = re.search(r'(<div id="calc-results-container".*?<!-- Ion Rejection Performance -->.*?</table>\s*</div>\s*</section>\s*</div>)', html, re.DOTALL)
if not calc_match:
    print('Could not find calc-results-container')
    exit()

calc_html = calc_match.group(1)
html = html.replace(calc_html, '<div id="calc-success-msg" style="display: none; padding: 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success-color); border-radius: 4px; color: var(--success-color); font-weight: 600; text-align: center;"><i class="fa-solid fa-circle-check"></i> Calculations completed successfully! Please navigate to the Report tab to view the detailed results.</div>')

# 3. Transform calc_html styling for Report Tab
calc_html = calc_html.replace('id="calc-results-container" style="display: none; flex-direction: column; gap: 1rem;"', 'id="calc-results-container" style="display: none; margin-bottom: 2.5rem;"')
calc_html = re.sub(r'<section class="card"([^>]*)>', r'<div\1 style="margin-bottom: 2.5rem;">', calc_html)
calc_html = calc_html.replace('</section>', '</div>')
calc_html = re.sub(r'<div class="card-header"[^>]*>\s*<h2 class="card-title"[^>]*>(.*?)</h2>\s*</div>', r'<h3 style="margin-top: 0; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.4rem; color: #0056b3; font-size: 0.9rem; font-weight: 700;">\1</h3>', calc_html)
calc_html = calc_html.replace('class="card-content"', 'class="report-card-content"')

# 4. Insert calc_html into report area
# Find where Section 2 ends. Let's just insert it before the closing </div> of printable-report-area.
# Let's find printable-report-area block
insert_pos = html.find('<!-- End of printable-report-area')
if insert_pos == -1:
    # Let's insert before the last </div> of report-panel-view
    report_match = re.search(r'(<div class="dashboard" id="report-panel-view".*?</div>\s*</div>\s*</div>)', html, re.DOTALL)
    if report_match:
        report_html = report_match.group(1)
        # Find the last </div>
        last_div_idx = report_html.rfind('</div>')
        new_report_html = report_html[:last_div_idx] + '<!-- Section 3: Detailed Calculations -->\n' + calc_html + '\n' + report_html[last_div_idx:]
        html = html.replace(report_html, new_report_html)
    else:
        print("Could not find report area")
        exit()

# Modify JS to show the success message instead of the calc-results-container
js = js.replace("document.getElementById('calc-results-container').style.display = 'flex';", "document.getElementById('calc-success-msg').style.display = 'block';\n                        document.getElementById('calc-results-container').style.display = 'block';")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Migration successful")
