import re

with open("ui_ux_design/script.js", "r", encoding="utf-8") as f:
    content = f.read()

# Fix calc-membrane -> calc-ro-membrane
content = content.replace(
    "const inputEl = document.getElementById('calc-membrane');",
    "const inputEl = document.getElementById('calc-ro-membrane');"
)

# Add event listener for calc-run-btn
listener_code = """
    const calcRunBtn = document.getElementById('calc-run-btn');
    if (calcRunBtn) {
        calcRunBtn.addEventListener('click', runSystemCalculation);
    }
"""
if "calcRunBtn.addEventListener('click', runSystemCalculation);" not in content:
    content = content.replace("    // Initial calculation (show pre-filled default calculations on first load)", listener_code + "\n    // Initial calculation (show pre-filled default calculations on first load)")

# Add runSystemCalculation function
func_code = """
async function runSystemCalculation() {
    const btn = document.getElementById('calc-run-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Calculating...';
    }

    try {
        const safeInputVal = (id, fallback) => {
            const el = document.getElementById(id);
            if (!el || !el.value) return fallback;
            const val = parseFloat(el.value);
            return isNaN(val) ? fallback : val;
        };

        const safeVal = (id) => {
            const el = document.getElementById(id);
            if (!el) return 0;
            return parseFloat(el.value || el.textContent) || 0;
        };

        const feedData = {
            calcium: safeVal('ca'), magnesium: safeVal('mg'), sodium: safeVal('na'), potassium: safeVal('k'),
            barium: safeVal('ba'), strontium: safeVal('sr'), chloride: safeVal('cl'), sulfate: safeVal('so4'),
            bicarbonate: safeVal('hco3'), nitrate: safeVal('no3'), fluoride: safeVal('f'), silica: safeVal('sio2'),
            boron: safeVal('b'), phosphate: safeVal('po4'), aluminium: safeVal('al'), iron: safeVal('fe'),
            manganese: safeVal('mn'), temperature: safeVal('temp') || 25, ph: safeVal('ph') || 7.5,
            tds: safeVal('calc-tds'), tss: safeVal('tss'), turbidity: safeVal('turbidity')
        };

        const vesselsEl = document.getElementById('calc-vessels-array');
        const vesselsStr = vesselsEl ? (vesselsEl.value || "4,2") : "4,2";
        const vessels = vesselsStr.split(',').map(s => parseInt(s.trim()) || 1);

        const payload = {
            technology_train: document.getElementById('calc-tech-train') ? document.getElementById('calc-tech-train').value : 'RO',
            feed_water: feedData,
            target_flow_m3h: safeInputVal('flow', 50.0),
            target_recovery_pct: document.getElementById('calc-target-recovery') ? safeInputVal('calc-target-recovery', 75.0) : safeInputVal('recovery', 75.0),
            target_tds: document.getElementById('target-tds') ? safeInputVal('target-tds', 50.0) : safeInputVal('rec-target-tds', 50.0),
            source_type: document.getElementById('water-type') ? document.getElementById('water-type').value.toUpperCase() : 'LOW_TDS',
            ro_membrane: document.getElementById('calc-ro-membrane') ? document.getElementById('calc-ro-membrane').value : 'BW30-400',
            stages: safeInputVal('calc-stages', 2),
            vessels_per_stage: vessels,
            elements_per_vessel: safeInputVal('calc-elements-pv', 6)
        };

        const response = await fetch('http://localhost:8000/api/calculate-system', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const result = await response.json();
        const ro = result.ro_results || {};
        const summary = ro.summary || {};
        const elements = ro.elements || [];

        // Update Summary Telemetry
        const updateText = (id, val, dec=1) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val !== undefined && val !== null ? val.toFixed(dec) : '--';
        };

        updateText('calc-sys-rec', summary.recovery_pct, 1);
        updateText('calc-sys-perm-flow', summary.perm_flow_m3h, 1);
        updateText('calc-sys-press', summary.feed_pressure_bar, 1);
        updateText('calc-sys-tds', summary.perm_tds, 1);
        updateText('calc-sys-sec', summary.sec_kwh_m3, 3);

        // Update Hydraulic Profile Table
        const hydTbody = document.getElementById('calc-hyd-tbody');
        if (hydTbody) {
            hydTbody.innerHTML = '';
            elements.forEach(el => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><b>Stage ${el.stage} - El ${el.element}</b></td>
                    <td>${el.feed_flow_m3h.toFixed(1)}</td>
                    <td style="color: var(--success-color); font-weight: bold;">${el.perm_flow_m3h.toFixed(2)}</td>
                    <td>${el.conc_flow_m3h.toFixed(1)}</td>
                    <td>${el.feed_press_bar.toFixed(1)}</td>
                    <td>${el.delta_p_bar.toFixed(2)}</td>
                    <td>${el.flux_lmh.toFixed(1)}</td>
                    <td>${el.recovery_pct.toFixed(1)}%</td>
                    <td style="${el.beta > 1.2 ? 'color: var(--danger-color); font-weight: bold;' : ''}">${el.beta.toFixed(3)}</td>
                `;
                hydTbody.appendChild(tr);
            });
        }

        document.getElementById('calc-results-container').style.display = 'flex';
        const loadingIndicator = document.getElementById('calc-loading-indicator');
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        if (window.switchCalcSubTab) {
            window.switchCalcSubTab('overview');
        }

    } catch (error) {
        console.error('Calculation Error:', error);
        alert('Error: Could not retrieve system calculation. Check Python backend.');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-calculator"></i> Run Detailed Calculation';
        }
    }
}
"""
if "async function runSystemCalculation" not in content:
    content += "\n" + func_code

with open("ui_ux_design/script.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied.")
