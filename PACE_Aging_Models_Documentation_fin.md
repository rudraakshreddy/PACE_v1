# Physics-Based Aging Models Documentation

The `physics_aging_engine.py` implements a strictly mechanistic Ordinary Differential Equation (ODE) framework. It discretizes the array into spatial segments and uses a 4th-order Runge-Kutta (RK4) solver to integrate the ODEs over time.

Below are the exact mathematical models and logic implemented in the backend, utilizing LaTeX math notation for the governing equations.

> **Revision note:** Section 6 (CIP Kinetics) rewritten from a single shared dissolution constant to two-step, foulant-specific constants plus a foulant-maturation penalty \(\eta_{age}\). Section 7 (new) ties default rate constants to the Permionics element datasheet instead of generic literature defaults, and adds a trigger-based CIP forecast output. "Translating to ASTM Metrics" expanded to explicitly define \(B_{REL}\), previously undocumented, and to fix its derivation order relative to CIP events. Motivated by a Year 0–5 stress test at a deliberately long 48-month CIP interval, which surfaced an implausibly small post-CIP recovery and a \(B_{REL}\) that never responded to CIP at all.
>
> **Revision note (2):** Section 7 rewritten again — the first version embedded the HPA RO-8040-LF's specific published numbers directly into the calibration logic, which only calibrates correctly for that one element. It is now schema-driven: a generic Membrane Datasheet Schema plus a three-tier fallback hierarchy, so any element from any manufacturer calibrates through the same pipeline. The HPA RO-8040-LF's numbers now appear only in a clearly-labeled, non-normative worked example at the end of the section, purely to demonstrate the schema against real data.
>
> **Revision note (3):** Corrected the \(B_{REL}\) misdiagnosis from Revision 1 — it is not a biofilm-burden index, it is the chlorine-driven oxidative degradation scalar (`kB_eff`), confirmed against `physics_aging_engine.py` ~L644. Added Section 6 (new): Sub-model VI, documenting this mechanism, its likely role as a salt-permeability-coefficient multiplier rather than a resistance term, and two open questions — the pending rename to \(B_{IRR}\), and whether its scope should stay chlorine-specific or generalize. Old Sections 6 and 7 renumbered to 7 and 8 accordingly, with a new calibration subsection (8.7) tying `kB_eff` to the same schema as the rest of Section 8. "Translating to ASTM Metrics" corrected to reference the real mechanism instead of the wrong guess.

## 1. Sub-model I: Cake Filtration (Colloidal & Particulate)
**Mechanism:** Particulate deposition driven by convective flux vs. shear-induced detachment.
**ODE Formulation:**
\[\frac{dm_c}{dt} = K_d \cdot J_w \cdot C_b - K_{rem} \cdot \tau_w \cdot m_c\]
*   \(m_c\): Cake mass per unit area (\(kg/m^2\))
*   \(K_d, K_{rem}\): Deposition and removal rate constants
*   \(J_w\): Local water flux
*   \(\tau_w\): Wall shear stress (driven by crossflow)

**Resistance (Compressible Cake):**
\[R_c = \alpha_0 \left( \frac{TMP}{TMP_{ref}} \right)^{s_c} \cdot m_c\]

## 2. Sub-model II: Biofouling (Biofilm Growth)
**Mechanism:** Bacteria attach and multiply, creating an EPS matrix. Modeled via Monod kinetics coupled with Logistic Growth to enforce a physical carrying capacity limit (preventing unbounded exponential explosions).
**ODE Formulation:**
\[\frac{dL_b}{dt} = \mu_{eff} \cdot L_b \cdot \left(1 - \frac{L_b}{L_{b,max}}\right) + J_{b,seed} - b_d \cdot L_b\]
Where the effective growth rate \(\mu_{eff}\) follows Monod kinetics based on TOC (nutrient) concentration:
\[\mu_{eff} = \mu_{max} \cdot \left( \frac{C_{toc}}{K_s + C_{toc}} \right) \cdot \exp\left( \frac{E_a}{R} \left( \frac{1}{T_{ref}} - \frac{1}{T} \right) \right)\]

**Resistance (Kozeny-Carman for fibrous biofilm):**
\[R_b = \frac{180 \cdot (1 - \epsilon_{bf})^2 \cdot \tau_{bf} \cdot L_b}{d_p^2 \cdot \epsilon_{bf}^3}\]

## 3. Sub-model III: Mineral Scaling (Classical Nucleation Theory)
**Mechanism:** Salts exceed solubility limits at the membrane wall. Scaling only initiates after an induction time \(t_{ind}\) (which is significantly extended by antiscalant).
**ODE Formulation:**
Once \(t > t_{ind}\), parabolic crystal growth applies based on the true supersaturation ratio \(S\):
\[S = 10^{SI_{wall}}\]
\[\frac{d(\delta_s)}{dt} = k_g \cdot \frac{(S - 1)^{n_s}}{\rho_{scale}}\]
*   \(\delta_s\): Scale thickness (\(m\))
*   \(SI_{wall}\): Saturation Index at the wall (including Concentration Polarization)

