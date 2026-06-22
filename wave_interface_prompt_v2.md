# Prompt for Building a DuPont WAVE-Like Interface

This markdown file contains a highly detailed, production-grade prompt designed for AI UI generators (such as Vercel v0, Claude Artifacts, or Bolt.new) to build a complex, data-dense industrial engineering interface inspired by DuPont's WAVE (Water Application Value Engine) software.

---

## The AI Prompt

Copy and paste the text block below directly into your AI UI builder:

```text
Act as an expert frontend engineer and UI/UX designer. Build a web-based interface inspired by industrial engineering software like DuPont's WAVE (Water Application Value Engine). The application is used for designing water treatment systems. 

The UI must be data-dense, professional, clean, and optimized for desktop viewing using Tailwind CSS, Shadcn UI components, and Lucide icons. Use a professional industrial color palette: slate grays, deep blues, and crisp whites.

### 1. Layout Structure
- **Top Navigation Bar:** Project name ("Industrial Desalination Plant X"), Status badge (Draft/Validated), and action buttons (Run Simulation, Export Report, Save).
- **Left Sidebar (Project Wizard):** A multi-step vertical navigation tree showing the project workflow:
  1. Project Info
  2. Water Chemistry (Feed Water)
  3. Process Configuration (The main active view)
  4. System Summary & Costing
- **Main Workspace:** The central area where the system design happens, split into a canvas on top and a configuration panel below.

### 2. Main Workspace Features (Process Configuration View)
- **Visual Process Train (The Flow Diagram):** - A horizontal, sequential pipeline representing the water treatment steps.
  - Render a chain of modular blocks: [Intake/Feed] -> [Ultrafiltration (UF)] -> [Reverse Osmosis (RO)] -> [Ion Exchange (IX)] -> [Product Water].
  - Each block should have an icon, a title, a brief status snippet (e.g., "Flux: 22 gfd", "Recovery: 85%"), and an "X" to delete.
  - Between blocks, show directional arrows. At the end of the train, show a dotted "+" button to "Add Technology".
- **Dynamic Configuration Panel (Below the Train):**
  - A tabbed container that changes based on which block in the process train is clicked.
  - Include mock controls for a "Reverse Osmosis" stage:
    - Left side: Dropdowns for Membrane Type (e.g., FilmTec BW30), Number of Elements, and Vessels per Stage.
    - Right side: Input sliders/fields for Target Recovery (%), Design Temperature, and Feed Flow Rate.

### 3. Water Chemistry Summary Widget
- A collapsible side-drawer or bottom panel showing a dense data table of key water ions tracking the feed vs. product water (e.g., Calcium, Magnesium, Sodium, Chloride, Sulfate, pH, and TDS). 
- Include a simple progress bar or indicator showing "Cation/Anion Balance" (e.g., 99.4% balanced).

### 4. Interactivity & State
- Allow the user to click between the different steps in the left sidebar.
- Allow clicking different blocks in the horizontal process train to highlight them and update the configuration panel context.
- Make the "Run Simulation" button trigger a brief loading state followed by a toast notification saying "Simulation converged successfully in 3 iterations."
```

---

## Strategic Tips for Iterative Refinement

If the initial generation needs adjustment, use these follow-up prompts to guide the AI:

1. **To Increase Enterprise Density:**
   > *"Make the UI more data-dense. Reduce padding, use smaller text (text-sm), and make it look like a highly technical desktop enterprise application rather than a modern consumer SaaS app."*

2. **To Add Technical Dashboards:**
   > *"Add a 'Results & Analytics' tab to the configuration panel that displays a line chart mapping system pressure profiles and membrane scaling limits across all stages."*

3. **To Refine the Chemistry Section:**
   > *"Expand the Water Chemistry view into a full interactive spreadsheet table allowing users to input mg/L concentrations for 15+ individual ions, with automated validation logic for charge balance."*
