/* =========================================================================
   PACE — PREMIUM RO PROCESS FLOW DIAGRAM GENERATOR
   ========================================================================= */

// --- Global State ---
const state = {
  passes: [[3, 2, 1], [2]], // Default: Pass 1 has 3 stages (3,2,1 vessels), Pass 2 has 1 stage (2 vessels)
  theme: {
    name: 'classic-pace',
    canvasBg: '#CEDDFF',
    vesselFill: '#FFFFF0',
    vesselStroke: '#000000',
    feed: '#555555',
    permeate: '#3B50D0',
    concentrate: '#C00000',
    pump: '#293990',
    label: '#000000'
  },
  geo: {
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
  },
  zoom: 0.95,
  pan: { x: 40, y: 20 },
  isDragging: false,
  dragStart: { x: 0, y: 0 },
  animateFlow: true,
  calc: {
    feedFlow: 100,      // m3/h
    recovery: 75,       // % overall
    showFlows: true,
    elementArea: 37.2,  // m2 (400 sq ft)
    elementsPerVessel: 6
  }
};

// --- Theme Presets ---
const THEME_PRESETS = {
  'dark-blueprint': {
    canvasBg: '#0f172a',
    vesselFill: '#1e293b',
    vesselStroke: '#64748b',
    feed: '#94a3b8',
    permeate: '#3b82f6',
    concentrate: '#ef4444',
    pump: '#0f766e',
    label: '#f8fafc'
  },
  'classic-pace': {
    canvasBg: '#CEDDFF',
    vesselFill: '#FFFFF0',
    vesselStroke: '#000000',
    feed: '#555555',
    permeate: '#3B50D0',
    concentrate: '#C00000',
    pump: '#293990',
    label: '#000000'
  },
  'light-modern': {
    canvasBg: '#f8fafc',
    vesselFill: '#ffffff',
    vesselStroke: '#0f172a',
    feed: '#64748b',
    permeate: '#2563eb',
    concentrate: '#dc2626',
    pump: '#0284c7',
    label: '#0f172a'
  },
  'cyber-neon': {
    canvasBg: '#050508',
    vesselFill: '#101018',
    vesselStroke: '#00ffcc',
    feed: '#ff00ff',
    permeate: '#00ffff',
    concentrate: '#ff3300',
    pump: '#ffff00',
    label: '#00ffcc'
  }
};

// --- DOM References ---
const DOM = {
  visualBuilder: document.getElementById('visualBuilderContainer'),
  addPassBtn: document.getElementById('addPassBtn'),
  cfgInput: document.getElementById('cfgInput'),
  copyJsonBtn: document.getElementById('copyJsonBtn'),
  presetsGrid: document.querySelector('.presets-grid'),
  colorPickers: {
    canvas: document.getElementById('color-canvas'),
    vesselFill: document.getElementById('color-vessel-fill'),
    vesselStroke: document.getElementById('color-vessel-stroke'),
    feed: document.getElementById('color-feed'),
    permeate: document.getElementById('color-permeate'),
    concentrate: document.getElementById('color-concentrate'),
    pump: document.getElementById('color-pump'),
    label: document.getElementById('color-label')
  },
  geoInputs: {
    vesselW: document.getElementById('geo-vessel-w'),
    vesselH: document.getElementById('geo-vessel-h'),
    vGap: document.getElementById('geo-v-gap'),
    stageGap: document.getElementById('geo-stage-gap'),
    passGap: document.getElementById('geo-pass-gap')
  },
  geoVals: {
    vesselW: document.getElementById('geo-vessel-w-val'),
    vesselH: document.getElementById('geo-vessel-h-val'),
    vGap: document.getElementById('geo-v-gap-val'),
    stageGap: document.getElementById('geo-stage-gap-val'),
    passGap: document.getElementById('geo-pass-gap-val')
  },
  calcInputs: {
    feedFlow: document.getElementById('calc-feed-flow'),
    recovery: document.getElementById('calc-recovery'),
    recoveryVal: document.getElementById('calc-recovery-val'),
    showFlows: document.getElementById('calc-show-flows')
  },
  metrics: {
    feedVal: document.getElementById('metric-feed-val'),
    permVal: document.getElementById('metric-perm-val'),
    concVal: document.getElementById('metric-conc-val'),
    fluxVal: document.getElementById('metric-flux-val')
  },
  stats: {
    passesCount: document.getElementById('stat-passes-count'),
    stagesCount: document.getElementById('stat-stages-count'),
    vesselsCount: document.getElementById('stat-vessels-count'),
    layoutDesc: document.getElementById('stat-layout-desc')
  },
  canvasViewport: document.getElementById('canvasViewport'),
  pfdCanvas: document.getElementById('pfdCanvas'),
  tooltip: document.getElementById('pfdTooltip'),
  themeToggleBtn: document.getElementById('themeToggleBtn'),
  sunIcon: document.getElementById('sunIcon'),
  moonIcon: document.getElementById('moonIcon'),
  zoomInBtn: document.getElementById('zoomInBtn'),
  zoomOutBtn: document.getElementById('zoomOutBtn'),
  zoomResetBtn: document.getElementById('zoomResetBtn'),
  toggleAnimBtn: document.getElementById('toggleAnimBtn'),
  exportSvgBtn: document.getElementById('exportSvgBtn'),
  exportPngBtn: document.getElementById('exportPngBtn')
};

// --- Initializing App ---
function init() {
  setupEventListeners();
  loadStateFromInput();
  syncSlidersUI();
  updateFlowMetrics();
  renderAll();
}

