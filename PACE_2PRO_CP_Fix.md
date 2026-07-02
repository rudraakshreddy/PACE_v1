# PACE — Two-Pass RO: Pass 2 CP Factor Fix

**Module:** `calc_engine.py` — Pass 2 element solver
**Issue:** β (CP factor) diverging to 3–4+ in Pass 2
**Status:** 3 fixes required — Fix 1 is mandatory (root cause), Fix 3 is safety net, Fix 2 is optional refinement

---

## Root Cause

`β = exp(Jv / k)`

In Pass 1, osmotic pressure Δπ ≈ 5–15 bar acts as a natural brake on Jv inside the NDP term. In Pass 2, the feed is P1 permeate — TDS ≈ 20–50 mg/L — so:

```
π_P2 ≈ 0.01–0.05 bar   (near zero)
NDP   = P_feed − P_perm − Δπ  ≈  P_feed − 0.5 − ~0.03  ≈  P_feed
```

The bisection solver drives Jv to whatever `A × NDP × TCF` produces — potentially 60–80 LMH. At that flux, `exp(Jv / k)` explodes.

The β ≤ 1.25 cap in SOP §5.7 is inside the Pass 1 iterative solver only. The Pass 2 code path inherits the same element solver without the cap being re-applied.

---

## Fix 1 — Flux Ceiling (Root Cause — Mandatory)

Add a maximum design flux cap for Pass 2 **before** Jv is passed into the CP calculation.

Per SOP Appendix E.3, the design flux range for a 2nd-pass RO system (feed = RO permeate) is **35.7–51.0 LMH**. Use 40 LMH as the conservative default ceiling.

### Change

In the Pass 2 element solver, after computing raw flux, before computing β:

```python
# --- existing line (unchanged) ---
Jv_raw = A_eff * NDP * TCF          # units: LMH

# --- ADD THIS ---
J_max_P2 = pass2_config.get("p2_max_flux_lmh", 40.0)   # user-overridable
Jv = min(Jv_raw, J_max_P2)          # hard ceiling before CP is computed
# --- end addition ---

# Jv is now used for all downstream calculations (beta, Qp, etc.)
```

### API / Config

Add `p2_max_flux_lmh` to `pass2_config` in the request payload:

```json
"pass2": {
  "membrane": "HPARO-8040-LF",
  "stages": 1,
  "vessels_per_stage": [2],
  "elements_per_vessel": 6,
  "target_recovery_pct": 85.0,
  "p2_max_flux_lmh": 40.0
}
```

If the field is absent, default to `40.0`.

---

## Fix 3 — Enforce β Cap in Pass 2 Element Solver (Safety Net — Mandatory)

The SOP §5.7 cap of `β ≤ 1.25` must be explicitly re-applied in the Pass 2 element solver. Use **1.20** for Pass 2 — slightly tighter than Pass 1's 1.25, because Pass 2 feed is pre-filtered by Pass 1 (effective SDI < 0.5, negligible fouling potential), so sustained β above 1.20 is physically implausible and indicates solver divergence.

### Change

In the Pass 2 element solver, at the β calculation step:

```python
# Pass 1 element solver (unchanged — SOP §5.7):
beta = min(exp(Jv / k), 1.25)

# Pass 2 element solver (new):
beta_P2 = min(exp(Jv_P2 / k_P2), 1.20)   # cap is 1.20, not 1.25
```

> **Note:** If Pass 1 and Pass 2 share the same element solver function, pass the cap value as a parameter:
>
> ```python
> def simulate_element(... , beta_cap=1.25):
>     ...
>     beta = min(exp(Jv / k), beta_cap)
>
> # Pass 1 call:
> simulate_element(..., beta_cap=1.25)
>
> # Pass 2 call:
> simulate_element(..., beta_cap=1.20)
> ```

---

## Fix 2 — Ion-Specific D_AB for Pass 2 Feed (Optional Refinement)

The SOP uses a fixed reference diffusivity `D_AB,ref = 1.6×10⁻⁹ m²/s` (Stokes-Einstein for NaCl at 25°C). This is appropriate for a NaCl-dominated Pass 1 feed.

In Pass 2, when the primary design objective is boron removal (feed boron > 1 mg/L), the dominant solute is **H₃BO₃** whose diffusivity is ~1.1×10⁻⁹ m²/s — about 30% lower than NaCl. A lower D_AB means a lower mass transfer coefficient k and a slightly higher β. Without this correction, boron rejection in Pass 2 is slightly overestimated.

