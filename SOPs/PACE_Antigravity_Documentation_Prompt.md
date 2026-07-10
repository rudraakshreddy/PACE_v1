# PACE — Complete Technical Documentation Generation

## 1\. Your role

You are producing the authoritative internal technical documentation for PACE (Permionics Advanced Calculation Engine) — the proprietary RO/NF/UF membrane system design and simulation platform. This document is going to Permionics management as the formal record of how the software works, and will also serve as the reference engineers use to maintain and extend the codebase going forward. Write accordingly: precise, complete, no marketing language, no hand-waving, no summarizing-away of detail for the sake of brevity.

## 2\. Objective

Produce complete markdown documentation covering **every module currently implemented in the PACE codebase** — not a representative subset. For each module: what it does, every equation it uses, why that equation and not an alternative, where that equation originates, every algorithm and logic structure it uses, why that approach and not an alternative, and exactly where in the code each of these lives.

## 3\. Step 0 — Discover the actual scope (mandatory first step)

Before writing anything, scan the full repository structure and produce a complete inventory of every module, sub-module, and calculation engine that currently exists in the code.

**The codebase is the source of truth, not the checklist below.** The checklist exists only to sanity-check completeness. If the code contains something not listed here, document it anyway. If something listed here no longer exists in the code (superseded, deprecated, merged into another module), say so explicitly rather than silently omitting it.

Reference checklist (floor, not ceiling):

* pH / speciation calculation (concentrate \& permeate, PHREEQC-integrated)
* Membrane fouling / multi-year aging engine — five mechanisms: colloidal cake, biofouling, scaling, NOM adsorption, compaction (resistance-in-series framework)
* Nanofiltration (NF) module — ion-specific rejection, multi-phase calculation sequence
* Auto-balance / charge-balance correction logic
* Process recommendation engine — PHREEQC-based scaling decision logic
* Two-pass RO extension
* Feed water input validation (charge balance error, ionic strength, pretreatment triggers)
* Membrane scoring / recommendation engine
* Scaling analysis (Ksp, activity coefficient models)
* Concentration polarization (CP) calculation, including the Pass 2 correction
* Energy \& economic calculation (CAPEX/OPEX)
* Long-term performance decline projection (regression-based)
* Report/output generation layer (document I/O and structure only — no new physics, so no equation-level treatment needed here)

## 4\. Required contents — for every module

Do not skip or lightly treat a module because it seems minor. Auto-balance logic and the CP bug fix get the same rigor as the aging engine.

### 4.1 Purpose \& scope

One paragraph: what engineering problem this module solves, and where it sits in the overall PACE pipeline — what feeds into it, what consumes its output.

### 4.2 Inputs \& outputs

A table: every input parameter (name, units, valid range, upstream source) and every output (name, units, downstream consumer).

### 4.3 Every equation

For each equation used in this module:

* The equation itself, in full, with every symbol defined. Reproduce it exactly as implemented — do not loosely paraphrase a named equation (Davies equation, Spiegler-Kedem-Katchalsky, etc.); the exact form matters.
* **Why this equation.** The physical/engineering reason this formulation was chosen over alternatives. Example of the expected depth: "The Davies equation is used for activity-coefficient correction rather than Debye-Hückel because RO concentrate streams routinely exceed 0.1 M ionic strength, which is outside Debye-Hückel's valid range."
* **Source.** See Section 5.
* **Code location.** File path and function/class name where this equation is implemented. Non-negotiable — this is what makes the document auditable against the running code.

### 4.4 Every algorithm / logic structure

Anything beyond a single equation: classification logic, branching/decision trees, numerical integration schemes, convergence or iteration loops, error and edge-case handling.

* Plain-language explanation of what it does.
* Why this approach was chosen over alternatives. Example: "RK4 integration with monthly sub-stepping replaces simple Euler integration because the fouling ODEs are numerically stiff near end-of-life conditions; Euler integration was observed to overshoot on these terms, and RK4 provides 4th-order accuracy — standard practice for stiff first-order ODE systems in engineering simulation."
* Known limitations or assumptions.
* Code location.

### 4.5 Justification for every user-facing number

For anything PACE reports to the end user — SI, LSI, flux decline %, projected membrane life, recommended membrane, CAPEX/OPEX, pH, recovery, dominant fouling mechanism, etc. — trace the full calculation chain and explain why each intermediate step is necessary. Not just the formula: why the resulting number means what it claims to mean.

### 4.6 Change / validation history

Document two related things here. Both are real institutional knowledge; neither should be omitted as incidental.

* **Known issues that were corrected** — numerical instability, incorrect partitioning logic, a misclassification bug: what the issue was, why it occurred, how the current implementation avoids it. Anything matching the following pattern must appear if present in the code: any Euler-to-analytical-integration change, any resistance-partitioning correction (e.g., separating fouling resistance from total resistance), any concentration-polarization / near-zero-osmotic-pressure correction.
* **Divergence from the original internal spec** (see Section 5, Step B) — anywhere the current implementation no longer matches what its spec document describes: state what the spec specified, what was actually built instead, and why if that's inferable. This applies even where the change wasn't a "bug fix" in the traditional sense — a deliberate redesign or refinement is just as important to record as a correction.

## 5\. Sourcing \& citation rules — hard constraint, read carefully