// --- Event Listeners Setup ---
function setupEventListeners() {
  // Tabs Navigation
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const tabId = `tab-${btn.dataset.tab}`;
      document.getElementById(tabId).classList.add('active');
    });
  });

  // Theme Toggle (Dark/Light Mode Skin)
  DOM.themeToggleBtn.addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark-mode');
    document.body.classList.toggle('light-mode', !isDark);
    DOM.sunIcon.classList.toggle('hidden', isDark);
    DOM.moonIcon.classList.toggle('hidden', !isDark);
    
    // Switch colors based on skin
    const presetName = isDark ? 'dark-blueprint' : 'light-modern';
    applyPreset(presetName);
  });

  // Presets Click
  document.querySelectorAll('.preset-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      applyPreset(card.dataset.preset);
    });
  });

  // Custom Color Pickers
  Object.keys(DOM.colorPickers).forEach(key => {
    DOM.colorPickers[key].addEventListener('input', (e) => {
      state.theme[key] = e.target.value;
      // Mark custom preset as active
      document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));
      renderAll();
    });
  });

  // Spacing Range Sliders
  Object.keys(DOM.geoInputs).forEach(key => {
    DOM.geoInputs[key].addEventListener('input', (e) => {
      const val = parseInt(e.target.value, 10);
      state.geo[key] = val;
      DOM.geoVals[key].innerText = `${val}px`;
      renderAll();
    });
  });

  // JSON Input
  DOM.cfgInput.addEventListener('input', () => {
    loadStateFromInput();
    updateFlowMetrics();
    renderAll();
  });

  // Copy JSON Code
  DOM.copyJsonBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(DOM.cfgInput.value).then(() => {
      const orig = DOM.copyJsonBtn.innerText;
      DOM.copyJsonBtn.innerText = 'Copied!';
      setTimeout(() => DOM.copyJsonBtn.innerText = orig, 2000);
    });
  });

  // Visual Builder: Add Pass
  DOM.addPassBtn.addEventListener('click', () => {
    state.passes.push([1]); // Add new pass with 1 stage (1 vessel)
    syncStateToInput();
    updateFlowMetrics();
    renderAll();
  });

  // Calculations Form Inputs
  DOM.calcInputs.feedFlow.addEventListener('input', (e) => {
    state.calc.feedFlow = parseFloat(e.target.value) || 100;
    updateFlowMetrics();
    renderAll();
  });

  DOM.calcInputs.recovery.addEventListener('input', (e) => {
    const val = parseInt(e.target.value, 10);
    state.calc.recovery = val;
    DOM.calcInputs.recoveryVal.innerText = val;
    updateFlowMetrics();
    renderAll();
  });

  DOM.calcInputs.showFlows.addEventListener('change', (e) => {
    state.calc.showFlows = e.target.checked;
    renderAll();
  });

  // Zoom and Pan Handlers
  DOM.canvasViewport.addEventListener('mousedown', startDrag);
  window.addEventListener('mousemove', drag);
  window.addEventListener('mouseup', endDrag);
  DOM.canvasViewport.addEventListener('wheel', handleWheel);

  DOM.zoomInBtn.addEventListener('click', () => adjustZoom(0.1));
  DOM.zoomOutBtn.addEventListener('click', () => adjustZoom(-0.1));
  DOM.zoomResetBtn.addEventListener('click', resetZoomPan);
  
  DOM.toggleAnimBtn.addEventListener('click', () => {
    state.animateFlow = !state.animateFlow;
    DOM.toggleAnimBtn.classList.toggle('active', state.animateFlow);
    renderAll();
  });

  // Exports
  DOM.exportSvgBtn.addEventListener('click', downloadSVG);
  DOM.exportPngBtn.addEventListener('click', downloadPNG);
}

// --- Sync state sliders to GUI inputs ---
function syncSlidersUI() {
  Object.keys(DOM.geoInputs).forEach(key => {
    DOM.geoInputs[key].value = state.geo[key];
    DOM.geoVals[key].innerText = `${state.geo[key]}px`;
  });
  DOM.calcInputs.feedFlow.value = state.calc.feedFlow;
  DOM.calcInputs.recovery.value = state.calc.recovery;
  DOM.calcInputs.recoveryVal.innerText = state.calc.recovery;
  DOM.calcInputs.showFlows.checked = state.calc.showFlows;
}

// --- Apply color presets ---
function applyPreset(name) {
  const colors = THEME_PRESETS[name];
  if (!colors) return;
  state.theme = { name, ...colors };
  
  // Set values on GUI color pickers
  DOM.colorPickers.canvas.value = colors.canvasBg;
  DOM.colorPickers.vesselFill.value = colors.vesselFill;
  DOM.colorPickers.vesselStroke.value = colors.vesselStroke;
  DOM.colorPickers.feed.value = colors.feed;
  DOM.colorPickers.permeate.value = colors.permeate;
  DOM.colorPickers.concentrate.value = colors.concentrate;
  DOM.colorPickers.pump.value = colors.pump;
  DOM.colorPickers.label.value = colors.label;

  // Set preset card active status
  document.querySelectorAll('.preset-card').forEach(c => {
    c.classList.toggle('active', c.dataset.preset === name);
  });

  renderAll();
}

// --- Load state from JSON Input box ---
function loadStateFromInput() {
  const val = DOM.cfgInput.value;
  try {
    const parsed = JSON.parse(val);
    if (Array.isArray(parsed) && parsed.every(p => Array.isArray(p) && p.every(n => Number.isInteger(n) && n > 0))) {
      state.passes = parsed;
      DOM.cfgInput.classList.remove('error');
    } else {
      throw new Error('Shape error');
    }
  } catch (e) {
    DOM.cfgInput.classList.add('error');
  }
}

// --- Sync UI structural edits back to JSON input ---
function syncStateToInput() {
  const jsonStr = JSON.stringify(state.passes);
  DOM.cfgInput.value = jsonStr;
  DOM.cfgInput.classList.remove('error');
}

// --- Flow balance calculations ---
function updateFlowMetrics() {
  const Q_f = state.calc.feedFlow;
  const Y = state.calc.recovery / 100;
  
  // Calculate flow totals
  const Q_p = Q_f * Y;
  const Q_c = Q_f - Q_p;
  
  // Count total vessels
  let totalVessels = 0;
  state.passes.forEach(p => {
    p.forEach(stageVessels => {
      totalVessels += stageVessels;
    });
  });

  // Calculate average Flux (LMH)
  // Area = Total vessels * elements per vessel * area per element
  const totalArea = totalVessels * state.calc.elementsPerVessel * state.calc.elementArea;
  const flux = totalArea > 0 ? (Q_p * 1000) / totalArea : 0; // LMH

  // Update UI stats
  DOM.metrics.feedVal.innerText = `${Q_f.toFixed(1)} m³/h`;
  DOM.metrics.permVal.innerText = `${Q_p.toFixed(1)} m³/h`;
  DOM.metrics.concVal.innerText = `${Q_c.toFixed(1)} m³/h`;
  DOM.metrics.fluxVal.innerText = `${flux.toFixed(1)} lmh`;

  // Update Quick Stats in top bar
  DOM.stats.passesCount.innerText = state.passes.length;
  DOM.stats.stagesCount.innerText = state.passes.reduce((sum, p) => sum + p.length, 0);
  DOM.stats.vesselsCount.innerText = totalVessels;
  DOM.stats.layoutDesc.innerText = JSON.stringify(state.passes);
}

