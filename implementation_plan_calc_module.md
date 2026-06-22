# PACE Calculation Module — Implementation Plan

## Goal

Build an industrial-grade **Calculation Module** that performs rigorous element-by-element membrane simulation for **RO**, **NF**, and **UF** systems (or combinations thereof). The module must use real transport equations (Solution-Diffusion, Spiegler-Kedem, concentration polarization) — no simplified "percentage rejection" shortcuts.

---

## User Review Required

> [!IMPORTANT]
> **Membrane Database Source:** The element-wise simulation requires membrane-specific parameters (water permeability `A`, solute permeability `B`, feed spacer thickness, active area). I plan to hardcode a curated database of ~20 common commercial membranes (e.g., Dow BW30-400, SW30HRLE-440, Hydranautics CPA5-LD, Toray TML20D-400). Should I use a specific manufacturer's membranes, or a generic multi-vendor database?

> [!IMPORTANT]
> **UF Module Selection:** The reference images show an IntegraTec™ SFD-2880 module. Should I model UF generically (user inputs module area, pore size, TMP limits) or include a specific UF module database?

> [!WARNING]
> **Computation Time:** Element-wise iterative calculation with concentration polarization for a 6-element, 3-stage system with 15 ions is computationally intensive. Each "Calculate" click may take 2–5 seconds. This is acceptable for engineering software but slower than the current instant scaling analysis.

## Open Questions

> [!IMPORTANT]
> 1. **Default elements per vessel:** Should we default to 6 or 7 elements per pressure vessel? (Industry uses both; 6 is more common for BWRO, 7 for SWRO.)
> 2. **Which parameters from the reference pics do you want displayed on the Calculation tab vs. only in the Word report?** The UF reference images show ~40+ parameters — displaying all of them on-screen would be cluttered.
> 3. **Are there additional reference pics you mentioned you would upload?** You said "Parameters which are not listed here I will upload the pics." — I should wait for those before finalizing.

---

## Proposed Changes

### Component 1: Membrane Database

#### [NEW] [membrane_database.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/membrane_database.py)

A curated database of commercial RO/NF/UF membrane elements with manufacturer specifications:

