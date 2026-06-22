import re

html_path = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\ui_ux_design\index.html'
js_path = r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\ui_ux_design\script.js'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Find the calc-results-container in the report and remove it
calc_match = re.search(r'(<div id="calc-results-container".*?<!-- Ion Rejection Performance -->.*?</table>\s*</div>\s*</div>\s*</div>)', html, re.DOTALL)
if calc_match:
    calc_html = calc_match.group(1)
    # Remove from Report
    html = html.replace('<!-- Section 3: Detailed Calculations -->\n' + calc_html + '\n', '')
    html = html.replace(calc_html, '')
    
    # 2. Transform calc_html back to Calculation tab styling
    calc_html = calc_html.replace('id="calc-results-container" style="display: none; margin-bottom: 2.5rem;"', 'id="calc-results-container" style="display: none; flex-direction: column; gap: 1rem;"')
    calc_html = re.sub(r'<div([^>]*) style="margin-bottom: 2.5rem;">', r'<section class="card"\1>', calc_html)
    calc_html = re.sub(r'<h3 style="margin-top: 0; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.4rem; color: #0056b3; font-size: 0.9rem; font-weight: 700;">(.*?)</h3>', r'<div class="card-header">\n                            <h2 class="card-title">\1</h2>\n                        </div>', calc_html)
    calc_html = calc_html.replace('class="report-card-content"', 'class="card-content"')
    
    # Replace all ending </div> of sections with </section>
    # Since we replaced <section> with <div>, there are 5 sections to restore.
    # We can just manually fix the closing tags using regex on the main blocks
    sections = calc_html.split('<!-- ')
    for i, sec in enumerate(sections):
        if 'System Summary' in sec or 'Design Warnings' in sec or 'Hydraulic Performance' in sec or 'Ion Rejection Performance' in sec:
            sections[i] = sec.rstrip().removesuffix('</div>') + '\n                    </section>\n'
    
    calc_html = '<!-- '.join(sections)
    # Fix the final closing div that might have been removed
    if not calc_html.strip().endswith('</div>'):
        calc_html += '                </div>'
    
    # 3. Replace the success message back with calc-results-container
    success_msg = r'<div id="calc-success-msg" style="display: none; padding: 1rem; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success-color); border-radius: 4px; color: var(--success-color); font-weight: 600; text-align: center;"><i class="fa-solid fa-circle-check"></i> Calculations completed successfully! Please navigate to the Report tab to view the detailed results.</div>'
    html = html.replace(success_msg, calc_html)

# Now, we need to clone the calc-results-container content dynamically to the report tab via JS!
# So we add an empty container in the Report Tab!
empty_report_container = '<div id="report-calculations-container" style="margin-bottom: 2.5rem;"></div>\n'
insert_pos = html.find('<!-- End of printable-report-area')
if insert_pos == -1:
    report_match = re.search(r'(<div class="dashboard" id="report-panel-view".*?</div>\s*</div>\s*</div>)', html, re.DOTALL)
    if report_match:
        report_html = report_match.group(1)
        last_div_idx = report_html.rfind('</div>')
        new_report_html = report_html[:last_div_idx] + empty_report_container + report_html[last_div_idx:]
        html = html.replace(report_html, new_report_html)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Reverse JS display logic
js = js.replace("document.getElementById('calc-success-msg').style.display = 'block';\n                        document.getElementById('calc-results-container').style.display = 'block';", "results.style.display = 'flex';")

# Add cloning logic
clone_logic = """
                // Show report button
                results.style.display = 'flex';
                
                // Clone the results to the report tab
                const reportContainer = document.getElementById('report-calculations-container');
                if (reportContainer) {
                    reportContainer.innerHTML = '<!-- Section 3: Detailed Calculations --><h3 style="margin-top: 0; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.4rem; color: #0056b3; font-size: 0.9rem; font-weight: 700;"><i class="fa-solid fa-calculator"></i> Detailed Calculations</h3>' + results.innerHTML;
                    // Strip dark styling from cloned cards
                    const clonedCards = reportContainer.querySelectorAll('.card');
                    clonedCards.forEach(card => {
                        card.className = '';
                        card.style.marginBottom = '2.5rem';
                    });
                    const clonedHeaders = reportContainer.querySelectorAll('.card-header');
                    clonedHeaders.forEach(hdr => {
                        hdr.className = '';
                        hdr.style.borderBottom = '1px solid #e0e0e0';
                        hdr.style.marginBottom = '0.5rem';
                        hdr.style.paddingBottom = '0.2rem';
                        const title = hdr.querySelector('.card-title');
                        if (title) {
                            title.style.color = '#0056b3';
                            title.style.fontSize = '0.85rem';
                        }
                    });
                }
"""
js = js.replace("results.style.display = 'flex';", clone_logic)
js = js.replace("document.getElementById('calc-success-msg').style.display = 'block';\n                results.style.display = 'block';", clone_logic)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Reversal successful")