// --- Visual Builder List rendering ---
function renderVisualBuilder() {
  DOM.visualBuilder.innerHTML = '';
  
  state.passes.forEach((passStages, pi) => {
    const passCard = document.createElement('div');
    passCard.className = 'pass-card';
    passCard.innerHTML = `
      <div class="pass-card-header">
        <span class="pass-card-title">Pass ${pi + 1}</span>
        <button class="text-btn danger" onclick="removePass(${pi})">Remove Pass</button>
      </div>
      <div class="stage-items-list" id="pass-${pi}-stages"></div>
      <div class="pass-card-controls">
        <button class="text-btn" onclick="addStage(${pi})">+ Add Stage</button>
      </div>
    `;
    
    DOM.visualBuilder.appendChild(passCard);
    const stagesContainer = document.getElementById(`pass-${pi}-stages`);
    
    passStages.forEach((vessels, si) => {
      const stageItem = document.createElement('div');
      stageItem.className = 'stage-item';
      stageItem.innerHTML = `
        <span class="stage-label">Stage ${si + 1}</span>
        <div class="stage-val-controls">
          <button class="circle-btn" onclick="adjustVesselCount(${pi}, ${si}, -1)">-</button>
          <span class="stage-vessel-count">${vessels}</span>
          <button class="circle-btn" onclick="adjustVesselCount(${pi}, ${si}, 1)">+</button>
          <button class="text-btn danger" style="margin-left:8px;" onclick="removeStage(${pi}, ${si})" title="Delete Stage">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      `;
      stagesContainer.appendChild(stageItem);
    });
  });
}

// --- Builder operations ---
window.removePass = function(passIndex) {
  if (state.passes.length <= 1) {
    alert("System must contain at least 1 Pass.");
    return;
  }
  state.passes.splice(passIndex, 1);
  syncStateToInput();
  updateFlowMetrics();
  renderAll();
};

window.addStage = function(passIndex) {
  state.passes[passIndex].push(1);
  syncStateToInput();
  updateFlowMetrics();
  renderAll();
};

window.removeStage = function(passIndex, stageIndex) {
  if (state.passes[passIndex].length <= 1) {
    alert("Pass must contain at least 1 Stage.");
    return;
  }
  state.passes[passIndex].splice(stageIndex, 1);
  syncStateToInput();
  updateFlowMetrics();
  renderAll();
};

window.adjustVesselCount = function(passIndex, stageIndex, delta) {
  const current = state.passes[passIndex][stageIndex];
  const newVal = Math.max(1, current + delta);
  state.passes[passIndex][stageIndex] = newVal;
  syncStateToInput();
  updateFlowMetrics();
  renderAll();
};

