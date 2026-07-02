# PACE — Project Handoff Documentation (A-Z Guide)

Welcome to the **PACE** (PHREEQC-Assisted Calculation Engine) Projection Software project. This document serves as the master guide for developers taking over the codebase, detailing the architecture, core calculation engines, APIs, and the index of specifications.

---

## 1. Project Overview
PACE is a desktop-friendly, offline-capable membrane projection and scaling prediction software. It simulates reverse osmosis (RO) and nanofiltration (NF) desalination systems, projects scaling saturation indices (SI) dynamically using **PHREEQC**, and models multi-year membrane degradation (aging) using a physics-based differential equation solver.

---

## 2. System Architecture

The application is built on a decoupled, client-server model designed to run entirely locally:

```
┌─────────────────────────────────┐
│       Frontend UI/UX            │
│   (HTML5 / CSS3 / Vanilla JS)   │  ◄──┐
└────────────────┬────────────────┘     │ Local REST API
                 │                      │ (HTTP JSON on Port 8000)
┌────────────────▼────────────────┐     │
│        FastAPI Backend          │  ───┘
│    (Python / PHREEQPython)      │
└─────────────────────────────────┘
```

*   **Frontend (`ui_ux_design/`)**: A modern, single-page application built using vanilla HTML/CSS and JS. It features a Process Flow Diagram (PFD) dynamic vector drawer, Chart.js trend lines, and native file pickers for project imports/exports.
*   **Backend (`backend/`)**: A FastAPI Python server wrapping the calculation modules. It communicates with PHREEQC via `phreeqpython` for thermodynamic calculations.

---

## 3. Directory & File Index

### Backend Engines (`backend/`)
*   [server.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/server.py): The FastAPI application defining JSON request/response schemas and endpoints.
*   [calc_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/calc_engine.py): The core RO element simulator. Implements Spiegler-Kedem and Solution-Diffusion mass transport models with temperature correction factors (TCF) and concentration polarization (CP).
*   [system_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/system_engine.py): Models multi-stage assemblies, multi-pass RO systems (Pass 1 and Pass 2 blending), and partial concentrate recycle streams.
*   [physics_aging_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/physics_aging_engine.py): Implements the five physics-based fouling sub-models (Colloidal Cake, Biofouling Monod kinetics, Inorganic Scaling CNT, NOM adsorption, and viscoelastic Compaction) integrated over time using a Runge-Kutta 4th Order (RK4) solver.
*   [uf_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/uf_engine.py): Simulates ultrafiltration (UF) pretreatments, backwash losses, and TMP limitations.
*   [conditioning.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/conditioning.py): Models pH adjustments and carbon dioxide (CO2) degassing chemistry.
*   [report_generator.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/report_generator.py): Compiles calculation results and Matplotlib charts into a professional styled Microsoft Word report (`.docx`).

### Frontend UI (`ui_ux_design/`)
*   [index.html](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/ui_ux_design/index.html): The HTML layout containing the project wizard, tab view selectors, water quality table, and calculations overview.
*   [script.js](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/ui_ux_design/script.js): Manages tabs, handles form events, connects to the local FastAPI endpoints, dynamically draws the SVG Process Flow Diagram (PFD), and exports/imports project config files.

---

## 4. Key Calculation Models & Algorithms

### A. Mass Transport Models (calc_engine.py)
*   **Water Flux ($J_w$)**: 
    $$J_w = A \cdot (\Delta P - \Delta \pi)$$
    where $A$ is water permeability (TCF-corrected) and $\Delta \pi$ is osmotic pressure difference calculated dynamically using PHREEQC's water activity.
*   **Solute Flux ($J_s$)**: Solute passage is modeled via Solution-Diffusion ($J_s = B \cdot (C_m - C_p)$) or Spiegler-Kedem equations.
*   **Concentration Polarization ($\beta$)**: Modeled via Schock-Miquel correlations using Sherwood ($Sh$), Reynolds ($Re$), and Schmidt ($Sc$) numbers:
    $$Sh = 0.065 \cdot Re^{0.875} \cdot Sc^{0.25}$$

### B. Fouling & Degradation ODEs (physics_aging_engine.py)
The time-dependent fouling state vector $\mathbf{Y} = [m_c, L_b, \delta_s, q, t_{op}]$ represents:
1.  **Cake Mass ($m_c$)**: Colloidal deposition vs shear-induced removal.
2.  **Biofilm Thickness ($L_b$)**: Monod nutrients-limited growth and shear detachment.
3.  **Scale Thickness ($\delta_s$)**: Classical Nucleation Theory (CNT) kinetics.
4.  **NOM Adsorption ($q$)**: Langmuir intermediate blocking kinetics.
5.  **Membrane Compaction**: Kelvin-Voigt viscoelastic creep model.

Integration is conducted at monthly timesteps ($dt = 730$ hours) using the **RK4 (Runge-Kutta 4th Order)** method.

---

## 5. Specification Document Map
Detailed technical specs are available as Word documents in the root directory:
*   [PHREEQC Integration Spec](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/PHREEQC_Integration_Document.docx): Explains dynamic chemical calculation loops.
*   [Membrane Aging Proposal](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/PACE_MembraneAgingModel_Proposal.docx): Outline of the physics engine specifications.
*   [Two-Pass RO Extension](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/PACE_TwoPass_RO_Extension_Proposal.docx): Outlines Pass 1 / Pass 2 system staging math.
*   [Membrane Recommendation Spec](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/PACE_Membrane_Recommendation_Specification.docx): Selection rules for RO/NF membrane modules.
*   [Process Recommendation Spec](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/PACE_Process_Recommendation_Algorithm_v1.0%20(1).docx): Design rules for pretreatment selection based on source water flags (TSS, TOC, Fe).

---

## 6. How to Run Locally

### Start the Backend Server:
Navigate to the `backend/` folder and start Uvicorn:
```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

### Run the Frontend:
Simply double-click the `ui_ux_design/index.html` file to open it in your browser (Chrome/Edge recommended for native file dialog support).

### Compile into a Desktop Executable (.exe):
You can bundle the Python FastAPI server and the static UI assets into a single desktop application using PyInstaller:
```bash
pyinstaller --onefile --noconsole --add-data "ui_ux_design;ui_ux_design" --add-data "backend/assets;backend/assets" desktop_app.py
```