**RO/NF Element Properties:**
| Property | Symbol | Unit | Source |
|---|---|---|---|
| Water permeability coefficient | `A` | L/m²·h·bar | Manufacturer datasheet |
| Solute transport parameter (TDS) | `B` | m/s | Derived from test conditions |
| Ion-specific rejection coefficients | `σ_i` | dimensionless | Published literature / fitted |
| Active membrane area | `S_m` | m² | Datasheet |
| Feed spacer thickness | `t_fs` | mil (0.001") | Datasheet |
| Max operating pressure | `P_max` | bar | Datasheet |
| Max feed flow | `Q_f_max` | m³/h | Datasheet |
| Min concentrate flow | `Q_c_min` | m³/h | Datasheet |
| Max recovery per element | `R_max` | % | Datasheet |
| Pressure drop per element | `ΔP_elem` | bar | Datasheet (typ. 0.2–0.7) |
| Element length and diameter | `L`, `D` | mm | Datasheet |

**Ion-Specific Rejection Coefficients (σ) for common RO membranes:**
| Ion | Typical BW Membrane σ | Typical SW Membrane σ |
|---|---|---|
| Ca²⁺ | 0.995 | 0.998 |
| Mg²⁺ | 0.995 | 0.998 |
| Na⁺ | 0.980 | 0.995 |
| K⁺ | 0.975 | 0.993 |
| Ba²⁺ | 0.997 | 0.999 |
| Sr²⁺ | 0.996 | 0.998 |
| Cl⁻ | 0.980 | 0.995 |
| SO₄²⁻ | 0.998 | 0.999 |
| HCO₃⁻ | 0.975 | 0.993 |
| NO₃⁻ | 0.930 | 0.970 |
| F⁻ | 0.960 | 0.985 |
| SiO₂ | 0.985 | 0.995 |
| B | 0.700 | 0.910 |
| NH₄⁺ | 0.850 | 0.930 |
| PO₄³⁻ | 0.995 | 0.999 |

**UF Module Properties:**
| Property | Unit |
|---|---|
| Module type / model name | — |
| Membrane area per module | m² |
| Max filtration flux | LMH |
| Clean membrane TMP at design temp | bar |
| Fouled membrane TMP limit | bar |
| Backwash flux | LMH |
| Backwash duration | min |
| Filtration cycle duration | min |
| CEB interval | hours |
| CIP interval | days |
| Forward flush flow (min/max) | m³/h/module |

---

### Component 2: RO/NF Calculation Engine

#### [NEW] [calc_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/calc_engine.py)

The core calculation engine. ~800–1200 lines of Python.

**Architecture:**

```
CalcEngine
├── SystemConfig (stages, PVs, elements, membrane model)
├── FeedWater (all ions, pH, temp, TDS)
├── DesignParams (target recovery, target permeate flow)
│
├── Phase A: System Sizing
│   ├── Calculate total membrane area needed
│   ├── Determine number of elements
│   ├── Determine staging array (e.g., 4:2:1)
│   └── Verify hydraulic constraints
│
├── Phase B: Element-by-Element Simulation
│   ├── For each stage:
│   │   ├── For each element in the vessel:
│   │   │   ├── Calculate local feed concentration (with CF)
│   │   │   ├── Calculate concentration polarization (β)
│   │   │   ├── Calculate membrane surface concentration
│   │   │   ├── Calculate osmotic pressure (OLI or van't Hoff)
│   │   │   ├── Calculate net driving pressure (NDP)
│   │   │   ├── Calculate water flux Jw = A × NDP
│   │   │   ├── Calculate permeate flow for this element
│   │   │   ├── Calculate ion-specific passage (Spiegler-Kedem)
│   │   │   ├── Calculate permeate concentration per ion
│   │   │   ├── Calculate element recovery
│   │   │   ├── Update feed for next element (mass balance)
│   │   │   └── Calculate pressure drop
│   │   └── Stage output: reject concentration, reject flow, stage permeate
│   └── Combine all stage permeates → system permeate
│
├── Phase C: System Performance Summary
│   ├── Total recovery
│   ├── Average flux (GFD / LMH)
│   ├── Specific energy consumption (kWh/m³)
│   ├── System permeate quality (TDS, individual ions)
│   ├── Concentrate quality
│   └── Feed pump pressure required
│
└── Phase D: Design Warnings
    ├── Max element recovery exceeded
    ├── Max element permeate flow exceeded
    ├── Min concentrate flow per element violated
    ├── Max feed flow per element exceeded
    ├── Beta (CP) factor > 1.20
    ├── Flux exceeds recommended design flux
    └── Pressure drop per stage exceeds limits
```

**Key Equations (no simplifications):**

1. **Osmotic Pressure** (Modified van't Hoff with activity correction):
$$\pi = iMRT \times \phi$$
Where $\phi$ is the osmotic coefficient (already implemented in our codebase).

2. **Water Flux** (Solution-Diffusion):
$$J_w = A \times (ΔP - Δ\pi) \times TCF$$
Where $TCF$ is the temperature correction factor:
$$TCF = \exp\left[2640 \times \left(\frac{1}{298} - \frac{1}{273 + T}\right)\right]$$

3. **Concentration Polarization** (Film Theory):
$$\beta = \frac{C_m}{C_b} = \exp\left(\frac{J_w}{k}\right)$$
Where $k$ is the mass transfer coefficient from Sherwood correlation:
$$Sh = 0.04 \times Re^{0.75} \times Sc^{0.33}$$

4. **Ion-Specific Rejection** (Spiegler-Kedem):
$$R_i = 1 - \frac{F_i}{1 - (1 - F_i) \times \exp\left(-\frac{J_w \times (1 - \sigma_i)}{P_{s,i}}\right)}$$
Where $F_i = \frac{1 - \sigma_i}{1 - \sigma_i \times (1 - J_w / P_{s,i})}$

5. **Pressure Drop per Element** (Schock & Miquel correlation):
$$\Delta P = \lambda \times \frac{L}{d_h} \times \frac{\rho \times v^2}{2}$$
Where $\lambda = 6.23 \times Re^{-0.3}$ for typical feed spacers.

6. **Specific Energy Consumption**:
$$SEC = \frac{P_{feed} \times Q_{feed}}{Q_{permeate} \times 36}$$

---

### Component 3: UF Calculation Engine

#### [NEW] [uf_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/uf_engine.py)

Handles UF system sizing and hydraulic calculations. ~400 lines.

**Calculations:**

1. **Number of Modules:**
$$N_{modules} = \frac{Q_{net\_product}}{J_{design} \times A_{module}}$$

2. **Gross Feed Flow** (accounting for backwash and waste):
$$Q_{gross} = \frac{Q_{net}}{R_{UF} / 100}$$

3. **TMP at Design Temperature:**
$$TMP = \frac{J}{L_p(T)} = \frac{J}{L_{p,20} \times \mu_{20} / \mu_T}$$
Where viscosity correction:
$$\mu_T = 1.0 \times 10^{-3} \times \exp\left(\frac{1808}{T+273} - 6.354\right)$$

4. **Backwash Volume per Cycle:**
$$V_{BW} = J_{BW} \times A_{module} \times N_{modules} \times t_{BW} / 1000$$

5. **CEB Chemical Dosing:**
$$Q_{chem} = \frac{Q_{BW} \times C_{target}}{C_{stock} \times 1000}$$

6. **Net Recovery:**
$$R_{net} = \frac{Q_{net}}{Q_{gross}} \times 100$$

7. **UF Water Quality Output:**
- Temperature: Pass-through
- Turbidity: ≤ 0.1 NTU (guaranteed by UF pore size)
- TSS: ~0 (complete removal of suspended solids)
- TDS: Pass-through (UF does not reject dissolved solids)
- pH: Pass-through

8. **Design Warnings:**
| Warning | Condition |
|---|---|
| Filtration Flux > Max | J_design > J_max (manufacturer limit) |
| Forward Flush Flow < Min | Q_ff < Q_ff_min per module |
| Clean TMP @ TMin > Max | TMP(T_min) > TMP_clean_max |
| Clean TMP @ TDesign > Max | TMP(T_design) > TMP_clean_max |
| Fouled TMP @ TMin > Max | TMP_fouled(T_min) > TMP_fouled_max |
| Fouled TMP @ TDesign > Max | TMP_fouled(T_design) > TMP_fouled_max |

---

### Component 4: Multi-Technology System Integration

#### [NEW] [system_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/system_engine.py)

Orchestrates calculations for combined systems (UF→RO, UF→NF, UF→RO→2nd Pass RO, etc.):

```
SystemEngine
├── parse_system_config() → Determine technology train
├── run_uf()             → UF sizing & hydraulics (if applicable)
├── run_ro_pass1()       → First pass RO element-wise simulation
├── run_ro_pass2()       → Second pass RO (if 2-pass required)
├── run_nf()             → NF element-wise (if NF selected)
├── combine_results()    → Merge all subsystem outputs
└── generate_warnings()  → Aggregate all design warnings
```

**Flow Logic:**
```
IF system includes UF:
    UF output (Q, TDS, ions) → becomes RO/NF feed input

IF system is RO:
    Run element-wise RO simulation (1st pass)
    IF 2-pass required:
        1st pass permeate → 2nd pass feed
        Run element-wise RO simulation (2nd pass)
        Final permeate = 2nd pass permeate

IF system is NF:
    Run element-wise NF simulation (same engine, different σ values)

Combine all streams → final system output
```

---

### Component 5: API Endpoints

#### [MODIFY] [server.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/server.py)

Add new endpoints:

```python
@app.post("/api/calculate-system")
def calculate_system(data: SystemCalcInput):
    """Main calculation endpoint. Returns element-wise results,
    system summary, and design warnings."""

@app.get("/api/membranes")
def list_membranes():
    """Returns available membrane models for dropdown selection."""

@app.get("/api/membranes/{model_id}")
def get_membrane(model_id: str):
    """Returns detailed specs for a specific membrane."""
```

---

### Component 6: Frontend — Calculation Tab UI

#### [MODIFY] [index.html](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/ui_ux_design/index.html)

The Calculation tab will have the following sections:

**Left Panel (Inputs):**
1. **System Configuration**
   - Technology train selector (UF→RO, UF→NF, RO only, NF only, UF→2P-RO)
   - Target permeate flow (m³/h)
   - Target recovery (%)

2. **Membrane Selection**
   - RO/NF membrane model dropdown (from database)
   - UF module model dropdown (if UF selected)

3. **System Array**
   - Number of stages
   - Pressure vessels per stage (auto-calculated or manual)
   - Elements per vessel (default 6)

4. **Operating Conditions**
   - Feed pressure (bar)
   - Temperature (°C) — pulled from Feed Data tab
   - pH — pulled from Feed Data tab

**Right Panel (Results) — displayed after calculation:**

1. **System Summary Card**
   - Total recovery (%)
   - Permeate flow (m³/h)
   - Concentrate flow (m³/h)
   - Feed pressure (bar)
   - Average flux (LMH)
   - Specific energy (kWh/m³)
   - Permeate TDS (mg/L)
   - Concentrate TDS (mg/L)

2. **Element-wise Performance Table** (scrollable)
   | Element | Feed Flow | Perm Flow | Conc Flow | Feed TDS | Perm TDS | Recovery | Flux | ΔP | β |
   |---|---|---|---|---|---|---|---|---|---|

3. **Element-wise Ion Concentration Table** (scrollable)
   | Ion | Feed (mg/L) | Permeate (mg/L) | Reject (mg/L) | Rejection (%) |
   |---|---|---|---|---|

4. **UF System Overview** (if UF is in the train)
   - Module type, count, flux, TMP, recovery
   - Operating conditions (backwash, CEB, CIP)
   - Water quality (feed vs product)

5. **Design Warnings Panel**
   - Table with Warning, Limit, Estimate, Status (Pass/Fail)

#### [MODIFY] [script.js](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/ui_ux_design/script.js)

- Add `calculateSystem()` function that calls `/api/calculate-system`
- Populate all result tables dynamically
- Pull feed water data from Feed Data tab inputs

#### [MODIFY] [styles.css](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/ui_ux_design/styles.css)

- Styles for element-wise tables (scrollable, striped rows)
- Design warning row highlighting (red for fail, green for pass)

---

### Component 7: Word Document Report Generator

#### [NEW] [report_generator.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/report_generator.py)

Generates a comprehensive `.docx` report containing:

1. **System Configuration Summary** — technology train, membrane model, staging
2. **Feed Water Analysis** — full ionic breakdown
3. **UF Summary Report** (if applicable) — matching the reference image layout
   - System overview table
   - Operating conditions table
   - Water quality table
   - Design warnings table
4. **RO/NF System Performance** — system-level summary
5. **Element-wise Performance Tables** — flow, pressure, flux per element
6. **Ion Rejection Report** — per-ion feed/permeate/reject concentrations
7. **Design Warnings** — all warnings with limit vs estimate
8. **Scaling Analysis** — SI values at concentrate conditions

---

## Verification Plan

### Automated Tests
```bash
# Unit test for element-wise simulation accuracy
python -m pytest backend/tests/test_calc_engine.py -v

# Test against known ROSA/WAVE projections for validation
python backend/tests/test_validation.py
```

### Manual Verification
1. **Cross-validate** element-wise results against DuPont WAVE or Hydranautics IMS Design for a standard 2-stage BWRO system with known feed water
2. **Verify UF calculations** match the reference images (IntegraTec SFD-2880 example)
3. **UI visual check** — ensure all tables render correctly in the dark theme
4. **Word report** — open generated .docx and verify formatting matches professional standards