// --- SVG Rendering Core ---
function buildSVG() {
  const COLORS = state.theme;
  const GEO = state.geo;
  const centerY = 320;
  
  let x = 60;
  let fullMarkup = '';
  let passExits = [];
  let sysMaxTop = centerY;
  let sysMaxBottom = centerY;
  let pumpsMarkup = '';

  // Arrow markers definition
  const arrowMarkerDefs = `
    <defs>
      <marker id="pfd-ah-feed" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
        <path d="M2 1 L8 5 L2 9 Z" fill="${COLORS.feed}" />
      </marker>
      <marker id="pfd-ah-permeate" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
        <path d="M2 1 L8 5 L2 9 Z" fill="${COLORS.permeate}" />
      </marker>
      <marker id="pfd-ah-concentrate" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
        <path d="M2 1 L8 5 L2 9 Z" fill="${COLORS.concentrate}" />
      </marker>
    </defs>
  `;

  // Draw high-pressure pump icon
  function pumpIcon(cx, cy, scale = 1, labelText = 'HP PUMP') {
    const isBooster = labelText === 'BOOSTER';
    
    let baseD = isBooster 
      ? "M -16 16 L -22 28 L 22 28 L 16 16 Z" 
      : "M -38 16 L -44 28 L 22 28 L 16 16 Z";
    
    let baseRectX = isBooster ? -24 : -46;
    let baseRectW = isBooster ? 48 : 70;
    
    let motorMarkup = '';
    if (!isBooster) {
      motorMarkup = `
        <!-- Motor housing -->
        <rect x="-42" y="-14" width="24" height="28" rx="3" fill="#2B3B98" stroke="#ffffff" stroke-width="2" />
        <!-- Cooling fins -->
        <line x1="-36" y1="-14" x2="-36" y2="14" stroke="#ffffff" stroke-width="1.5" />
        <line x1="-30" y1="-14" x2="-30" y2="14" stroke="#ffffff" stroke-width="1.5" />
        <line x1="-24" y1="-14" x2="-24" y2="14" stroke="#ffffff" stroke-width="1.5" />
        <!-- Motor coupling -->
        <rect x="-18" y="-6" width="6" height="12" fill="#2B3B98" stroke="#ffffff" stroke-width="2" />
      `;
    }

    const textX = isBooster ? 0 : -11;

    return `
      <g class="pfd-pump" transform="translate(${cx},${cy}) scale(${scale})" cursor="pointer" data-type="pump" data-name="${labelText}">
        <!-- Base -->
        <path d="${baseD}" fill="#2B3B98" stroke="#ffffff" stroke-width="2" stroke-linejoin="round" />
        <rect x="${baseRectX}" y="28" width="${baseRectW}" height="4" fill="#2B3B98" stroke="#ffffff" stroke-width="2" />
        
        ${motorMarkup}
        
        <!-- Volute & Discharge Path -->
        <path d="M 30 -18 L 0 -18 A 18 18 0 1 0 16.1 -8 L 30 -8 Z" fill="#2B3B98" stroke="#ffffff" stroke-width="2" stroke-linejoin="round" />
        
        <!-- Discharge Flange -->
        <rect x="30" y="-21" width="6" height="16" fill="#2B3B98" stroke="#ffffff" stroke-width="2" />
        
        <!-- Inner Motor / Suction Eye -->
        <circle cx="0" cy="0" r="8" fill="#2B3B98" stroke="#ffffff" stroke-width="2" />
        
        <!-- Text label -->
        <text x="${textX}" y="44" font-size="11" font-weight="700" fill="${COLORS.label}" text-anchor="middle" font-family="Outfit, sans-serif">${labelText}</text>
      </g>
    `;
  }

  // Draw mixer icon
  function mixerIcon(cx, cy, scale = 1) {
    return `
      <g class="pfd-mixer" transform="translate(${cx},${cy}) scale(${scale})" cursor="pointer" data-type="mixer">
        <circle cx="0" cy="0" r="10" fill="#FFFFF0" stroke="${COLORS.vesselStroke}" stroke-width="2" />
        <line x1="-7" y1="-7" x2="7" y2="7" stroke="${COLORS.vesselStroke}" stroke-width="2" />
        <line x1="-7" y1="7" x2="7" y2="-7" stroke="${COLORS.vesselStroke}" stroke-width="2" />
      </g>
    `;
  }

  // Draw vessel shape
  function vesselShape(vx, vy, vw, vh, passIdx, stageIdx, vesselIdx) {
    const midY = vy + vh / 2;
    const label = `PV #${vesselIdx + 1}`;
    
    // Construct the outer shell path
    const p1x = vx, p1y = vy;
    const p2x = vx + 10, p2y = vy;
    const p3x = vx + 16, p3y = vy + 4;
    const p4x = vx + vw - 16, p4y = vy + 4;
    const p5x = vx + vw - 10, p5y = vy;
    const p6x = vx + vw, p6y = vy;
    const p7x = vx + vw, p7y = vy + vh;
    const p8x = vx + vw - 10, p8y = vy + vh;
    const p9x = vx + vw - 16, p9y = vy + vh - 4;
    const p10x = vx + 16, p10y = vy + vh - 4;
    const p11x = vx + 10, p11y = vy + vh;
    const p12x = vx, p12y = vy + vh;

    const pathD = `M ${p1x} ${p1y} L ${p2x} ${p2y} L ${p3x} ${p3y} L ${p4x} ${p4y} L ${p5x} ${p5y} L ${p6x} ${p6y} L ${p7x} ${p7y} L ${p8x} ${p8y} L ${p9x} ${p9y} L ${p10x} ${p10y} L ${p11x} ${p11y} L ${p12x} ${p12y} Z`;

    let s = `
      <g class="pfd-vessel" data-pass="${passIdx}" data-stage="${stageIdx}" data-vessel="${vesselIdx}">
        <path d="${pathD}" fill="${COLORS.vesselFill}" stroke="${COLORS.vesselStroke}" stroke-width="1.5" stroke-linejoin="round" />
        
        <!-- Vertical lines for end caps -->
        <line x1="${p2x}" y1="${p2y}" x2="${p11x}" y2="${p11y}" stroke="${COLORS.vesselStroke}" stroke-width="1.5" />
        <line x1="${p5x}" y1="${p5y}" x2="${p8x}" y2="${p8y}" stroke="${COLORS.vesselStroke}" stroke-width="1.5" />
        
        <!-- Diagonal membrane line (top-left to bottom-right) -->
        <line x1="${p3x}" y1="${p3y}" x2="${p9x}" y2="${p9y}" stroke="${COLORS.vesselStroke}" stroke-width="2.5" />
        
        <!-- Label with background to mask the diagonal line -->
        <rect x="${vx + vw / 2 - 20}" y="${midY - 8}" width="40" height="16" fill="${COLORS.vesselFill}" />
        <text x="${vx + vw / 2}" y="${midY + 4}" font-size="11" fill="${COLORS.label}" font-weight="600" text-anchor="middle" font-family="Inter, sans-serif" pointer-events="none">${label}</text>
      </g>
    `;
    return s;
  }

  // Create stream paths (orthogonal routing) for animations
  function streamPath(points, color, flowClass = '', addMarker = false) {
    if (points.length < 2) return '';
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      d += ` L ${points[i].x} ${points[i].y}`;
    }
    const animClass = state.animateFlow ? 'flow-animating' : '';
    let markerAttr = '';
    if (addMarker) {
      if (color === COLORS.feed) markerAttr = 'marker-end="url(#pfd-ah-feed)"';
      else if (color === COLORS.permeate) markerAttr = 'marker-end="url(#pfd-ah-permeate)"';
      else if (color === COLORS.concentrate) markerAttr = 'marker-end="url(#pfd-ah-concentrate)"';
    }
    return `<path d="${d}" stroke="${color}" fill="none" stroke-width="2" class="stream-path ${animClass} ${flowClass}" ${markerAttr} />`;
  }

  // Linear calculations model values
  const Q_f = state.calc.feedFlow;
  const Y_overall = state.calc.recovery / 100;
  
  // Calculate flow rates per pass
  // Assuming Pass 1 recovery = Y_overall, Pass 2 recovery = 0.85
  const passFlows = [];
  let currentFeed = Q_f;
  
  state.passes.forEach((stages, pi) => {
    const passRec = pi === 0 ? Y_overall : 0.85; // Pass 2+ is treated as 2nd pass polishing
    const passPerm = currentFeed * passRec;
    const passConc = currentFeed - passPerm;
    
    // Stage recovery distribution: 1 - (1-Y_pass)^(1/k)
    const k = stages.length;
    const stageRec = 1 - Math.pow(1 - passRec, 1 / k);
    
    const stageFlows = [];
    let stageFeed = currentFeed;
    
    stages.forEach((v, si) => {
      const stagePerm = stageFeed * stageRec;
      const stageConc = stageFeed - stagePerm;
      stageFlows.push({
        feed: stageFeed,
        permeate: stagePerm,
        concentrate: stageConc
      });
      stageFeed = stageConc; // Next stage feed is current stage concentrate
    });
    
    passFlows.push({
      feed: currentFeed,
      permeate: passPerm,
      concentrate: passConc,
      stages: stageFlows
    });
    
    currentFeed = passPerm; // Double pass: 2nd pass feed is 1st pass permeate
  });

  // Render main inlet stream with offset for pump suction/discharge
  const pumpCy = centerY + 13;
  const pumpCx = x + GEO.feedStub + 34;
  
  const mixCx = x - 10;
  const mixCy = pumpCy;

  // The pump casing extends to pumpCx + 36. We place the start of the manifold (x) well past it.
  const newX = pumpCx + 90;
  const feedInXFirst = newX - GEO.manifoldMargin;

  // Raw feed into mixer (stops at left edge of circle)
  fullMarkup += streamPath([{ x: mixCx - 40, y: pumpCy }, { x: mixCx - 10, y: pumpCy }], COLORS.feed, '', true);
  // Mixed line from mixer to suction (starts at right edge of circle, stops at left edge of pump motor)
  fullMarkup += streamPath([{ x: mixCx + 10, y: pumpCy }, { x: pumpCx - 46, y: pumpCy }], COLORS.feed, '', true);
  // Line out of discharge (top)
  fullMarkup += streamPath([{ x: pumpCx, y: centerY }, { x: feedInXFirst, y: centerY }], COLORS.feed);
  
  fullMarkup += `<text x="${mixCx - 36}" y="${pumpCy - 8}" font-size="11" font-weight="600" fill="${COLORS.label}" font-family="Outfit, sans-serif">Feed</text>`;
  
  if (state.calc.showFlows) {
    fullMarkup += `<text x="${mixCx - 36}" y="${pumpCy + 16}" font-size="9" font-weight="500" fill="${COLORS.feed}" font-family="Fira Code, monospace">${Q_f.toFixed(1)} m³/h</text>`;
  }

  pumpsMarkup += mixerIcon(mixCx, mixCy, 1);
  // Draw main feed pump (added to pumpsMarkup to render on top of the flow line)
  pumpsMarkup += pumpIcon(pumpCx, pumpCy, 1, 'FEED PUMP');
  
  x = newX;

  // Render each pass
  state.passes.forEach((passStages, pi) => {
    const passFlow = passFlows[pi];
    const maxVesselsInPass = Math.max(...passStages.map(v => v > 4 ? 4 : v));
    const passHeight = maxVesselsInPass * GEO.vesselH + (maxVesselsInPass - 1) * GEO.vGap;
    const firstStageStartY = centerY - passHeight / 2;
    
    fullMarkup += `
      <g transform="translate(${x}, ${firstStageStartY - GEO.headerMargin - GEO.passHeaderMargin})">
        <text x="0" y="0" font-size="13" font-weight="800" fill="${COLORS.label}" font-family="Outfit, sans-serif">PASS ${pi + 1}</text>
        <line x1="0" y1="4" x2="54" y2="4" stroke="${COLORS.label}" stroke-width="2" />
      </g>
    `;

    let stageX = x;
    let feedFromX = stageX - 26;
    let feedFromY = centerY;
    let stagePermExits = [];
    let lastConcExit = null;
    let passMaxTop = centerY;
    let passMaxBottom = centerY;

    passStages.forEach((stageVessels, si) => {
      const stageFlow = passFlow.stages[si];
      const feedColor = si === 0 ? (pi === 0 ? COLORS.feed : COLORS.permeate) : COLORS.concentrate;
      const permHeaderY = firstStageStartY - GEO.headerMargin;
      const concManifoldY = firstStageStartY + passHeight + GEO.manifoldMargin;
      const stageExitX = stageX + GEO.vesselW + 30 + GEO.stageExitPad;

      passMaxTop = Math.min(passMaxTop, permHeaderY);
      passMaxBottom = Math.max(passMaxBottom, concManifoldY);

      fullMarkup += `<text x="${stageX + GEO.vesselW / 2}" y="${firstStageStartY - 14}" font-size="11" font-weight="700" fill="${COLORS.label}" text-anchor="middle" font-family="Outfit, sans-serif">Stage ${si + 1}</text>`;

      const feedInX = stageX - 26;
      if (si === 0) {
        fullMarkup += streamPath([{ x: feedFromX, y: feedFromY }, { x: feedInX, y: centerY }], feedColor);
      } else {
        const upX = feedFromX + 20;
        const pumpCy = centerY + 13;
        const pumpCx = upX + 34;
        
        fullMarkup += streamPath([
          { x: feedFromX, y: feedFromY },
          { x: upX, y: feedFromY },
          { x: upX, y: pumpCy },
          { x: pumpCx - 18, y: pumpCy }
        ], feedColor, '', true);
        
        fullMarkup += streamPath([
          { x: pumpCx, y: centerY },
          { x: feedInX, y: centerY }
        ], feedColor);
        
        pumpsMarkup += pumpIcon(pumpCx, pumpCy, 1, 'BOOSTER');
        
        if (state.calc.showFlows) {
          fullMarkup += `<text x="${upX + 4}" y="${pumpCy - 6}" font-size="8.5" font-weight="500" fill="${COLORS.concentrate}" font-family="Fira Code, monospace">${stageFlow.feed.toFixed(1)}</text>`;
        }
      }

      const displayCount = stageVessels > 4 ? 4 : stageVessels;
      let renderSlots = [];
      if (stageVessels <= 4) {
        for (let i=0; i<stageVessels; i++) renderSlots.push({ type: 'vessel', labelIdx: i });
      } else {
        renderSlots.push({ type: 'vessel', labelIdx: 0 });
        renderSlots.push({ type: 'vessel', labelIdx: 1 });
        renderSlots.push({ type: 'dots' });
        renderSlots.push({ type: 'vessel', labelIdx: stageVessels - 1 });
      }

      let pYs = [];
      let cYs = [];
      
      let feedMinY = centerY;
      let feedMaxY = centerY;

      renderSlots.forEach((slot, vi) => {
        const vy = firstStageStartY + vi * (GEO.vesselH + GEO.vGap);
        const vyMid = vy + GEO.vesselH / 2;
        
        feedMinY = Math.min(feedMinY, vyMid);
        feedMaxY = Math.max(feedMaxY, vyMid);

        if (slot.type === 'vessel') {
          fullMarkup += streamPath([{ x: feedInX, y: vyMid }, { x: stageX, y: vyMid }], feedColor, '', true);
          fullMarkup += vesselShape(stageX, vy, GEO.vesselW, GEO.vesselH, pi, si, slot.labelIdx);
          const pY = vy + GEO.vesselH * 0.25;
          const cY = vy + GEO.vesselH * 0.75;
          pYs.push(pY);
          cYs.push(cY);
          fullMarkup += streamPath([{ x: stageX + GEO.vesselW, y: pY }, { x: stageX + GEO.vesselW + 14, y: pY }], COLORS.permeate, '', true);
          fullMarkup += streamPath([{ x: stageX + GEO.vesselW, y: cY }, { x: stageX + GEO.vesselW + 30, y: cY }], COLORS.concentrate, '', true);
        } else if (slot.type === 'dots') {
          // Add a short feed stub pointing to the empty space for the dots
          fullMarkup += streamPath([{ x: feedInX, y: vyMid }, { x: stageX - 10, y: vyMid }], feedColor);
          fullMarkup += `<text x="${stageX + GEO.vesselW / 2}" y="${vyMid + 6}" font-size="24" font-weight="700" fill="${COLORS.label}" text-anchor="middle" font-family="Outfit, sans-serif">⋮</text>`;
        }
      });

      if (feedMinY < feedMaxY) {
        // Vertical feed distribution line
        fullMarkup += streamPath([{ x: feedInX, y: feedMinY }, { x: feedInX, y: feedMaxY }], feedColor);
      }

      const blueBusX = stageX + GEO.vesselW + 14;
      const redBusX = stageX + GEO.vesselW + 30;

      // Vertical collecting manifolds
      if (displayCount > 1) {
        fullMarkup += streamPath([{ x: blueBusX, y: pYs[0] }, { x: blueBusX, y: pYs[pYs.length - 1] }], COLORS.permeate);
        fullMarkup += streamPath([{ x: redBusX, y: cYs[0] }, { x: redBusX, y: cYs[cYs.length - 1] }], COLORS.concentrate);
      }
      
      const blueMergeY = (pYs[0] + pYs[pYs.length - 1]) / 2;
      const redMergeY = (cYs[0] + cYs[cYs.length - 1]) / 2;

      // Pipe to header/manifold exits
      fullMarkup += streamPath([
        { x: blueBusX, y: blueMergeY },
        { x: blueBusX, y: permHeaderY },
        { x: stageExitX, y: permHeaderY }
      ], COLORS.permeate);
      
      fullMarkup += streamPath([
        { x: redBusX, y: redMergeY },
        { x: redBusX, y: concManifoldY },
        { x: stageExitX, y: concManifoldY }
      ], COLORS.concentrate);

      stagePermExits.push({ x: stageExitX, y: permHeaderY });
      lastConcExit = { x: stageExitX, y: concManifoldY };

      // Flow indicators next to stage exit lines
      if (state.calc.showFlows) {
        fullMarkup += `<text x="${stageExitX - 22}" y="${permHeaderY - 6}" font-size="8.5" font-weight="600" fill="${COLORS.permeate}" font-family="Fira Code, monospace">${stageFlow.permeate.toFixed(1)}</text>`;
        fullMarkup += `<text x="${stageExitX - 22}" y="${concManifoldY + 12}" font-size="8.5" font-weight="600" fill="${COLORS.concentrate}" font-family="Fira Code, monospace">${stageFlow.concentrate.toFixed(1)}</text>`;
      }

      // Advance to next stage coordinate
      if (si < passStages.length - 1) {
        const nextX = stageExitX + GEO.stageGap;
        feedFromX = stageExitX;
        feedFromY = concManifoldY;
        stageX = nextX;
      } else {
        stageX = stageExitX;
      }
    });

    // PASS HEADERS COLLECTING
    const passHeaderY = passMaxTop - GEO.passHeaderMargin + GEO.headerMargin;
    let minHx = Infinity, maxHx = -Infinity;
    
    stagePermExits.forEach(p => {
      fullMarkup += streamPath([{ x: p.x, y: p.y }, { x: p.x, y: passHeaderY }], COLORS.permeate);
      minHx = Math.min(minHx, p.x);
      maxHx = Math.max(maxHx, p.x);
    });
    
    // Connect all permeate lines horizontally
    fullMarkup += streamPath([{ x: minHx, y: passHeaderY }, { x: maxHx, y: passHeaderY }], COLORS.permeate);

    passExits.push({
      permeateX: maxHx,
      permeateY: passHeaderY,
      concentrateX: lastConcExit.x,
      concentrateY: lastConcExit.y
    });

    sysMaxTop = Math.min(sysMaxTop, passHeaderY);
    sysMaxBottom = Math.max(sysMaxBottom, lastConcExit.y);

    // Coordinate prep for next pass
    x = stageX + GEO.passGap;

    // Double Pass connection: Pass 1 Permeate -> Pump -> Pass 2 Feed
    if (pi < state.passes.length - 1) {
      const p1ExitX = maxHx;
      const pumpCy = centerY + 13;
      const pumpCx = p1ExitX + 48;
      
      const newX = pumpCx + 90;
      const feedInXPass = newX - GEO.manifoldMargin;
      
      // Line into suction (center) - stops at left edge of motor housing
      fullMarkup += streamPath([
        { x: p1ExitX, y: passHeaderY },
        { x: p1ExitX + 18, y: passHeaderY },
        { x: p1ExitX + 18, y: pumpCy },
        { x: pumpCx - 46, y: pumpCy }
      ], COLORS.permeate, 'flow-fast', true);
      
      // Line out of discharge (top)
      fullMarkup += streamPath([
        { x: pumpCx, y: centerY },
        { x: feedInXPass, y: centerY }
      ], COLORS.permeate, 'flow-fast');
      
      // Add pump to pumps layer so it draws on top of the line
      pumpsMarkup += pumpIcon(pumpCx, pumpCy, 1, 'INTERPASS PUMP');
      
      x = newX; // Reposition starting x for Pass 2
    }
  });

  // FINAL OUTLETS: SYSTEM PERMEATE & CONCENTRATE
  const last = passExits[passExits.length - 1];
  
  // 1. Draw final permeate stream outlet with marker
  fullMarkup += streamPath([{ x: last.permeateX, y: last.permeateY }, { x: last.permeateX + GEO.outletStub, y: last.permeateY }], COLORS.permeate);
  // Arrow head marker
  fullMarkup += `<line x1="${last.permeateX + GEO.outletStub - 6}" y1="${last.permeateY}" x2="${last.permeateX + GEO.outletStub}" y2="${last.permeateY}" stroke="${COLORS.permeate}" stroke-width="2.6" marker-end="url(#pfd-ah-permeate)" />`;
  fullMarkup += `<text x="${last.permeateX + GEO.outletStub + 12}" y="${last.permeateY + 4}" font-size="13" font-weight="800" fill="${COLORS.permeate}" font-family="Outfit, sans-serif">PERMEATE</text>`;
  
  if (state.calc.showFlows) {
    const finalPerm = passExits.length > 1 ? passFlows[1].permeate : passFlows[0].permeate;
    fullMarkup += `<text x="${last.permeateX + 6}" y="${last.permeateY - 8}" font-size="10" font-weight="700" fill="${COLORS.permeate}" font-family="Fira Code, monospace">${finalPerm.toFixed(1)} m³/h</text>`;
  }

  // 2. Draw final concentrate collection manifold and outlet
  const finalManifoldY = Math.max(...passExits.map(p => p.concentrateY)) + 50; // drop down more to give space
  
  const hasRecycle = state.passes.length >= 2;
  const recyclePass = 1; // Pass 2

  passExits.forEach((p, idx) => {
    // Drop down each pass concentrate to final bottom header
    fullMarkup += streamPath([
      { x: p.concentrateX, y: p.concentrateY },
      { x: p.concentrateX, y: finalManifoldY }
    ], COLORS.concentrate);
    
    // Add flow node labels for individual pass concentrate
    if (state.calc.showFlows) {
      fullMarkup += `<text x="${p.concentrateX + 4}" y="${(p.concentrateY + finalManifoldY) / 2}" font-size="8.5" font-weight="500" fill="${COLORS.concentrate}" font-family="Fira Code, monospace">${passFlows[idx].concentrate.toFixed(1)}</text>`;
    }
  });

  // Connect bottom header horizontally
  const firstConcX = passExits[0].concentrateX;
  const lastConcX = passExits[passExits.length - 1].concentrateX;
  if (passExits.length > 1) {
    fullMarkup += streamPath([{ x: firstConcX, y: finalManifoldY }, { x: lastConcX, y: finalManifoldY }], COLORS.concentrate);
  }
  
  // Final outlet
  fullMarkup += streamPath([{ x: lastConcX, y: finalManifoldY }, { x: lastConcX + GEO.outletStub, y: finalManifoldY }], COLORS.concentrate);
  
  // Recycle loop drawing (Partial recycle from Pass 2)
  if (hasRecycle) {
    const p = passExits[recyclePass];
    const branchY = p.concentrateY + 14; // Branch off cleanly above the flow text
    const recycleDropX = p.concentrateX - 40; // Drop down on the LEFT side, between the passes
    const recycleY = finalManifoldY + 40;
    const startMixCx = 60 - 10; // Derived from x=60 initial value
    const startMixCy = centerY + 13;
    
    fullMarkup += streamPath([
      { x: p.concentrateX, y: branchY },
      { x: recycleDropX, y: branchY },
      { x: recycleDropX, y: recycleY },
      { x: startMixCx, y: recycleY },
      { x: startMixCx, y: startMixCy + 10 }
    ], COLORS.concentrate, 'flow-fast', true);
    
    if (state.calc.showFlows) {
      fullMarkup += `<text x="${startMixCx + 8}" y="${recycleY - 6}" font-size="8.5" font-weight="500" fill="${COLORS.concentrate}" font-family="Fira Code, monospace">Pass ${recyclePass + 1} Recycle (Partial)</text>`;
    }
  }

  // Arrow head marker
  fullMarkup += `<line x1="${lastConcX + GEO.outletStub - 6}" y1="${finalManifoldY}" x2="${lastConcX + GEO.outletStub}" y2="${finalManifoldY}" stroke="${COLORS.concentrate}" stroke-width="2.6" marker-end="url(#pfd-ah-concentrate)" />`;
  fullMarkup += `<text x="${lastConcX + GEO.outletStub + 12}" y="${finalManifoldY + 4}" font-size="13" font-weight="800" fill="${COLORS.concentrate}" font-family="Outfit, sans-serif">CONCENTRATE</text>`;
  
  if (state.calc.showFlows) {
    const finalConc = Q_f - (passExits.length > 1 ? passFlows[1].permeate : passFlows[0].permeate);
    fullMarkup += `<text x="${lastConcX + 6}" y="${finalManifoldY + 16}" font-size="10" font-weight="700" fill="${COLORS.concentrate}" font-family="Fira Code, monospace">${finalConc.toFixed(1)} m³/h</text>`;
  }

  // Update bounds for viewBox sizing
  sysMaxBottom = Math.max(sysMaxBottom, hasRecycle ? finalManifoldY + 60 : finalManifoldY + 40);
  sysMaxTop = Math.min(sysMaxTop, last.permeateY - 40);

  const totalWidth = Math.max(last.permeateX, lastConcX) + GEO.outletStub + 150;
  const viewMinY = sysMaxTop - 30;
  const viewHeight = (sysMaxBottom + 30) - viewMinY;

  const svgOpening = `<svg id="pfdSvg" xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="${viewHeight}" viewBox="0 ${viewMinY} ${totalWidth} ${viewHeight}" style="background-color: transparent;">`;
  
  return svgOpening + arrowMarkerDefs + fullMarkup + pumpsMarkup + `</svg>`;
}