**Resistance:**
\[R_s = \alpha_s \cdot \rho_{scale} \cdot \delta_s\]

## 4. Sub-model IV: Organic Fouling (NOM Adsorption)
**Mechanism:** Natural Organic Matter (NOM) adsorbs onto the membrane surface via a Langmuir isotherm.
**ODE Formulation:**
\[\frac{dq}{dt} = k_{ads} \cdot (q_{eq} - q) \cdot f_{shear}\]
Where the equilibrium adsorption \(q_{eq}\) is:
\[q_{eq} = q_{max} \cdot \frac{K_L \cdot C_{nom,w}}{1 + K_L \cdot C_{nom,w}}\]

**Resistance:**
\[R_n = r_{NOM} \cdot q\]

## 5. Sub-model V: Membrane Compaction
**Mechanism:** The polymer structure visco-elastically creeps under the applied trans-membrane pressure (TMP), permanently losing permeability.
**Kelvin-Voigt Creep Formula (Incremental):**
\[\epsilon_{comp}(t+\Delta t) = \epsilon_{comp}(t) + (\epsilon_{\infty} - \epsilon_{comp}(t)) \cdot \left(1 - \exp\left(-\frac{\Delta t}{\tau_c}\right)\right)\]
Where the asymptotic maximum compaction strain is driven by stress:
\[\epsilon_{\infty} = \frac{TMP \cdot f_{stress}}{E_m}\]

## 6. Sub-model VI: Chlorine-Induced Oxidative Degradation

**Mechanism:** Free chlorine and other oxidants attack the polyamide barrier layer directly, degrading its selectivity. Unlike Sub-models I–V, this is not a deposit sitting on the membrane surface — it is chemical damage to the membrane itself, which is why no CIP step touches it regardless of chemistry or duration. Confirmed in the current implementation: the driving scalar (`kB_eff`, `physics_aging_engine.py` ~L644) is not reduced by `_apply_cip()`.

**Currently named `B_REL` in the codebase — pending rename to `B_IRR`** (open item in the implementation plan). "REL" implies relative-to-baseline-right-now, which misdescribes a quantity that is designed to only ever increase.

**ODE formulation:** not yet transcribed into this spec. The exact functional form of `kB_eff` — whether driven by instantaneous free-chlorine concentration, cumulative CT-dose exposure, temperature, or some combination — should be pulled directly from `physics_aging_engine.py` ~L644 rather than assumed here.

**Likely transport-layer role (hypothesis — confirm against code, not yet verified):** in standard solution-diffusion RO transport notation, \(A\) is the water permeability coefficient and \(B\) is the salt permeability coefficient (\(J_s = B \cdot \Delta C\)). The naming and the Year 0–5 stress-test numbers both point toward this scalar acting as a multiplier on the membrane's intrinsic salt permeability coefficient, not as a term inside \(R_{total}\):
\[B_{eff}(t) = B_0 \cdot B_{IRR}(t)\]
At Year 4 in that test, \(B_{REL}\) (1.062) tracked NSP (1.0579) far more closely than it tracked FRI (0.273) or anything resistance-derived — consistent with this scalar driving salt passage directly rather than hydraulic resistance. If confirmed, this also explains the CIP behavior structurally, not just as an exception: it is not fouling sitting on top of the membrane, it is damage to the selective layer itself, so it was never a candidate for the reducible-state list in Section 7 to begin with.

**Open design question — unresolved, do not default silently:** should this stay scoped to chlorine/oxidative attack specifically, or become a general irreversible-damage bucket that later also absorbs compaction (\(\epsilon_{comp}\)) or scale that has aged past \(\eta_{age}\)'s recoverable range (Section 7)? These are mechanistically distinct — chemical attack on the barrier layer, mechanical creep, and mineralogical hardening are three different physical processes — and likely deserve separate, clearly-named scalars rather than one combined "irreversible" number. This is a real decision, not something to resolve by convention.

## 7. Chemical Cleaning (CIP) Kinetics — Revised

**Mechanism:** A real CIP is a sequential two-step protocol, not one generic wash — a high-pH (alkaline) circulation targets biological and organic foulants, and a low-pH (acid) circulation targets mineral scale and inorganic cake. Sharing a single dissolution constant across all four reversible states under-recovers whichever foulant doesn't match that step's chemistry, which is almost certainly why the previous version showed a muted post-CIP jump regardless of how long fouling had been left to build up.

