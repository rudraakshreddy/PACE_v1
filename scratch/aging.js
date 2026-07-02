// Membrane Aging Simulation Logic

async function runAgingSimulation() {
    const btn = document.getElementById('aging-run-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Simulating Aging...';
    btn.disabled = true;

    try {
        // Build payload
        const feedWater = getFeedWaterData(); // Assumes this global function exists (it does, it builds feed object)
        const flow = parseFloat(document.getElementById('flow').value) || 10.0;
        const recovery = parseFloat(document.getElementById('recovery').value) || 75.0;

        const payload = {
            feed_water: feedWater,
            system_config: {
                membrane: document.getElementById('ro-membrane') ? document.getElementById('ro-membrane').value : 'BW30-400',
                stages: parseInt(document.getElementById('stages') ? document.getElementById('stages').value : 1),
                vessels_per_stage: (document.getElementById('vessels-stage-1') ? [parseInt(document.getElementById('vessels-stage-1').value), parseInt(document.getElementById('vessels-stage-2') ? document.getElementById('vessels-stage-2').value : 0)].filter(v => v>0) : [1]),
                elements_per_vessel: parseInt(document.getElementById('elements-per-vessel') ? document.getElementById('elements-per-vessel').value : 6),
                target_recovery_pct: recovery
            },
            aging_config: {
                design_life_months: parseInt(document.getElementById('aging-design-life').value) || 60,
                time_step_months: 1,
                simulation_mode: document.getElementById('aging-sim-mode').value || 'constant_recovery',
                cip_trigger: document.getElementById('aging-cip-mode').value || 'scheduled',
                cip_interval_days: parseInt(document.getElementById('aging-cip-interval').value) || 90,
                cip_type: 'acid_alkaline_sequential',
                antiscalant_dosed: document.getElementById('aging-antiscalant').checked
            },
            feed_history: {
                sdi15: parseFloat(document.getElementById('aging-sdi').value) || 3.0,
                toc_mg_l: parseFloat(document.getElementById('aging-toc').value) || 2.0,
                temperature_c: parseFloat(document.getElementById('aging-temp').value) || 28.0,
                cl2_residual_mg_l: parseFloat(document.getElementById('aging-cl2').value) || 0.0
            },
            target_flow_m3h: flow
        };

        const response = await fetch('/api/simulate-aging', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Simulation failed');
        }

        const result = await response.json();
        renderAgingResults(result);

    } catch (error) {
        console.error(error);
        alert('Aging simulation failed: ' + error.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function renderAgingResults(data) {
    // Reveal Cards
    document.getElementById('aging-eol-card').style.display = 'block';
    document.getElementById('aging-autopsy-card').style.display = 'block';
    document.getElementById('aging-highlights-card').style.display = 'block';
    document.getElementById('aging-chart-card').style.display = 'block';
    document.getElementById('aging-mechanism-card').style.display = 'block';
    document.getElementById('aging-table-card').style.display = 'block';

    const final = data.final_state;
    const eol = data.eol_prediction;
    const series = data.time_series;

    // Highlights
    document.getElementById('aging-hl-npf').textContent = final.npf_m3h.toFixed(1);
    document.getElementById('aging-hl-pfeed').textContent = final.feed_pressure_bar.toFixed(1);
    document.getElementById('aging-hl-cips').textContent = final.cumulative_cips;
    document.getElementById('aging-eol-month').textContent = eol.eol_reached ? eol.eol_month : '> ' + data.metadata.design_life_months;
    document.getElementById('aging-hl-eol').textContent = document.getElementById('aging-eol-month').textContent;
    document.getElementById('aging-dominant-mech').textContent = eol.dominant_mechanism.replace('_', ' ').toUpperCase();

    // Table
    const tbody = document.getElementById('aging-monthly-tbody');
    tbody.innerHTML = '';
    series.forEach(pt => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${pt.month}</td>
            <td style="color: var(--accent); font-weight: 600;">${pt.feed_pressure_bar.toFixed(2)}</td>
            <td>${pt.npf_m3h.toFixed(2)}</td>
            <td>${pt.nsr_pct.toFixed(2)}</td>
            <td>${pt.dp_ratio.toFixed(2)}</td>
            <td>${pt.avg_flux_lmh.toFixed(1)}</td>
            <td>${pt.recovery_pct.toFixed(1)}</td>
            <td>${pt.cip_event ? '✅' : ''}</td>
        `;
        tbody.appendChild(tr);
    });

    // Autopsy Table
    const autoTbody = document.getElementById('aging-autopsy-tbody');
    autoTbody.innerHTML = '';
    const finalElems = final.elements;
    
    // Check if we have element-level data
    if (finalElems && finalElems.length > 0) {
        finalElems.forEach((el, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>Element ${idx + 1}</td>
                <td>${el.fri_cake.toFixed(3)}</td>
                <td>${el.fri_bio.toFixed(3)}</td>
                <td>${el.fri_nom.toFixed(3)}</td>
                <td>${el.fri_scale.toFixed(3)}</td>
                <td style="font-weight: bold;">${el.fri_total.toFixed(3)}</td>
                <td>${(el.active_area_eff * 100).toFixed(1)}%</td>
            `;
            autoTbody.appendChild(tr);
        });
    }

    // Mechanism Breakdown Chart (Doughnut)
    drawMechanismChart(final);

    // Performance Chart
    drawPerformanceChart(series);
}

let agingChartInstance = null;
let mechanismChartInstance = null;

function drawPerformanceChart(series) {
    const ctx = document.getElementById('aging-canvas-npf').getContext('2d');
    
    if (agingChartInstance) {
        agingChartInstance.destroy();
    }

    const labels = series.map(s => s.month);
    const npfData = series.map(s => s.npf_m3h);
    const pressData = series.map(s => s.feed_pressure_bar);
    const cipPoints = series.map(s => s.cip_event ? s.npf_m3h : null);

    agingChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'NPF (m³/h)',
                    data: npfData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    yAxisID: 'y',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Feed Pressure (bar)',
                    data: pressData,
                    borderColor: '#ef4444',
                    borderDash: [5, 5],
                    yAxisID: 'y1',
                    fill: false,
                    tension: 0.1
                },
                {
                    label: 'CIP Events',
                    data: cipPoints,
                    type: 'scatter',
                    backgroundColor: '#10b981',
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time (Months)' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'NPF' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Pressure (bar)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function drawMechanismChart(final) {
    const ctx = document.getElementById('aging-canvas-mechanism').getContext('2d');
    
    if (mechanismChartInstance) {
        mechanismChartInstance.destroy();
    }

    const data = [
        final.avg_fri_cake,
        final.avg_fri_bio,
        final.avg_fri_nom,
        final.avg_fri_scale,
        1 - final.avg_active_area_eff // Oxidation/Compaction area loss
    ];

    mechanismChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Particulate', 'Biofouling', 'Organic', 'Scaling', 'Irreversible (Oxid/Comp)'],
            datasets: [{
                data: data,
                backgroundColor: [
                    '#f59e0b', // amber
                    '#10b981', // emerald
                    '#8b5cf6', // violet
                    '#3b82f6', // blue
                    '#ef4444'  // red
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 12, font: { size: 10 } }
                }
            }
        }
    });
}