// --- Main Render coordinator ---
function renderAll() {
  renderVisualBuilder();
  
  // Build and inject SVG PFD
  const svgContent = buildSVG();
  DOM.pfdCanvas.innerHTML = svgContent;
  
  // Reapply zoom/pan transforms
  updateTransform();
  
  // Re-bind interactive tooltips & events to SVG elements
  setupSVGInteractivity();
}

// --- Zoom / Pan Utilities ---
function updateTransform() {
  DOM.pfdCanvas.style.transform = `translate(${state.pan.x}px, ${state.pan.y}px) scale(${state.zoom})`;
}

function adjustZoom(delta) {
  state.zoom = Math.min(3, Math.max(0.3, state.zoom + delta));
  updateTransform();
}

function resetZoomPan() {
  state.zoom = 0.95;
  state.pan = { x: 40, y: 20 };
  updateTransform();
}

function handleWheel(e) {
  e.preventDefault();
  const zoomFactor = 1.05;
  const oldZoom = state.zoom;
  
  if (e.deltaY < 0) {
    state.zoom = Math.min(3, state.zoom * zoomFactor);
  } else {
    state.zoom = Math.max(0.3, state.zoom / zoomFactor);
  }
  
  // Adjust pan so zoom focuses on cursor
  const rect = DOM.canvasViewport.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  state.pan.x = mouseX - (mouseX - state.pan.x) * (state.zoom / oldZoom);
  state.pan.y = mouseY - (mouseY - state.pan.y) * (state.zoom / oldZoom);
  
  updateTransform();
}