**Per-mechanism, per-step dissolution:**
For each reversible state \(X \in \{m_c, L_b, \delta_s, q\}\) and each CIP step \(j \in \{alkaline, acid\}\):
\[X_{post-step_j} = X_{pre-step_j} \cdot \exp\left(-k_{dis,X,j}(T) \cdot \eta_{age}(t_{elapsed,X}) \cdot t_{duration,j}\right)\]

Recommended default step affinity — set the off-chemistry constant near zero rather than sharing one value across both steps:

| State | Alkaline step | Acid step |
|---|---|---|
| \(L_b\) (biofilm / EPS) | primary | negligible |
| \(q\) (NOM) | primary | secondary |
| \(\delta_s\) (mineral scale) | negligible | primary |
| \(m_c\) (cake) | secondary | secondary (composition-dependent) |

**Foulant-maturation penalty (new):**
\[\eta_{age}(t_{elapsed}) = \eta_{min} + (1-\eta_{min}) \cdot \exp\left(-\frac{t_{elapsed}}{\tau_{age}}\right)\]
\(t_{elapsed}\) is measured from when a given foulant layer began accumulating, not from the last CIP check. This captures cake consolidation, EPS cross-linking, and Ostwald ripening of scale into larger, less-soluble crystals — standard reasons a membrane fouled for years cleans back less completely than one fouled for months, even at identical chemistry and duration. Suggested uncalibrated starting points: \(\eta_{min} \approx 0.5\text{–}0.7\), \(\tau_{age} \approx 12\text{–}18\) months. This term is what should produce a muted recovery at a long, neglected interval — for the right physical reason, rather than as a side effect of an undertuned or shared \(k_{dis}\).

**Compaction remains permanently excluded.** \(\epsilon_{comp}\) is never touched by CIP dissolution logic, in this or any future version — stated explicitly here so it can't be folded into the reducible-state list by a later edit.

**Validation target:** a full-duration two-step CIP triggered at a realistic interval (10–15% NPF decline, before \(\eta_{age}\) has decayed much) should recover \(m_c, L_b, \delta_s, q\) to roughly 90–98% of their pre-fouling values. A properly-scheduled CIP recovering less than ~80% of the reversible fraction in test cases should be treated as a sign to re-check \(k_{dis,X,j}\) and \(t_{duration,j}\), not accepted as a modeling curiosity.

## 8. Calibration Against the Manufacturer Design Envelope

Rate constants in Sections 1–5 must never be written as literal numbers for one element. Every membrane in PACE's catalog — any manufacturer, RO/NF/UF, LF or standard — calibrates through the same generic pipeline below, driven entirely by whatever that element's own datasheet publishes, with a defined fallback when it doesn't publish something.

**8.1 Membrane Datasheet Schema**
Every element is normalized into the same record shape on import, regardless of manufacturer:
*   `model_id`, `manufacturer`, `membrane_class` (e.g. BWRO, SWRO, NF, UF)
*   `active_area`, `nominal_flow`, `nominal_rejection`
*   `design_flux_table`: list of (water source, SDI range, flux range) as published
*   `saturation_limits`: dict of published index/species → ceiling — keys vary by manufacturer, see 8.4
*   `operating_limits`: max pressure, max temperature, operating pH range, CIP pH range, max chlorine, max SDI
*   `surface_class`: hydrophilic (bool), fouling-resistant claim (bool), material family

All fields are optional. No field here is specific to any one SKU — this is the shape every catalog entry is normalized into, and 8.3–8.6 below are written purely in terms of it.

**8.2 Fallback hierarchy**
For any calibration input, resolve in this order and record which tier was used:
1.  **SKU-specific** — the value as published on the selected element's own datasheet.
2.  **Class default** — typical value across other elements sharing the same `membrane_class` and `surface_class.material` in the catalog.
3.  **Literature default** — a generic industry-typical value, used only when neither of the above exists.

Surface the tier alongside the result (e.g. "using class default — element does not publish SrSO₄ limit") so the engineer can see when a number is vendor-verified versus assumed, rather than presenting a fallback as if it were a spec.

**8.3 Deposition rate vs. design flux category (Sub-model I)**
Where `design_flux_table` is published, compute how far the configured system flux sits above the ceiling for the applicable water-source/SDI bracket, and scale \(K_d\) by that ratio — a system pushed above its own element's recommended ceiling for the assumed feed quality should carry a higher \(K_d\) than one operated within it. Where `design_flux_table` is absent for a given element, fall back to a generic BWRO/SWRO/NF flux-vs-SDI guideline table (tier 3), never to one manufacturer's specific numbers.

