import re

with open(r'c:\Users\Rudraaksh\OneDrive\Desktop\intern_proj\new_pfd_des\app (1).js', 'r', encoding='utf-8') as f:
    app_js = f.read()

start_str = "// --- SVG Rendering Core ---"
end_str = "return svgOpening + arrowMarkerDefs + fullMarkup + pumpsMarkup + `</svg>`;\n}"
start_idx = app_js.find(start_str)
end_idx = app_js.find(end_str) + len(end_str)

build_svg_code = app_js[start_idx:end_idx]

adapter = f"""window.drawPFDSVG = function(ro_results, p1Arr, nEl) {{
    if (!p1Arr || p1Arr.length === 0) p1Arr = [4,2];
    
    const stages_data = (ro_results && ro_results.stages) ? ro_results.stages : [];
    
    let sys_feed_flow = (stages_data.length > 0) ? stages_data[0].feed_flow : 0;
    if (sys_feed_flow === 0) {{
        const flowInput = document.getElementById('flow');
        if (flowInput) sys_feed_flow = parseFloat(flowInput.value) || 0;
    }}
    
    let overall_recovery = 75;
    const recInput = document.getElementById('recovery');
    if (recInput) overall_recovery = parseFloat(recInput.value) || 75;

    let p2Arr = [];
    const hasPass2 = !!(window.lastCalcResult && window.lastCalcResult.pass2_results);
    
    if (hasPass2) {{
        const elP2Stages = document.getElementById('calc-pass2-stages');
        let np2 = elP2Stages ? parseInt(elP2Stages.value) || 1 : 1;
        for (let i = 1; i <= np2; i++) {{
            const vi = document.getElementById('calc-pass2-vessels-s' + i);
            p2Arr.push(vi ? parseInt(vi.value) || 2 : 2);
        }}
    }}

    const passesArray = [p1Arr];
    if (hasPass2) passesArray.push(p2Arr);

    const state = {{
        passes: passesArray,
        theme: {{
            name: 'classic-pace',
            canvasBg: '#CEDDFF',
            vesselFill: '#FFFFF0',
            vesselStroke: '#000000',
            feed: '#555555',
            permeate: '#3B50D0',
            concentrate: '#C00000',
            pump: '#293990',
            label: '#000000'
        }},
        geo: {{
            vesselW: 110,
            vesselH: 32,
            vGap: 18,
            headerMargin: 26,
            manifoldMargin: 26,
            stageExitPad: 36,
            stageGap: 130,
            passGap: 72,
            passHeaderMargin: 50,
            feedStub: 80,
            outletStub: 50
        }},
        animateFlow: false,
        calc: {{
            feedFlow: sys_feed_flow,
            recovery: overall_recovery,
            showFlows: true
        }}
    }};

    {build_svg_code}

    const svgContent = buildSVG();
    const containers = document.querySelectorAll('#pfd-svg-container');
    containers.forEach(c => c.innerHTML = svgContent);
}};"""

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'window\.drawPFDSVG = function\(ro_results, p1Arr, nEl\)\s*\{.*?(?=\n// --- Make PFD Dynamic Based on User Inputs ---)', re.DOTALL)
new_content = pattern.sub(adapter + '\n', content)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(new_content)