function startDrag(e) {
  if (e.target.closest('.canvas-floating-controls')) return; // Avoid drag on UI buttons
  state.isDragging = true;
  state.dragStart.x = e.clientX - state.pan.x;
  state.dragStart.y = e.clientY - state.pan.y;
  DOM.canvasViewport.style.cursor = 'grabbing';
}

function drag(e) {
  if (!state.isDragging) return;
  state.pan.x = e.clientX - state.dragStart.x;
  state.pan.y = e.clientY - state.dragStart.y;
  updateTransform();
}

function endDrag() {
  state.isDragging = false;
  DOM.canvasViewport.style.cursor = 'grab';
}

// --- Tooltips & SVG Interactivity ---
function setupSVGInteractivity() {
  const vessels = DOM.pfdCanvas.querySelectorAll('.pfd-vessel');
  vessels.forEach(vessel => {
    vessel.addEventListener('mouseenter', showVesselTooltip);
    vessel.addEventListener('mousemove', moveTooltip);
    vessel.addEventListener('mouseleave', hideTooltip);
  });

  const pumps = DOM.pfdCanvas.querySelectorAll('.pfd-pump');
  pumps.forEach(pump => {
    pump.addEventListener('mouseenter', showPumpTooltip);
    pump.addEventListener('mousemove', moveTooltip);
    pump.addEventListener('mouseleave', hideTooltip);
  });
}

