# PACE v1 - Industrial Desalination Software

PACE (Process Analysis and Cost Engineering) is a comprehensive web-based engineering tool designed for the modeling, simulation, and economic analysis of industrial desalination plants.

## Features

- **Interactive Process Flow Diagram (PFD):** Visually design and configure process trains including Intake, Ultrafiltration (UF), Reverse Osmosis (RO), and Ion Exchange.
- **Feed Water Chemistry:** Automatically analyze cationic and anionic balances, calculate TDS and pH, and check for scaling potential.
- **Pretreatment Recommendations:** Intelligent suggestions for filtration and chemical dosing based on feed water characteristics (SDI, turbidity, chlorine, etc.).
- **System Sizing & Simulation:** Accurately simulate Ultrafiltration and Reverse Osmosis performance, calculating required modules, vessels, elements, feed pressure, and energy consumption.
- **Performance Decline Projection:** Forecast the decline in membrane performance over time based on fouling and scaling factors.
- **Economic Costing:** High-level economic parameters for OPEX and CAPEX estimations based on energy tariffs, membrane lifespans, and capital costs.

## Architecture

- **Backend:** A robust Python API powered by FastAPI (`backend/server.py`), featuring dedicated physics and simulation engines for UF, RO, and System flow (`uf_engine.py`, `system_engine.py`, etc.).
- **Frontend:** A responsive, modern web interface built with vanilla HTML/JS/CSS (`ui_ux_design/index.html`), utilizing Tailwind CSS for styling and interactive UI components.

## Getting Started

1. Set up a Python virtual environment.
2. Install dependencies (e.g., FastAPI, Uvicorn, standard science libraries).
3. Start the backend server by running `start.bat` or executing `uvicorn backend.server:app --reload`.
4. Open `ui_ux_design/index.html` in a modern web browser to access the interface.