### Change

Replace the fixed `D_AB,ref` in the Pass 2 element solver with an ion-weighted mean:

```python
# Ion-specific diffusivities at 25°C [m²/s] — Stokes-Einstein estimates
D_AB_ions = {
    'Na':   1.33e-9,
    'Cl':   2.03e-9,
    'Ca':   0.79e-9,
    'Mg':   0.71e-9,
    'SO4':  1.07e-9,
    'HCO3': 1.19e-9,
    'K':    1.96e-9,
    'B':    1.10e-9,   # boron — key for pH 9.5–10.5 Pass 2
    'NO3':  1.90e-9,
}
D_AB_DEFAULT = 1.6e-9   # fallback for unlisted ions

def compute_weighted_D_AB(p2_feed_ions: dict) -> float:
    """
    p2_feed_ions: dict of {ion_name: concentration_mg_L}
    Returns concentration-weighted mean diffusivity [m²/s].
    Falls back to D_AB_DEFAULT if feed is essentially pure water.
    """
    total_conc = sum(p2_feed_ions.values())
    if total_conc < 1.0:                   # near-pure water — use default
        return D_AB_DEFAULT
    weighted = sum(
        conc * D_AB_ions.get(ion, D_AB_DEFAULT)
        for ion, conc in p2_feed_ions.items()
    )
    return weighted / total_conc

# In the P2 element solver, replace:
#   DAB_25 = 1.6e-9
# with:
DAB_25_P2 = compute_weighted_D_AB(p2_feed_ions)

# Temperature correction is unchanged (SOP §5.3 Step 4):
DAB_T_P2 = DAB_25_P2 * (T_K / 298.15) * (mu_25 / mu_T)
```

This fix is **secondary** — Fix 1 eliminates the β=4 problem entirely. Apply Fix 2 only after Fix 1 and Fix 3 are verified working.

---

## Expected β Values After Fixes

| Condition | Before fixes | After Fix 1 + Fix 3 |
|---|---|---|
| P2, Jv unconstrained (~65 LMH), v = 0.18 m/s | β ≈ 3.5–4.2 | β ≈ 1.12–1.18 |
| P2, Jv = 40 LMH (capped), v = 0.18 m/s | β ≈ 1.9–2.4 | β ≈ 1.12–1.18 |
| P2, Jv = 25 LMH, v = 0.18 m/s | β ≈ 1.9–2.4 | β ≈ 1.09–1.14 |
| P1, Jv = 22 LMH (unchanged) | β ≈ 1.10–1.18 | β ≈ 1.10–1.18 (no change) |

**Sanity check:** Pass 2 β must always be ≤ Pass 1 β at the same crossflow velocity. P2 feed is cleaner and P2 flux is lower (after Fix 1) — both reduce β relative to P1. If P2 β > P1 β in your output, Fix 1 has not taken effect.

---

## Implementation Checklist

```
[ ] Add p2_max_flux_lmh to pass2_config schema (default: 40.0 LMH)
[ ] Fix 1: In P2 element solver — Jv = min(A * NDP * TCF, J_max_P2)
[ ] Fix 3: In P2 element solver — beta = min(exp(Jv / k), 1.20)
[ ] If P1 and P2 share one element function, add beta_cap parameter (1.25 / 1.20)
[ ] Verify at clean state (t=0): P2 β range is 1.05–1.18 across all elements
[ ] Verify: P2 element 1 (highest flux) has highest β; P2 element 6 has lowest β
[ ] Verify: system-wide P2 β ≤ P1 β at matched crossflow velocity
[ ] Optional Fix 2: use compute_weighted_D_AB(p2_feed_ions) for boron-targeted systems
```

---

## References

- SOP v1.0 §5.3 Step 8 — CP Beta Factor (Film Model): `β = exp(Jv / k)`, cap β ≤ 1.25
- SOP v1.0 §5.7 — Iterative Convergence Solver: 0.7/0.3 relaxation, β cap at 1.25
- SOP v1.0 Appendix E.3 — Design Flux Guidelines: 2nd pass (RO permeate feed) 35.7–51.0 LMH
- Two-Pass RO Extension Proposal §4.2 — Pass 2 Bisection: P2 pressure bounds