function showVesselTooltip(e) {
  const g = e.currentTarget;
  const passIdx = parseInt(g.dataset.pass, 10);
  const stageIdx = parseInt(g.dataset.stage, 10);
  const vesselIdx = parseInt(g.dataset.vessel, 10);
  
  // Compute individual vessel flow estimation for tooltip
  const passFlow = passFlowsEstimate()[passIdx];
  const stageFlow = passFlow.stages[stageIdx];
  const stageVesselCount = state.passes[passIdx][stageIdx];
  
  // Parallel vessel flow rate splits
  const vFeed = stageFlow.feed / stageVesselCount;
  const vPerm = stageFlow.permeate / stageVesselCount;
  const vConc = stageFlow.concentrate / stageVesselCount;

  DOM.tooltip.innerHTML = `
    <div class="pfd-tooltip-title">Pressure Vessel Details</div>
    <div class="pfd-tooltip-row">
      <span class="pfd-tooltip-lbl">Location:</span>
      <span class="pfd-tooltip-val">P${passIdx+1} - S${stageIdx+1} - PV${vesselIdx+1}</span>
    </div>
    <div class="pfd-tooltip-row">
      <span class="pfd-tooltip-lbl">Feed Flow:</span>
      <span class="pfd-tooltip-val">${vFeed.toFixed(2)} m³/h</span>
    </div>
    <div class="pfd-tooltip-row">
      <span class="pfd-tooltip-lbl">Permeate:</span>
      <span class="pfd-tooltip-val">${vPerm.toFixed(2)} m³/h</span>
    </div>
    <div class="pfd-tooltip-row">
      <span class="pfd-tooltip-lbl">Concentrate:</span>
      <span class="pfd-tooltip-val">${vConc.toFixed(2)} m³/h</span>
    </div>
  `;
  DOM.tooltip.classList.remove('hidden');
}