**Critical context: the internal spec documents describe an earlier design. The actual implementation has diverged from them in a number of modules — in some cases significantly.** Treat every spec document as a *reference to check against*, never as a *source to cite from directly*. A spec's citation is only valid for what's currently implemented if you've confirmed the equation itself hasn't changed since the spec was written. Skipping that confirmation is how a superseded equation ends up in a management document carrying a citation that makes it look current and correct.

Work through sourcing in this order for every equation and algorithm:

**Step A — Extract from code first, always.** Document exactly what the current implementation does. This is the only thing that gets documented as "how this module works" — never what a spec says it should do.

**Step B — Cross-check against the internal specs (comparison, not citation).** If a corresponding equation or algorithm exists in one of the spec documents below, compare it against what you found in Step A:

* **Exact match** (same equation, same parameters, same logic): the spec's original citation may be inherited. Mark it `\[VERIFIED — Internal Spec: <document name>, confirmed match with current implementation]`.
* **Divergence found** (modified, extended, replaced): the spec's citation does **not** carry over — it justified the old equation, not the one actually running now. Document the divergence explicitly in that module's change history (Section 4.6): what the spec specified, what the code actually does now, and why if that's inferable from comments or context. The current, modified form then needs its own sourcing through Step C or the internal-method tag below.
* **No corresponding entry in any spec**: proceed directly to Step C.

Internal spec documents for Step B:

* PACE-CALC-pH-001
* PACE-FEAT-MPP-002
* PACE-NF-IMPL-001
* PACE-ALGO-BAL-001
* PACE\_Process\_Recommendation\_Algorithm\_v1.0
* PACE\_TwoPass\_RO\_Extension\_Proposal
* PACE\_MembraneAgingModel\_Proposal

If any of these is missing from your context when you need it, say so explicitly rather than guessing at its contents.

**Step C — External sourcing.** For anything not confirmed via Step B, find the equation's actual origin in a credible, publicly accessible source: peer-reviewed literature, established reference texts (e.g., *Perry's Chemical Engineers' Handbook*, Crittenden et al., *MWH's Water Treatment*), recognized standards bodies (AWWA, ASTM), the USGS PHREEQC documentation, membrane manufacturer technical literature (e.g., DuPont Filmtec), or the original foundational paper (e.g., Spiegler \& Kedem, 1966, for the Spiegler-Kedem-Katchalsky formulation). Every external citation needs a live URL and is marked `\[VERIFIED — External Source: <URL>, accessed <date>]`.

**Internal-method tag — for Permionics' own engineering work.** Not everything needs, or has, an external citation. Where the current implementation is a deliberate in-house refinement or heuristic — not derived from a textbook or paper, but from Permionics' own engineering judgment or observed behavior — say so plainly rather than forcing an external citation onto it or defaulting it to unverified. Mark it `\[INTERNAL METHOD — Permionics-developed; based on <originating method, if any>; rationale: <if inferable from context, else "not documented in available material">]`. This is not a lesser category than an external citation — in a document going to management, correctly labeled proprietary engineering work is a point of record, not a gap.

**Hard rule — no fabrication.** If none of the above applies — no confirmed spec match, no credible external source, and no clear basis to call it an internal method — do not invent or guess a citation. Mark it `\[UNVERIFIED — REQUIRES ENGINEERING REVIEW]` and state briefly why. Given how much of this codebase has moved past its original specs, expect a meaningful number of these, and expect a meaningful number of internal-method tags too — that's a correct and expected outcome of this process, not a failure of it. A flagged gap is always acceptable. A fabricated, mismatched, or stale citation in a document going to management is not — treat this as the single most important rule in this prompt.

## 6\. Traceability matrix (close the document with this)

One row per equation/algorithm across the entire codebase:

|Module|Equation / Algorithm|Code location (file:function)|Source tier|Citation|Confidence flag|
|-|-|-|-|-|-|

This is a standard requirements-traceability-matrix structure — the same pattern used in regulated engineering documentation to tie implementation back to justification. It's what lets anyone verify the document against the code line by line, and it's what lets every `\[UNVERIFIED]` item be found in one place instead of hunted for across the whole document.

## 7\. Format requirements

* Deliverable: markdown. A single file if it stays manageable; otherwise a master index file plus one file per module — your judgment call on which, but provide a master index either way.
* Math notation: use standard LaTeX-style delimiters (`$$...$$` for display equations, `$...$` inline) so equations survive conversion to Word. Avoid Unicode-only math symbols where a LaTeX equivalent exists.
* Consistent heading hierarchy: H1 = document title, H2 = module, H3 = subsections within a module. This needs to map cleanly onto Word heading styles.
* Tables for every input/output list and for the final traceability matrix.
* No marketing language, no filler. This is an internal engineering record for management and future engineers, not a pitch document.

## 8\. Required closing section

After the full documentation, add a **"Gaps \& Confidence Summary"**: a single consolidated list of every `\[UNVERIFIED]` flag raised anywhere in the document, with the module and equation/algorithm name attached, so it can be worked through as a checklist rather than hunted for.

## 9\. Non-negotiables

* Do not skip any module, however small it seems.
* Do not loosely paraphrase a named equation — reproduce it exactly as implemented.
* Do not fabricate, guess, or "best-effort" a citation under any circumstance. An honest gap is always preferable to a confident wrong answer.
* Do not treat an internal spec document as authoritative for the current implementation without confirming, against the actual code, that the equation or algorithm it describes hasn't changed. Where it has changed, the spec's citation does not transfer — document the current form on its own terms.

