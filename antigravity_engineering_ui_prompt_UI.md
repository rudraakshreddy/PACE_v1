# Prompt for Antigravity: Engineering UI Redesign

**Role & Context:** You are an expert UI/UX designer and frontend engineer specializing in complex, data-heavy enterprise and scientific software. Build the "Feed Data" interface for a Membrane Projection Software used by water treatment engineers. 

**Core Aesthetic & Vibe (The "Anti-SaaS" Look):**
Move away from trendy, spacious, dark-mode Web3/startup aesthetics. This needs to look like a robust, high-trust, industrial engineering application (think AutoCAD, Bloomberg Terminal, or a modern SCADA/HMI interface). It must prioritize information density, rapid data entry, and extreme legibility over slick visual flair. 

**Layout & Density:**
* **High Information Density:** Reduce padding and margins significantly. Engineers need to see all parameters on a single screen without scrolling.
* **Grid-Based Structure:** Use a tight, structured, dashboard layout. The interface should feel like a highly modernized, extremely readable Excel spreadsheet merged with a control panel.
* **Compact Panels:** Create distinct, tightly bordered panels for: "Physical Parameters", "Fouling Indicators", "Ionic Data" (a large data-entry table), and a fixed right-hand "Analysis" sidebar.

**Color Palette & Typography:**
* **Utilitarian Colors:** Use a professional, muted color palette. Think slate greys, cool steel blues, and high-contrast whites/blacks. If using dark mode, make it a flat, matte charcoal rather than a glowing neon-blue gradient.
* **Typography:** Use a clean, compact sans-serif (like Inter or Roboto) for labels. **Crucially, use tabular lining or a monospace font for all numeric inputs and outputs** so decimals align perfectly vertically.

**Specific UI Components:**
* **Tabs:** A compact, horizontal tab bar at the top (File, Feed Data, Membrane Recommendation, Scaling Analysis, Report). 
* **Input Fields:** Make input boxes small and dense. Units (e.g., mg/L, m³/h, pH) should be integrated directly into the input field or positioned intimately close to the label. Do not use generic placeholders like "e.g. 50"—use realistic default engineering values.
* **The Ionic Data Table:** This is the core data entry zone. Design a dense, multi-column table for ions (Sodium, Calcium, Magnesium, etc.) with columns for MG/L, MEQ/L, and PPM CACO3.
* **Analysis Sidebar:** A prominent, persistent panel showing real-time calculations (Charge Balance Error as a prominent percentage, Calculated TDS, Est. Conductivity). 

**Behavioral Vibe:** The UI should look like it was built for a power-user who uses the "Tab" key to rapidly fly through 30 data-entry fields in seconds. Make it look sharp, serious, and highly functional.