function showPumpTooltip(e) {
  const g = e.currentTarget;
  const pumpName = g.dataset.name;
  
  let desc = 'High Pressure Process Pump';
  let flowVal = state.calc.feedFlow;
  
  if (pumpName === 'INTERPASS PUMP') {
    desc = 'Second Pass Feed Booster Pump';
    const flows = passFlowsEstimate();
    flowVal = flows[0].permeate;
  }

  DOM.tooltip.innerHTML = `
    <div class="pfd-tooltip-title">${pumpName}</div>
    <div class="pfd-tooltip-row">
      <span class="pfd-tooltip-lbl">Type:</span>
      <span class="pfd-tooltip-val">Centrifugal</span>
    </div>
    <div class="pfd-tooltip-row">
      <span class="pfd-tooltip-lbl">Flow Rate:</span>
      <span class="pfd-tooltip-val">${flowVal.toFixed(1)} m³/h</span>
    </div>
    <div style="font-size: 9.5px; color: #94a3b8; margin-top: 4px;">
      ${desc}
    </div>
  `;
  DOM.tooltip.classList.remove('hidden');
}

function moveTooltip(e) {
  // Position tooltip relative to viewport
  const viewportRect = DOM.canvasViewport.getBoundingClientRect();
  const tooltipW = DOM.tooltip.offsetWidth;
  const tooltipH = DOM.tooltip.offsetHeight;
  
  let x = e.clientX - viewportRect.left + 15;
  let y = e.clientY - viewportRect.top + 15;
  
  // Keep inside viewport bounds
  if (x + tooltipW > viewportRect.width) {
    x = e.clientX - viewportRect.left - tooltipW - 15;
  }
  if (y + tooltipH > viewportRect.height) {
    y = e.clientY - viewportRect.top - tooltipH - 15;
  }
  
  DOM.tooltip.style.left = `${x}px`;
  DOM.tooltip.style.top = `${y}px`;
}

function hideTooltip() {
  DOM.tooltip.classList.add('hidden');
}

// --- Helper: recalculate flows specifically for tooltip queries ---
function passFlowsEstimate() {
  const Q_f = state.calc.feedFlow;
  const Y_overall = state.calc.recovery / 100;
  const passFlows = [];
  let currentFeed = Q_f;
  
  state.passes.forEach((stages, pi) => {
    const passRec = pi === 0 ? Y_overall : 0.85;
    const passPerm = currentFeed * passRec;
    const passConc = currentFeed - passPerm;
    const k = stages.length;
    const stageRec = 1 - Math.pow(1 - passRec, 1 / k);
    const stageFlows = [];
    let stageFeed = currentFeed;
    
    stages.forEach((v, si) => {
      const stagePerm = stageFeed * stageRec;
      const stageConc = stageFeed - stagePerm;
      stageFlows.push({
        feed: stageFeed,
        permeate: stagePerm,
        concentrate: stageConc
      });
      stageFeed = stageConc;
    });
    
    passFlows.push({
      feed: currentFeed,
      permeate: passPerm,
      concentrate: passConc,
      stages: stageFlows
    });
    
    currentFeed = passPerm;
  });
  
  return passFlows;
}

// --- SVG / PNG Export Downloads ---
function getSelfContainedSVG() {
  const svgEl = document.getElementById('pfdSvg');
  if (!svgEl) return '';
  
  // Clone element to avoid modifying original layout properties
  const clone = svgEl.cloneNode(true);
  
  // Inject explicit CSS styles derived from theme custom properties
  const COLORS = state.theme;
  const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
  
  // Re-map stream paths to correct hardcoded styles since animation might strip CSS links
  styleEl.textContent = `
    .stream-path {
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .pfd-vessel {
      transition: fill 0.2s, stroke 0.2s;
    }
    svg {
      background-color: ${COLORS.canvasBg};
    }
  `;
  clone.insertBefore(styleEl, clone.firstChild);
  
  // Serialize
  const serializer = new XMLSerializer();
  return serializer.serializeToString(clone);
}

function downloadSVG() {
  const svgMarkup = getSelfContainedSVG();
  const blob = new Blob([svgMarkup], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `PACE_RO_PFD_Layout.svg`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function downloadPNG() {
  const svgMarkup = getSelfContainedSVG();
  const svgEl = document.getElementById('pfdSvg');
  if (!svgEl) return;
  
  const width = svgEl.width.baseVal.value;
  const height = svgEl.height.baseVal.value;
  
  const blob = new Blob([svgMarkup], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    
    const ctx = canvas.getContext('2d');
    
    // Draw background since SVG background transparency might bleed through
    ctx.fillStyle = state.theme.canvasBg;
    ctx.fillRect(0, 0, width, height);
    
    ctx.drawImage(img, 0, 0);
    
    // Trigger download
    const pngUrl = canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.href = pngUrl;
    link.download = `PACE_RO_PFD_Layout.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  };
  img.src = url;
}

// --- Run Init ---
window.addEventListener('DOMContentLoaded', init);