**8.4 Scaling induction time vs. published saturation limits (Sub-model III)**
Iterate over whatever keys exist in `saturation_limits` for the selected element — manufacturers differ in which indices and species they publish (LSI and SDSI are close to universal; specific-salt ceilings such as CaSO₄, SrSO₄, BaSO₄, SiO₂, or CaCO₃/calcium phosphate vary by product line). For each published key, compute the concentrate-side value and compare it to its ceiling. \(t_{ind} \to \infty\) while every published limit is satisfied; \(t_{ind}\) collapses once any one is exceeded. The check must iterate the dict that exists for the selected element — never assume a fixed species list.

**8.5 Fouling-resistance class multiplier (Sub-models I & II)**
Apply a multiplier \(f_{class} \le 1\) to \(K_d\) and \(\mu_{max}\) whenever `surface_class.fouling_resistant_claim` is true, regardless of manufacturer or product name — this covers any vendor's low-fouling or hydrophilic-surface line, not one company's naming convention. Treat \(f_{class}\) as a tier-3 calibration slot (suggested uncalibrated starting range 0.6–0.8) until field or pilot CIP data justifies a tighter, class- or SKU-specific value.

**8.6 Compaction stiffness estimate (Sub-model V)**
Where `operating_limits.max_pressure` and `surface_class.material` are published, use them as a structural-robustness proxy for \(E_m\) — higher-rated elements within the same material family generally compact less under equivalent TMP. Fall back to a generic literature \(E_m\) by material family (e.g. PA thin-film composite vs. cellulose acetate vs. PVDF UF) when SKU-specific data isn't available.

**8.7 Chlorine-degradation rate vs. published tolerance (Sub-model VI)**
Where `operating_limits.max_chlorine` is published, use exposure above that ceiling (concentration × time, i.e. CT-dose) to drive `kB_eff` — an element rated for stricter chlorine tolerance should degrade slower under identical exposure than one rated more permissively. Where the element doesn't publish a chlorine tolerance, fall back to a generic PA thin-film-composite tolerance (tier 3) rather than one manufacturer's number. This keeps Sub-model VI on the same schema as 8.3–8.6 instead of reintroducing a standalone hardcoded constant.

**8.8 Output: trigger-based CIP forecast**
Independent of whatever `CIP Interval (months)` the user configures, `system_engine` should project the uncontrolled trajectory forward and report the month at which NPF first drops 10%, NSP first rises 10%, or normalized ΔP first rises 15% — whichever comes first — as a `Recommended_Next_CIP` output field. This one is already fully generic: it depends only on the projected trajectory, not on any membrane-specific constant.

---

**Appendix A (non-normative): worked example.** Shown only to demonstrate 8.1 against a real datasheet — this table must never be read by `physics_aging_engine.py` directly.

| Schema field | HPA RO-8040-LF value |
|---|---|
| `membrane_class` | BWRO |
| `design_flux_table` (Surface Water, SDI<5) | 12–16 gfd |
| `saturation_limits.LSI` | < +1.5 |
| `saturation_limits.CaSO4_pct` | 230% |
| `surface_class.fouling_resistant_claim` | true |
| `operating_limits.max_pressure` | 600 psi (4.14 MPa) |

Swap in any other manufacturer's element and 8.1–8.7 resolve the same way without touching the engine.

## Translating to ASTM Metrics
The discrete resistances are summed: 
\[R_{total} = R_m + R_c + R_b + R_s + R_n + R_{comp}\]
Sub-model VI (Section 6) is deliberately absent from this sum — it degrades the salt permeability coefficient directly rather than adding hydraulic resistance, so it belongs on the salt-passage side of the transport model, not here. The `system_engine` then iteratively solves for the `P_feed` required to achieve the target flux against this dynamically shifting \(R_{total}\). From there, standard ASTM D4516-19a metrics (NPF, NSP, FRI) are back-calculated for the UI.

**\(B_{IRR}\) (formerly \(B_{REL}\)) — corrected definition.** An earlier revision of this document guessed \(B_{REL}\) was a biofilm-burden index; that guess was wrong. It is the chlorine-driven oxidative degradation scalar defined in Section 6 (Sub-model VI), currently implemented as `kB_eff` and not reset by `_apply_cip()`. That non-reset behavior is correct, not a bug — barrier-layer oxidative damage is genuinely irreversible, unlike the four reversible states in Section 7 (CIP Kinetics). See Section 6 for the mechanism, the pending rename to \(B_{IRR}\), and the open question on whether its scope should stay chlorine-specific or expand into a general irreversible-damage bucket.

The one rule that still holds everywhere in `system_engine`, unchanged from before: **NPF, NSP, FRI, and any CIP-affected state are computed from the state vector *after* any same-timestep CIP reduction, never before.** \(B_{IRR}\) is exempt from this by design — it is supposed to carry through CIP untouched — which is exactly why it needs its own name rather than sharing "REL" with metrics that are supposed to reset.
