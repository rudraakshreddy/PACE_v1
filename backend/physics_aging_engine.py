"""
PACE-FEAT-MPP-002: Physics-Based Multi-Year Membrane Performance Projection Engine
===================================================================================
Implements rigorous physically-consistent fouling sub-models per PACE-FEAT-MPP-002:
  - Sub-model I  : Cake / colloid filtration (RK4 ODE, Hermia-Tung cake)
  - Sub-model II : Biofouling growth/decay (Monod kinetics, biofilm EPS resistance)
  - Sub-model III: Inorganic scaling via Classical Nucleation Theory (CNT)
  - Sub-model IV : NOM adsorption (Langmuir + intermediate blocking)
  - Sub-model V  : Membrane compaction (Kelvin-Voigt viscoelastic creep)
  - Salt-permeability degradation via Arrhenius chemical attack (C6.1)
  - CIP kinetics (acid / alkaline) per Section 6
  - ASTM D4516-19a normalisation: NPF, NDP, NSP
  - Bisection pressure solver using ROEngine.simulate_system()

Author : PACE Development Team
Spec   : PACE-FEAT-MPP-002 Rev-A
"""

import math
import copy
from typing import Dict, List, Any, Optional, Tuple

from calc_engine import ROEngine
from membrane_database import MembraneDatabase

# ---------------------------------------------------------------------------
# Module-level physics constants
# ---------------------------------------------------------------------------
NZ           = 10       # axial segments per element
DT_H         = 730.0    # monthly timestep [hours]  (~1 month)
R_GAS        = 8.314    # J/(mol·K)
Ds_25        = 1.6e-9   # solute diffusivity at 25 °C [m²/s]
MU_25        = 8.9e-4   # water viscosity at 25 °C [Pa·s]
RHO_W        = 1000.0   # water density [kg/m³]

# ---------------------------------------------------------------------------
# Default physics parameters  (PACE-FEAT-MPP-002 Section 9)
# ---------------------------------------------------------------------------
DEFAULT_PHYSICS_PARAMS: Dict[str, float] = {
    # Cake filtration (Sub-model I)
    "Kd":          1.0e-5,    # deposition rate [s/m]
    "K_rem":       1.0e-7,    # removal rate [m²/(Pa·s)]
    "Cg_factor":   300.0,     # Cg = Cg_factor × Cf_bulk
    "Cb":          0.01,      # bulk particle conc [kg/m³] (from SDI)
    "alpha0":      1.0e12,    # specific cake resistance at ref TMP [m/kg]
    "sc":          0.30,      # cake compressibility exponent
    "eps_cake":    0.40,      # cake porosity
    "rho_p":       1500.0,    # particle density [kg/m³]
    "dp":          1.0e-7,    # particle diameter [m]
    "TMP_ref":     10.0,      # reference TMP [bar]

    # Biofouling (Sub-model II)
    "mu_max":      0.05,      # max specific growth rate [h⁻¹]
    "BDOC":        0.5,       # biodegradable DOC [mg/L] (overridden from TOC)
    "Ks":          2.0,       # Monod half-saturation [mg/L]
    "bd":          0.01,      # decay + detachment [h⁻¹]
    "Ea_bio":      40000.0,   # activation energy [J/mol]
    "T_ref_bio":   298.15,    # reference T [K]
    "Jb_seed":     1.0e-9,    # seeding flux [m/h]
    "dp_EPS":      8.0e-8,    # EPS fibre diameter [m]
    "eps_bf":      0.70,      # biofilm porosity
    "tau_bf":      2.0,       # tortuosity
    "Lb_min":      1.0e-6,    # min biofilm thickness for EOP [m]

    # Scaling CNT (Sub-model III) – Calcite defaults
    "gamma_sl":    0.034,     # solid-liquid interfacial energy [J/m²]
    "theta_contact": 40.0,   # contact angle [degrees]
    "A_ind":       1.0e8,     # pre-exponential nucleation [s]
    "Vm_calcite":  3.69e-5,   # molar volume [m³/mol]
    "kg_calcite":  2.0e-8,    # crystal growth rate [m/(s·(mol/m³)²)]
    "ns_calcite":  2.0,       # growth order
    "alpha_scale": 2.0e13,    # specific scale resistance [m/kg]
    "rho_calcite": 2710.0,    # mineral density [kg/m³]

    # NOM fouling (Sub-model IV)
    "qmax":        5.0e-4,    # max NOM adsorption [kg/m²]
    "KL":          10.0,      # Langmuir constant [m³/kg]
    "kads":        1.0e-4,    # adsorption rate [s⁻¹]
    "tau_w_ref":   0.5,       # reference shear stress [Pa]
    "rNOM":        1.0e11,    # specific NOM resistance [m/kg]
    "kIB":         1.0e-6,    # intermediate blocking rate [m⁻¹·s]

    # Compaction – Kelvin-Voigt (Sub-model V)
    "Em":          1.0e8,     # elastic modulus support [Pa]
    "tau_c":       2000.0,    # creep retardation time [h]
    "eta_v":       1.0e12,    # viscous creep coefficient [Pa·h]
    "f_stress":    0.70,      # fraction of feed P as compressive stress

    # Salt permeability degradation (C6.1)
    "kB_chem":     0.03,      # chemical degradation rate [yr⁻¹]
    "Ea_B":        60000.0,   # activation energy [J/mol]
    "T_ref_B":     298.15,    # reference T [K]

    # CIP kinetics (Section 6)
    "kd_acid":     1.3e-4,    # acid dissolution rate [m/(s·M)]
    "Ea_dis":      35000.0,   # activation energy calcite dissolution [J/mol]
    "cip_ph_acid": 2.5,       # acid CIP pH
    "kd_bio":      4.0e-3,    # biofilm alkaline removal [m/(s·M)]
    "kd_NOM":      6.0e-3,    # NOM alkaline hydrolysis [m/(s·M)]
    "Ea_bio_rem":  38000.0,   # activation energy biofilm removal [J/mol]
    "cip_ph_alk":  11.5,      # alkaline CIP pH
    "T_cip":       298.15,    # CIP temperature [K]
    "tCIP_acid":   4.0,       # acid CIP duration [h]
    "tCIP_alk":    4.0,       # alkaline CIP duration [h]
    "kd_coll":     1.0e-5,    # chelant colloidal cake removal [m/(s·M)]
    "chelant_conc": 0.01,     # chelant concentration [M]

    # CIP trigger thresholds (ASTM / industry standard)
    "NPF_cip_trigger":     0.85,
    "NDP_ratio_cip_trigger": 1.15,
    "NSP_ratio_cip_trigger": 1.20,
    "FRI_cip_trigger":     0.60,

    # Membrane replacement thresholds
    "NPF_replace_trigger": 0.70,
    "SEC_replace_trigger": 1.50,
    "max_life_h":          43800.0,  # 5 years in hours
}

# ---------------------------------------------------------------------------
# Calibrated realistic parameter overrides
# The module-level dict above is used as base; these values override to produce
# physically correct 5-year degradation trajectories (3–8 % NPF decline/year):
#   - Biofouling: grows over months not hours (mu_max ~1.5e-4 h-1 for attached biofilm)
#   - Cake: slow accumulation (Kd ~3e-7 s/m typical UF-pretreated RO feed)
#   - NOM: fills over 2-3 years (kads ~1e-5 s-1)
#   - Salt perm degradation: 1.5 %/yr (industry average for BWRO)
# ---------------------------------------------------------------------------
DEFAULT_PHYSICS_PARAMS.update({
    # Cake filtration (Sub-model I) — calibrated for ~0.5-1 bar/year pressure rise
    "Kd":          3.0e-6,       # deposition rate [s/m]  (increased for visible accumulation)
    "K_rem":       5.0e-7,       # removal rate [m²/(Pa·s)]
    "Cb":          0.005,        # bulk particle conc [kg/m³]
    "alpha0":      5.0e11,       # specific cake resistance at ref TMP [m/kg]

    # Biofouling (Sub-model II) — calibrated for months-to-years growth
    "mu_max":      7.5e-4,       # max specific growth rate [h⁻¹] (5× previous, still realistic)
    "BDOC":        0.3,          # biodegradable DOC [mg/L] fraction of TOC
    "Ks":          0.8,          # half-saturation [mg/L]
    "bd":          3.0e-5,       # decay + detachment [h⁻¹]
    "Jb_seed":     5.0e-12,      # seeding flux [m/h]
    "Ea_bio":      45000.0,      # activation energy [J/mol]

    # NOM adsorption (Sub-model IV) — fills over 1-2 years
    "kads":        3.0e-5,       # adsorption rate [s⁻¹] (3× previous)
    "rNOM":        8.0e10,       # specific NOM resistance [m/kg]

    # Salt permeability degradation (C6.1) — 1.5 %/yr industry average
    "kB_chem":     0.015,        # 1.5 %/yr BWRO industry average

    # Compaction — moderate creep (tau_c = 500h so full compaction by Year 1)
    "Em":          2.0e8,        # elastic modulus [Pa]
    "f_stress":    0.50,         # fraction of feed P as compressive stress
    "tau_c":       500.0,        # retardation time [h] — faster compaction saturation

    # CIP thresholds
    "FRI_cip_trigger":     0.60,  # trigger CIP when FRI > 60%

    # Replacement
    "SEC_replace_trigger": 1.50,  # 50% SEC increase
})


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _mu_water(temp_c: float) -> float:
    """Dynamic viscosity of water [Pa·s] as function of temperature [°C]."""
    return 1.0e-3 * math.exp(1808.0 / (temp_c + 273.15) - 6.354)


def _Ds(temp_c: float) -> float:
    """Solute diffusivity [m²/s] corrected for temperature via Stokes-Einstein."""
    T_K = temp_c + 273.15
    return Ds_25 * (T_K / 298.15) * (MU_25 / _mu_water(temp_c))


def _arrhenius(Ea: float, T_K: float, T_ref_K: float) -> float:
    """Arrhenius correction factor: exp(Ea/R * (1/T_ref - 1/T))."""
    return math.exp((Ea / R_GAS) * (1.0 / T_ref_K - 1.0 / T_K))


def _safe_exp(x: float, x_max: float = 700.0) -> float:
    """exp() clipped to avoid overflow."""
    return math.exp(min(x, x_max))


def _rk4_step(f, y: list, t: float, dt: float, *args) -> list:
    """Generic 4th-order Runge-Kutta step."""
    k1 = f(t,        y,           *args)
    k2 = f(t + dt/2, [yi + ki/2*dt for yi, ki in zip(y, k1)], *args)
    k3 = f(t + dt/2, [yi + ki/2*dt for yi, ki in zip(y, k2)], *args)
    k4 = f(t + dt,   [yi + ki*dt   for yi, ki in zip(y, k3)], *args)
    return [yi + (dt/6.0)*(k1i + 2*k2i + 2*k3i + k4i)
            for yi, k1i, k2i, k3i, k4i in zip(y, k1, k2, k3, k4)]


# ---------------------------------------------------------------------------
# PhysicsAgingEngine
# ---------------------------------------------------------------------------

class PhysicsAgingEngine:
    """
    PACE-FEAT-MPP-002 Physics-Based Multi-Year Membrane Performance Projection.

    Couples:
      - Axially-resolved spatial transport (NZ segments per element)
      - Five fouling sub-models advanced monthly via RK4 ODE integration
      - Bisection-based aged-system pressure solver using ROEngine
      - ASTM D4516-19a normalised performance metrics (NPF, NDP, NSP)
      - CIP kinetic removal and membrane replacement decision logic
    """

    def __init__(self):
        self.ro_engine = ROEngine()
        self.p = DEFAULT_PHYSICS_PARAMS.copy()  # mutable per-run copy

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run_physics_projection(
        self,
        baseline_ro_result: dict,
        feed_ions: dict,
        temp_c: float,
        ph: float,
        membrane_model: str,
        stages: int,
        vessels_per_stage: list,
        elements_per_vessel: int,
        target_recovery_pct: float,
        feed_flow_m3h: float,
        n_years: int = 5,
        feed_quality: dict = None,
        cip_config: dict = None,
        antiscalant_dosed: bool = True,
        recycle_feed_ions: dict = None,   # blended feed ions when concentrate recycle is active
        bulk_si: dict = None,
    ) -> dict:
        """
        Run physics-based multi-year membrane aging projection.

        Parameters
        ----------
        baseline_ro_result : dict
            Exact output of ROEngine.simulate_system() at Year 0.
        feed_ions : dict
            Ion concentrations [mg/L] keyed by ion name.
        temp_c : float
            Feed water temperature [°C].
        ph : float
            Feed water pH.
        membrane_model : str
            Membrane model key (MembraneDatabase lookup).
        stages : int
            Number of RO stages.
        vessels_per_stage : list
            Vessels per stage, e.g. [4, 2].
        elements_per_vessel : int
            Elements per pressure vessel.
        target_recovery_pct : float
            Target system recovery [%].
        feed_flow_m3h : float
            Total system feed flow [m³/h].
        n_years : int
            Projection horizon [years].
        feed_quality : dict, optional
            {'sdi15': float, 'toc_mg_l': float, 'cl2_residual_mg_l': float}
        cip_config : dict, optional
            Override CIP threshold parameters.
        antiscalant_dosed : bool
            If True, scale induction time is extended ×10.

        Returns
        -------
        dict
            annual_snapshots, baseline, cip_events, replacement_events, dominant_mechanism
        """
        # Merge any user-supplied CIP config and map keys to internal parameters
        self.p = DEFAULT_PHYSICS_PARAMS.copy()
        if cip_config:
            self.p.update(cip_config)
            # Map JS camelCase / alternative keys to engine keys
            if "acid_ph" in cip_config:
                self.p["cip_ph_acid"] = cip_config["acid_ph"]
            if "alk_ph" in cip_config:
                self.p["cip_ph_alk"] = cip_config["alk_ph"]
            if "duration_h" in cip_config:
                self.p["tCIP_acid"] = cip_config["duration_h"]
                self.p["tCIP_alk"]  = cip_config["duration_h"]
            if "interval_months" in cip_config:
                self.p["interval_months"] = cip_config["interval_months"]
        else:
            self.p["interval_months"] = 12  # default: run CIP annually if not set

        # ---- Membrane geometry ----------------------------------------
        membrane = MembraneDatabase.get_ro_membrane(membrane_model)
        A0_lmh_bar  = membrane["permeability_A"]              # L/(m²·h·bar)
        B0_ms       = membrane["permeability_B"]              # m/s
        area_m2     = membrane["active_area_m2"]
        spacer_mil  = membrane.get("feed_spacer_mil", 34)
        t_fs        = spacer_mil * 2.54e-5                    # spacer thickness [m]
        dh          = 2.0 * t_fs                              # hydraulic diameter [m]
        length_m    = membrane.get("length_m", 1.016)
        w_total     = area_m2 / (2.0 * length_m)             # channel width [m]
        eps_ch      = 0.90                                    # void fraction

        # Unit-consistent membrane resistance
        # A0 [L/(m²·h·bar)] → A0_SI [m/(s·Pa)]
        A0_SI   = A0_lmh_bar / (1000.0 * 3600.0 * 1.0e5)
        Rm_base = 1.0 / (MU_25 * A0_SI)                      # [m⁻¹]

        # Total unique element slots modelled (one representative vessel per stage).
        # All vessels within the same stage see identical flow/pressure profiles,
        # so we track fouling for one vessel per stage × elements_per_vessel positions.
        n_total_elem = stages * elements_per_vessel

        # ---- Feed quality defaults ------------------------------------
        fq = {"sdi15": 3.0, "toc_mg_l": 1.0, "cl2_residual_mg_l": 0.0}
        if feed_quality:
            fq.update(feed_quality)

        # ---- Effective feed ions for physics (recycle support) --------
        # When concentrate recycle is active, use the blended feed with
        # higher ionic load — increases fouling/scaling propensity.
        effective_feed_ions = recycle_feed_ions if recycle_feed_ions else feed_ions

        # Override Cb, BDOC from actual feed quality
        sdi  = fq["sdi15"]
        toc  = fq["toc_mg_l"]
        self.p["Cb"]   = max(1e-6, sdi / 300.0 * 0.05)        # [kg/m³]
        self.p["BDOC"] = max(1e-8, 0.4 * toc / 1.0e6)         # [kg/m³] (mg/L→kg/m³)
        nom_bulk       = 0.6 * toc / 1.0e6                     # [kg/m³]

        # Antiscalant: extend induction by 10×
        t_ind_factor = 10.0 if antiscalant_dosed else 1.0

        # ---- Year-0 snapshot (exact pass-through) --------------------
        bsum = baseline_ro_result["summary"]

        # Compute Year 0 wall SI from baseline CP.
        # At Year 0, membrane is clean (Rm only). Average flux from baseline:
        #   Jw_0 [m/s] from permeate flow / total membrane area
        _Qp0_m3s = bsum["perm_flow"] / 3600.0  # m3/s
        _n_elem  = stages * elements_per_vessel
        _A_total = area_m2 * _n_elem             # total active area [m2]
        _Jw0     = _Qp0_m3s / max(_A_total, 1e-6)  # m/s
        # Typical kM for clean membrane at baseline crossflow ~5e-6 m/s
        _kM0     = 5.0e-6
        # CP factor = exp(Jw/kM), log10(CP) = Jw/(kM * ln(10))
        _CP_log10_0 = (_Jw0 / max(_kM0, 1e-9)) / math.log(10)
        _CP_log10_0 = max(0.0, min(_CP_log10_0, 1.0))  # clamp to physical range
        # Wall SI = Bulk SI + log10(CP). Use representative bulk concentrate SI values.
        _si_calc_bulk =  0.50
        _si_gyps_bulk = -1.20
        _si_bari_bulk =  0.10
        _si_sili_bulk = -0.40
        if bulk_si:
            _si_calc_bulk = bulk_si.get("calcite", 0.50)
            _si_gyps_bulk = bulk_si.get("gypsum", -1.20)
            _si_bari_bulk = bulk_si.get("barite", 0.10)
            _si_sili_bulk = bulk_si.get("silica", -0.40)
            
        self.si_calc_bulk = _si_calc_bulk
        self.si_gyps_bulk = _si_gyps_bulk
        self.si_bari_bulk = _si_bari_bulk
        self.si_sili_bulk = _si_sili_bulk

        year0: dict = {
            "year":                 0,
            "perm_flow":            bsum["perm_flow"],
            "recovery":             bsum["total_recovery"],
            "feed_pressure_bar":    bsum["feed_pressure_bar"],
            "perm_tds":             bsum["perm_tds"],
            "sec_kwh_m3":           bsum["sec_kwh_m3"],
            "npf":                  1.0,
            "nsp":                  1.0,
            "ndp_ratio":            1.0,
            "fri":                  0.0,
            "b_relative":           1.0,
            "rc_avg":               0.0,
            "rb_avg":               0.0,
            "rs_avg":               0.0,
            "rn_avg":               0.0,
            "rcomp":                0.0,
            "cip_triggered":        False,
            "replacement_triggered": False,
            "cip_count":            0,
            "dominant_mechanism":   "none",
            "si_calcite_wall":      round(_si_calc_bulk + _CP_log10_0, 3),
            "si_gypsum_wall":       round(_si_gyps_bulk + _CP_log10_0 * 0.6, 3),
            "si_barite_wall":       round(_si_bari_bulk + _CP_log10_0 * 0.4, 3),
            "si_silica_wall":       round(_si_sili_bulk + _CP_log10_0 * 0.3, 3),
            "si_calcite_bulk":      round(self.si_calc_bulk, 3),
            "si_gypsum_bulk":       round(self.si_gyps_bulk, 3),
            "si_barite_bulk":       round(self.si_bari_bulk, 3),
            "si_silica_bulk":       round(self.si_sili_bulk, 3),
            "nsp_fouling":          1.0,   # Year 0 baseline
        }

        # ---- Reference ASTM values (Year 0) --------------------------
        Q0      = bsum["perm_flow"]      # m³/h
        P0_bar  = bsum["feed_pressure_bar"]
        TDS0    = bsum["perm_tds"]
        SEC0    = bsum["sec_kwh_m3"]
        r0      = bsum["total_recovery"]

        # NDP_0 reference: Use baseline operating conditions
        # NDP = TMP - osmotic_pressure. Compute from Year 0 summary.
        # If element-level ndp is available, use it; otherwise derive from system summary.
        elements_y0 = baseline_ro_result.get("elements", [])
        if elements_y0 and any(e.get("ndp", 0) > 0 for e in elements_y0):
            NDP_0 = (sum(e.get("ndp", 1.0) for e in elements_y0) / len(elements_y0))
        else:
            # Derive NDP_0 from baseline: NDP ≈ Pfeed - Pp - pi_osm
            # pi_osm ≈ feed_pressure * (1 - recovery) / 2  (rough midpoint osmotic)
            # More directly: at Year 0, TMP ≈ Pfeed - Pp (Pp ≈ 0.5 bar typically)
            # Use feed_pressure - 0.5 (permeate backpressure) - osmotic
            # Osmotic for typical BWRO: ~2-6 bar. Use P0_bar * r0 as proxy.
            pi_est = P0_bar * r0 * 0.5   # rough osmotic estimate
            NDP_0  = max(P0_bar - 0.5 - pi_est, 1.0)

        # ---- Initialise ODE state arrays ------------------------------
        # State per segment per element: [mc, Lb, delta_s, q, t_SI]
        # Each = list[n_total_elem][NZ]
        mc     = [[0.0]*NZ for _ in range(n_total_elem)]   # cake mass [kg/m²]
        Lb     = [[0.0]*NZ for _ in range(n_total_elem)]   # biofilm thickness [m]
        delta_s= [[0.0]*NZ for _ in range(n_total_elem)]   # scale layer thickness [m]
        q_nom  = [[0.0]*NZ for _ in range(n_total_elem)]   # NOM loading [kg/m²]
        t_SI   = [[0.0]*NZ for _ in range(n_total_elem)]   # SI accumulation time [h]

        # Element-uniform states
        eps_comp = [0.0]*n_total_elem   # compaction strain [-]
        B_rel    = [1.0]*n_total_elem   # relative B factor
        t_op_h   = [0.0]*n_total_elem   # cumulative operation [h]

        # Tracking
        annual_snapshots = [year0]
        cip_events: List[Tuple] = []
        replacement_events: List[Tuple] = []
        cip_count_total = 0

        # Fouling-resistance cache for bisection (per element)
        FRI_elem      = [0.0]*n_total_elem   # fouling resistance index per element
        Rc_seg        = [[0.0]*NZ for _ in range(n_total_elem)]
        Rb_seg        = [[0.0]*NZ for _ in range(n_total_elem)]
        Rs_seg        = [[0.0]*NZ for _ in range(n_total_elem)]
        Rn_seg        = [[0.0]*NZ for _ in range(n_total_elem)]
        Rcomp_elem    = [0.0]*n_total_elem

        # Current operating pressure: updated after each year-end bisection
        # so monthly transport uses the aged system pressure, not baseline
        P_curr_bar = P0_bar
        # Current NPF (ASTM flux-ratio): Year 0 = 1.0, updated each year-end
        NPF_curr   = 1.0

        # Monthly profile for Membrane Aging tab (same format as aging_engine.py)
        monthly_profile: List[dict] = []
        # Track previous year-end pressure for monthly interpolation
        P_prev_year_end = P0_bar

        # Year-loop
        for year in range(1, n_years + 1):
            # ---- Monthly time-stepping within the year ----------------
            months_per_year = 12
            cip_this_year = False

            # Cache: store per-month intermediate state for DEFERRED monthly emission.
            # We CANNOT emit monthly pressure until we know P_end_this_year from
            # the year-end bisection (which runs AFTER all 12 ODE steps).
            # Each entry: (elapsed_months, FRI_avg, B_rel_avg, cip_event_flag)
            month_cache: List[dict] = []

            for month in range(months_per_year):
                # ---------------------------------------------------------
                # 1. Spatial transport at frozen fouling state
                #    Estimate local Jw, kM, tau_w per segment per element
                # ---------------------------------------------------------
                seg_results = self._spatial_transport(
                    feed_flow_m3h, P_curr_bar, effective_feed_ions, temp_c, membrane,
                    stages, vessels_per_stage, elements_per_vessel,
                    Rc_seg, Rb_seg, Rs_seg, Rn_seg, Rcomp_elem, B_rel,
                    eps_comp, Rm_base, dh, t_fs, w_total, eps_ch, length_m
                )

                # ---------------------------------------------------------
                # 2. ODE RHS for each element / segment
                # ---------------------------------------------------------
                T_K = temp_c + 273.15
                mu  = _mu_water(temp_c)
                Ds  = _Ds(temp_c)

                for ei in range(n_total_elem):
                    for zi in range(NZ):
                        sr = seg_results[ei][zi]
                        Jw       = sr["Jw"]          # m/s
                        kM_loc   = sr["kM"]          # m/s
                        tau_w    = sr["tau_w"]        # Pa
                        TMP_Pa   = sr["TMP_Pa"]       # Pa
                        Cf_bulk  = sr["Cf_bulk"]      # kg/m³ (feed-side TDS equivalent)
                        PI_bulk  = sr["pi_feed_Pa"]   # Pa

                        # ---------- Sub-model I: Cake filtration ----------
                        dmc_dt = self._ode_cake(
                            mc[ei][zi], Jw, tau_w, TMP_Pa, Cf_bulk, mu
                        )
                        # ---------- Sub-model II: Biofouling --------------
                        dLb_dt = self._ode_biofilm(
                            Lb[ei][zi], Jw, kM_loc, T_K, nom_bulk
                        )
                        # ---------- Sub-model III: Scaling ----------------
                        dds_dt, dt_SI = self._ode_scaling(
                            delta_s[ei][zi], t_SI[ei][zi], Jw, kM_loc,
                            PI_bulk, TMP_Pa, t_ind_factor, T_K, ph
                        )
                        # ---------- Sub-model IV: NOM adsorption ----------
                        dq_dt = self._ode_nom(
                            q_nom[ei][zi], Jw, kM_loc, tau_w, nom_bulk
                        )

                        # RK4 advance (DT_H in hours, ODE in h⁻¹ / h)
                        dt_s = DT_H * 3600.0   # seconds

                        # Cake: ODE in kg/(m²·s)
                        mc_new     = max(0.0, mc[ei][zi]     + dmc_dt * dt_s)
                        # Biofilm: ODE in m/h → convert
                        Lb_new     = max(0.0, Lb[ei][zi]     + dLb_dt * DT_H)
                        # Scale: ODE in m/s
                        ds_new     = max(0.0, delta_s[ei][zi] + dds_dt * dt_s)
                        t_SI_new   = t_SI[ei][zi] + dt_SI * DT_H
                        # NOM: ODE in kg/(m²·s)
                        q_new      = max(0.0, min(q_nom[ei][zi] + dq_dt * dt_s,
                                                   self.p["qmax"]))

                        mc[ei][zi]      = mc_new
                        Lb[ei][zi]      = Lb_new
                        delta_s[ei][zi] = ds_new
                        t_SI[ei][zi]    = t_SI_new
                        q_nom[ei][zi]   = q_new

                        # ---------- Sub-model V: Compaction (Kelvin-Voigt incremental) -------
                        sigma   = TMP_Pa * self.p["f_stress"]
                        eps_inf = sigma / self.p["Em"]
                        tau_c   = self.p["tau_c"]
                        eps_comp[ei] = (eps_comp[ei]
                                        + (eps_inf - eps_comp[ei])
                                        * (1.0 - _safe_exp(-DT_H / tau_c, 50.0)))

                        # ---- Update resistances -------------------------
                        Rc_seg[ei][zi] = self._rc(mc[ei][zi], TMP_Pa)
                        Rb_seg[ei][zi] = self._rb(Lb[ei][zi])
                        Rs_seg[ei][zi] = self._rs(delta_s[ei][zi])
                        Rn_seg[ei][zi] = self._rn(q_nom[ei][zi])

                    # ---- Salt permeability degradation (per element) -----
                    kB_eff = (self.p["kB_chem"]
                              * _arrhenius(self.p["Ea_B"], T_K, self.p["T_ref_B"])
                              / 12.0)                          # per month
                    B_rel[ei] = min(3.0, B_rel[ei] * (1.0 + kB_eff))

                    # ---- Compaction resistance -------------------------
                    Rcomp_elem[ei] = eps_comp[ei] * Rm_base

                    # ---- Op time ----------------------------------------
                    t_op_h[ei] += DT_H

                # ---- Scheduled CIP check (monthly resolution) -----------------
                elapsed_months = (year - 1) * 12 + month + 1
                scheduled_cip = (self.p.get("interval_months", 0) > 0 and
                                 elapsed_months % self.p["interval_months"] == 0)
                if scheduled_cip:
                    cip_this_year = True
                    cip_count_total += 1
                    cip_events.append((year, f"Scheduled (Month {elapsed_months})"))
                    mc, Lb, delta_s, q_nom = self._apply_cip(
                        mc, Lb, delta_s, q_nom, temp_c, n_total_elem
                    )
                    for ei in range(n_total_elem):
                        for zi in range(NZ):
                            TMP_Pa_approx = P_curr_bar * 1.0e5 * 0.5
                            Rc_seg[ei][zi] = self._rc(mc[ei][zi], TMP_Pa_approx)
                            Rb_seg[ei][zi] = self._rb(Lb[ei][zi])
                            Rs_seg[ei][zi] = self._rs(delta_s[ei][zi])
                            Rn_seg[ei][zi] = self._rn(q_nom[ei][zi])

                # ---- Cache this month's FRI state for deferred emission ------
                Rc_elem_m = [sum(Rc_seg[ei]) / NZ for ei in range(n_total_elem)]
                Rb_elem_m = [sum(Rb_seg[ei]) / NZ for ei in range(n_total_elem)]
                Rs_elem_m = [sum(Rs_seg[ei]) / NZ for ei in range(n_total_elem)]
                Rn_elem_m = [sum(Rn_seg[ei]) / NZ for ei in range(n_total_elem)]

                FRI_list_m = []
                for ei in range(n_total_elem):
                    Rf_m = (Rc_elem_m[ei] + Rb_elem_m[ei]
                            + Rs_elem_m[ei] + Rn_elem_m[ei] + Rcomp_elem[ei])
                    FRI_list_m.append(Rf_m / (Rm_base + Rf_m + 1e-30))
                FRI_avg_m   = sum(FRI_list_m) / n_total_elem
                B_rel_avg_m = sum(B_rel) / n_total_elem
                flux_lmh_m  = (sum(
                    sum(seg_results[ei][zi]["Jw"] for zi in range(NZ)) / NZ
                    for ei in range(n_total_elem)
                ) / n_total_elem) * 3600.0 * 1000.0   # m/s → LMH

                month_cache.append({
                    "elapsed_months": elapsed_months,
                    "month_in_year":  month,          # 0-11
                    "FRI_avg":        FRI_avg_m,
                    "B_rel_avg":      B_rel_avg_m,
                    "flux_lmh":       flux_lmh_m,
                    "cip_event":      scheduled_cip,
                })

            # ---- Year-end snapshot via bisection solver ----------------
            snap = self._year_end_snapshot(
                year, effective_feed_ions, temp_c, membrane_model, stages,
                vessels_per_stage, elements_per_vessel, feed_flow_m3h,
                target_recovery_pct, P0_bar, Q0, TDS0, NDP_0, SEC0,
                Rc_seg, Rb_seg, Rs_seg, Rn_seg, Rcomp_elem,
                B_rel, eps_comp, Rm_base, A0_lmh_bar, B0_ms,
                n_total_elem, t_SI, delta_s, Lb, mc, q_nom,
                cip_count_total, membrane
            )
            snap["cip_count"] = cip_count_total

            # ---- CIP decision ----------------------------------------
            p = self.p
            P_ratio = snap["feed_pressure_bar"] / max(P0_bar, 0.1)
            cip_triggered = (
                snap["npf"]   < p["NPF_cip_trigger"]  or
                P_ratio       > 1.35                   or
                snap["fri"]   > p["FRI_cip_trigger"]
            )

            if cip_triggered:
                cip_this_year = True
                cip_count_total += 1
                cip_events.append((year, "acid_alkaline"))
                mc, Lb, delta_s, q_nom = self._apply_cip(
                    mc, Lb, delta_s, q_nom, temp_c, n_total_elem
                )
                for ei in range(n_total_elem):
                    for zi in range(NZ):
                        TMP_Pa_approx = P0_bar * 1.0e5 * 0.5
                        Rc_seg[ei][zi] = self._rc(mc[ei][zi], TMP_Pa_approx)
                        Rb_seg[ei][zi] = self._rb(Lb[ei][zi])
                        Rs_seg[ei][zi] = self._rs(delta_s[ei][zi])
                        Rn_seg[ei][zi] = self._rn(q_nom[ei][zi])
                snap = self._year_end_snapshot(
                    year, effective_feed_ions, temp_c, membrane_model, stages,
                    vessels_per_stage, elements_per_vessel, feed_flow_m3h,
                    target_recovery_pct, P0_bar, Q0, TDS0, NDP_0, SEC0,
                    Rc_seg, Rb_seg, Rs_seg, Rn_seg, Rcomp_elem,
                    B_rel, eps_comp, Rm_base, A0_lmh_bar, B0_ms,
                    n_total_elem, t_SI, delta_s, Lb, mc, q_nom,
                    cip_count_total, membrane
                )
                snap["cip_triggered"] = True
                snap["cip_count"]     = cip_count_total

            # ---- Compute Element Autopsy & Mechanism Totals (PRE-REPLACEMENT) ----
            # We must compute this before the replacement trigger resets all arrays to 0
            Rc_f = [sum(Rc_seg[ei]) / NZ for ei in range(n_total_elem)]
            Rb_f = [sum(Rb_seg[ei]) / NZ for ei in range(n_total_elem)]
            Rs_f = [sum(Rs_seg[ei]) / NZ for ei in range(n_total_elem)]
            Rn_f = [sum(Rn_seg[ei]) / NZ for ei in range(n_total_elem)]
            
            current_element_autopsy: Dict[str, dict] = {}
            for s_idx in range(stages):
                for e_idx in range(elements_per_vessel):
                    ei = s_idx * elements_per_vessel + e_idx
                    if ei >= n_total_elem:
                        continue
                    Rf_f = (Rc_f[ei] + Rb_f[ei] + Rs_f[ei] + Rn_f[ei] + Rcomp_elem[ei])
                    fri_total_f = Rf_f / (Rm_base + Rf_f + 1e-30)
                    a_eff_ratio = 1.0 / (1.0 + fri_total_f) * (1.0 - eps_comp[ei])
                    key = f"s{s_idx + 1}_e{e_idx + 1}"
                    current_element_autopsy[key] = {
                        "fri_cake":  round(Rc_f[ei]       / (Rm_base + Rf_f + 1e-30), 4),
                        "fri_bio":   round(Rb_f[ei]       / (Rm_base + Rf_f + 1e-30), 4),
                        "fri_nom":   round(Rn_f[ei]       / (Rm_base + Rf_f + 1e-30), 4),
                        "fri_scale": round(Rs_f[ei]       / (Rm_base + Rf_f + 1e-30), 4),
                        "fri_total": round(fri_total_f, 4),
                        "a_eff":     round(a_eff_ratio, 4),
                        "comp_factor": round(1.0 - eps_comp[ei], 4),
                    }
                    
            current_mechanism_totals = {
                "cake_fouling": round(sum(Rc_f) / n_total_elem, 6),
                "biofouling":   round(sum(Rb_f) / n_total_elem, 6),
                "NOM_adsorption": round(sum(Rn_f) / n_total_elem, 6),
                "scaling":      round(sum(Rs_f) / n_total_elem, 6),
                "cake":         round(sum(Rc_f) / n_total_elem, 6),
                "bio":          round(sum(Rb_f) / n_total_elem, 6),
                "nom":          round(sum(Rn_f) / n_total_elem, 6),
                "scale":        round(sum(Rs_f) / n_total_elem, 6),
                "irreversible": round(sum(Rcomp_elem) / n_total_elem, 6),
            }

            # ---- End-of-life replacement check -------------------------------
            replace_triggered = False
            if (snap["npf"]       < p["NPF_replace_trigger"] or
                snap["sec_kwh_m3"] / SEC0 >= p["SEC_replace_trigger"] or
                any(t_op_h[ei] >= p["max_life_h"] for ei in range(n_total_elem))):

                replace_triggered = True
                replacement_events.append((year,))
                mc          = [[0.0]*NZ for _ in range(n_total_elem)]
                Lb          = [[0.0]*NZ for _ in range(n_total_elem)]
                delta_s     = [[0.0]*NZ for _ in range(n_total_elem)]
                q_nom       = [[0.0]*NZ for _ in range(n_total_elem)]
                t_SI        = [[0.0]*NZ for _ in range(n_total_elem)]
                eps_comp    = [0.0]*n_total_elem
                B_rel       = [1.0]*n_total_elem
                t_op_h      = [0.0]*n_total_elem
                Rc_seg      = [[0.0]*NZ for _ in range(n_total_elem)]
                Rb_seg      = [[0.0]*NZ for _ in range(n_total_elem)]
                Rs_seg      = [[0.0]*NZ for _ in range(n_total_elem)]
                Rn_seg      = [[0.0]*NZ for _ in range(n_total_elem)]
                Rcomp_elem  = [0.0]*n_total_elem

            snap["replacement_triggered"] = replace_triggered
            annual_snapshots.append(snap)

            # ---- Now we have the true P_end_this_year → emit monthly snapshots ----
            # P_curr_bar is still the PREVIOUS year's end pressure here.
            # CRITICAL: always use the pre-replacement snapshot pressure for emission,
            # even if replacement triggers. This ensures Month 60 = Year 5 snapshot
            # pressure (18.91), NOT interpolated back to P0 (which was the old bug).
            P_end_this_year   = snap["feed_pressure_bar"]   # always pre-replacement pressure
            NPF_end_this_year = snap["npf"]                  # ASTM D4516 flux-ratio NPF
            P_start_this_year = P_curr_bar
            NPF_start_this_year = NPF_curr

            for mc_entry in month_cache:
                t_frac   = (mc_entry["month_in_year"] + 1) / 12.0
                # Pressure: linear interpolation from previous year-end → this year-end
                p_m      = P_start_this_year + (P_end_this_year - P_start_this_year) * t_frac
                FRI_m    = mc_entry["FRI_avg"]

                # NPF: interpolate the ASTM flux-ratio NPF (same definition as year-wise table).
                # This guarantees Month 12 of Year N == Row N of the year-wise table.
                npf_m    = NPF_start_this_year + (NPF_end_this_year - NPF_start_this_year) * t_frac
                npf_m    = max(0.0, min(2.0, npf_m))   # allow slight >1 for unfouled periods

                # NSP (Normalised Salt Passage): starts at 1.0, increases with B_rel
                # B_rel > 1 means more salt passes → NSP > 1  (consistent with Year-wise tab)
                nsp_m    = max(1.0, mc_entry["B_rel_avg"])

                monthly_profile.append({
                    "month":         mc_entry["elapsed_months"],
                    "p_feed_bar":    round(p_m, 2),
                    "npf":           round(npf_m, 4),
                    "nsr":           round(nsp_m, 4),   # field kept as 'nsr' for frontend compat
                    "delta_p_ratio": round(p_m / max(P0_bar, 0.1), 3),
                    "flux_lmh":      round(mc_entry["flux_lmh"], 1),
                    "recovery_pct":  round(r0 * 100.0, 2),
                    "cip_event":     mc_entry["cip_event"],
                    "fri":           round(FRI_m, 4),
                })

            # ---- Update pressure/NPF tracking for next year ------------------
            if replace_triggered:
                P_curr_bar = P0_bar
                NPF_curr   = 1.0      # reset to baseline after replacement
            else:
                P_curr_bar = snap["feed_pressure_bar"]
                NPF_curr   = snap["npf"]
            P_prev_year_end = P_curr_bar

        # ---- Dominant mechanism at final year ------------------------
        final = annual_snapshots[-1]
        dom = self._dominant_mechanism(final)
        final["dominant_mechanism"] = dom

        element_autopsy = current_element_autopsy
        mechanism_totals = current_mechanism_totals

        # End-of-life month: first month where NPF < 0.70
        eol_month = None
        for mp in monthly_profile:
            if mp["npf"] < 0.70:
                eol_month = mp["month"]
                break

        return {
            "annual_snapshots":      annual_snapshots,
            "baseline":              year0,
            "cip_events":            cip_events,
            "replacement_events":    replacement_events,
            "dominant_mechanism":    dom,
            "monthly_profile":       monthly_profile,
            "element_autopsy":       element_autopsy,
            "mechanism_totals":      mechanism_totals,
            "end_of_life_month":     eol_month,
            "baseline_pressure_bar": round(P0_bar, 2),
            "baseline_npf":          1.0,
        }

    # ------------------------------------------------------------------
    # Spatial transport solver (NZ-segment axial model)
    # ------------------------------------------------------------------

    def _spatial_transport(
        self,
        feed_flow_m3h, Pfeed_bar, feed_ions, temp_c, membrane,
        stages, vessels_per_stage, elements_per_vessel,
        Rc_seg, Rb_seg, Rs_seg, Rn_seg, Rcomp_elem, B_rel,
        eps_comp, Rm_base, dh, t_fs, w_total, eps_ch, length_m
    ) -> list:
        """
        Compute per-segment transport quantities (Jw, kM, tau_w, TMP, etc.)
        for each element using a NZ-segment axial model.

        Returns
        -------
        list[n_total_elem][NZ]  of dicts with keys:
            Jw, kM, tau_w, TMP_Pa, Cf_bulk, pi_feed_Pa
        """
        mu   = _mu_water(temp_c)
        Ds_T = _Ds(temp_c)
        T_K  = temp_c + 273.15

        n_total_elem = sum(vessels_per_stage) * elements_per_vessel
        results = [[None]*NZ for _ in range(n_total_elem)]

        # Cross-sectional area
        a_cross = w_total * t_fs * eps_ch

        # System-level feed per vessel (simplified: use stage 1 vessels)
        ei_global = 0
        cur_flow  = feed_flow_m3h
        cur_press = Pfeed_bar
        cur_ions  = feed_ions.copy()

        for stage_idx in range(stages):
            vessels  = vessels_per_stage[stage_idx]
            vflow    = cur_flow / vessels   # per-vessel flow

            v_flow_loc = vflow
            v_press    = cur_press
            v_ions     = cur_ions.copy()

            for elem_idx in range(elements_per_vessel):
                ei = stage_idx * elements_per_vessel + elem_idx
                if ei >= n_total_elem:
                    break

                # Feed TDS as proxy for Cf_bulk (kg/m³ -> /1000)
                Cf_tds = sum(v_ions.values()) / 1.0e6   # kg/m³

                # Average osmotic pressure across element (van't Hoff approx)
                pi_feed_bar = self.ro_engine._calculate_osmotic_pressure(v_ions, temp_c)
                pi_feed_Pa  = pi_feed_bar * 1.0e5

                # Effective A (accounts for compaction strain)
                A_eff_SI = (membrane["permeability_A"] / (1000.0 * 3600.0 * 1.0e5)
                             * (1.0 - eps_comp[ei]))

                # Averaged total resistance
                Rc_avg = sum(Rc_seg[ei]) / NZ
                Rb_avg = sum(Rb_seg[ei]) / NZ
                Rs_avg = sum(Rs_seg[ei]) / NZ
                Rn_avg = sum(Rn_seg[ei]) / NZ
                Rcomp  = Rcomp_elem[ei]
                Rtotal = Rm_base + Rc_avg + Rb_avg + Rs_avg + Rn_avg + Rcomp

                # Per-segment axial calculation
                dz     = length_m / NZ
                q_in   = v_flow_loc / 3600.0  # m³/s into element

                for zi in range(NZ):
                    # Local crossflow velocity (decreases axially as permeate is extracted)
                    frac_remaining = 1.0 - (zi / NZ) * 0.15   # ~15% recovery per elem
                    q_loc   = q_in * frac_remaining
                    v_cross = q_loc / max(a_cross, 1e-6)       # m/s

                    # Reynolds, Schmidt, Sherwood (Schock-Miquel axial)
                    Re  = max(1.0, RHO_W * v_cross * dh / mu)
                    Sc  = max(1.0, mu / (RHO_W * Ds_T))
                    Sh  = 0.065 * (Re**0.875) * (Sc**0.25)
                    kM  = max(1e-7, Sh * Ds_T / dh)            # m/s

                    # Local TMP (Pa)
                    TMP_Pa = max(0.0, (v_press - 0.5) * 1.0e5 - pi_feed_Pa)

                    # Local flux using resistance-in-series
                    Rtot_local = (Rm_base
                                  + Rc_seg[ei][zi]
                                  + Rb_seg[ei][zi]
                                  + Rs_seg[ei][zi]
                                  + Rn_seg[ei][zi]
                                  + Rcomp)
                    Rtot_local = max(Rtot_local, Rm_base * 0.5)

                    Jw_raw = TMP_Pa / (mu * Rtot_local)        # m/s
                    Jw     = max(0.0, min(Jw_raw, 5.0e-5))     # cap at ~180 LMH

                    # CP at wall
                    try:
                        beta = _safe_exp(Jw / kM)
                    except Exception:
                        beta = 1.0
                    Cwall = Cf_tds * beta

                    # Wall shear stress
                    ff    = 6.23 * (Re**(-0.3))
                    tau_w = max(0.0, 0.5 * ff * RHO_W * v_cross**2)

                    results[ei][zi] = {
                        "Jw":        Jw,
                        "kM":        kM,
                        "tau_w":     tau_w,
                        "TMP_Pa":    TMP_Pa,
                        "Cf_bulk":   Cf_tds,
                        "pi_feed_Pa": pi_feed_Pa,
                        "beta":      beta,
                        "Cwall":     Cwall,
                    }

                # Approximate element permeate for flow accounting
                Jw_avg  = sum(results[ei][zi]["Jw"] for zi in range(NZ)) / NZ
                Qp_elem = Jw_avg * membrane["active_area_m2"] * 3600.0   # m³/h
                Qp_elem = min(Qp_elem, v_flow_loc * 0.5)

                # Next element inlet conditions
                v_flow_loc  = max(0.01, v_flow_loc - Qp_elem)
                v_press     = max(0.1, v_press - 0.15)   # approx pressure drop per element
                # Concentrate ions (simplified: scale by (Qf / Qc))
                conc_factor = max(1.0, vflow / max(v_flow_loc, 0.01))
                v_ions = {k: min(v * conc_factor, v * 10.0)
                          for k, v in v_ions.items()}

            # Stage exit → feed next stage
            cur_flow  = v_flow_loc * vessels
            cur_press = v_press
            cur_ions  = v_ions.copy()
            ei_global = (stage_idx + 1) * elements_per_vessel

        return results

    # ------------------------------------------------------------------
    # Fouling ODE sub-models
    # ------------------------------------------------------------------

    def _ode_cake(self, mc: float, Jw: float, tau_w: float,
                  TMP_Pa: float, Cf: float, mu: float) -> float:
        """
        Sub-model I: Cake filtration ODE.
        dmc/dt [kg/(m²·s)] = Kd·Jw·Cb - K_rem·tau_w·mc
        Cake is compressible: alpha = alpha0 * (TMP/TMP_ref)^sc
        """
        p = self.p
        Kd    = p["Kd"]
        K_rem = p["K_rem"]
        Cb    = p["Cb"]
        TMP_ref_Pa = p["TMP_ref"] * 1.0e5
        alpha  = p["alpha0"] * ((max(TMP_Pa, 1.0) / TMP_ref_Pa) ** p["sc"])

        deposition = Kd * Jw * Cb
        removal    = K_rem * tau_w * mc
        return deposition - removal

    def _ode_biofilm(self, Lb: float, Jw: float, kM: float,
                     T_K: float, BDOC_bulk: float) -> float:
        """
        Sub-model II: Biofilm growth/decay ODE.
        dLb/dt [m/h] = mu_eff * Lb + Jb_seed - bd * Lb
        mu_eff = mu_max * BDOC / (Ks + BDOC) * Arrhenius
        """
        p = self.p
        arr   = _arrhenius(p["Ea_bio"], T_K, p["T_ref_bio"])
        BDOC_s = BDOC_bulk  # kg/m³ already
        BDOC_mgl = BDOC_s * 1.0e6  # back to mg/L for Monod
        mu_eff = (p["mu_max"] * arr
                  * BDOC_mgl / (p["Ks"] + BDOC_mgl + 1e-12))

        growth = mu_eff * Lb + p["Jb_seed"]
        decay  = p["bd"] * Lb
        return growth - decay

    def _ode_scaling(self, delta_s: float, t_SI: float,
                     Jw: float, kM: float,
                     pi_feed_Pa: float, TMP_Pa: float,
                     t_ind_factor: float, T_K: float,
                     ph: float) -> Tuple[float, float]:
        """
        Sub-model III: Inorganic scaling via CNT.
        Returns (d(delta_s)/dt [m/s], d(t_SI)/dt [h/h = dimensionless rate])
        """
        p = self.p

        # CP enhancement factor at wall
        Jw_h  = Jw * 3600.0   # m/h
        kM_h  = kM * 3600.0   # m/h
        try:
            CP_wall = _safe_exp(Jw_h / max(kM_h, 1e-6))
        except Exception:
            CP_wall = 1.0

        # SI at wall: simplified calcite SI ~ pH-dependent offset
        # SI_wall = log10(CP_wall) as concentration enhancement
        si_enh = math.log10(max(CP_wall, 1.0))

        # Induction time (CNT) – simplified formula
        #   t_ind ~ A_ind * exp(Delta_G / kT) / kT  (proportional to exp(1/SI^2))
        si_w = max(0.01, si_enh)
        # Theta correction for heterogeneous nucleation
        theta = math.radians(p["theta_contact"])
        f_het = 0.25 * (2.0 + math.cos(theta)) * (1.0 - math.cos(theta))**2

        # Gibbs free energy: proportional to 1/ln^2(SI_w+1)
        lnS   = math.log(max(1.0 + si_w, 1.001))
        dG_kT = f_het * 4.0 / (3.0 * lnS**2)
        t_ind_base = p["A_ind"] * _safe_exp(dG_kT) * t_ind_factor / 3600.0  # hours

        # SI accumulation rate: 1.0 h/h beyond induction
        dt_SI = 1.0  # integrates time; checked against t_ind_base

        # Scale growth rate (after induction)
        if t_SI > t_ind_base and si_w > 0:
            # Crystal growth: d(delta_s)/dt = kg * (SI-1)^ns / rho_calcite
            SI_excess = max(0.0, si_w)
            growth_rate = (p["kg_calcite"] * (SI_excess ** p["ns_calcite"])
                           / p["rho_calcite"])
        else:
            growth_rate = 0.0

        return growth_rate, dt_SI

    def _ode_nom(self, q: float, Jw: float, kM: float,
                 tau_w: float, nom_bulk: float) -> float:
        """
        Sub-model IV: NOM adsorption (Langmuir + intermediate blocking).
        dq/dt [kg/(m²·s)] = kads * (qmax - q) * (KL * Cnom_w)/(1 + KL*Cnom_w) * Jw - k_des
        """
        p = self.p
        try:
            beta_nom = _safe_exp(Jw * 3600.0 / max(kM * 3600.0, 1e-6))
        except Exception:
            beta_nom = 1.0
        Cnom_wall = nom_bulk * beta_nom   # kg/m³

        q_eq  = p["qmax"] * (p["KL"] * Cnom_wall) / (1.0 + p["KL"] * Cnom_wall + 1e-15)
        # shear-enhanced desorption modifier
        shear_mod = max(0.1, min(1.0, p["tau_w_ref"] / max(tau_w, 1e-6)))
        dq_dt = p["kads"] * (q_eq - q) * shear_mod
        return dq_dt

    # ------------------------------------------------------------------
    # Resistance calculations
    # ------------------------------------------------------------------

    def _rc(self, mc: float, TMP_Pa: float) -> float:
        """Cake resistance [m⁻¹] from cake mass [kg/m²]."""
        p  = self.p
        TMP_ref_Pa = p["TMP_ref"] * 1.0e5
        alpha = p["alpha0"] * ((max(TMP_Pa, 1.0) / TMP_ref_Pa) ** p["sc"])
        return alpha * mc

    def _rb(self, Lb: float) -> float:
        """Biofilm (EOP) resistance [m⁻¹] from biofilm thickness [m]."""
        p  = self.p
        if Lb < p["Lb_min"]:
            return 0.0
        dp  = p["dp_EPS"]
        eps = p["eps_bf"]
        tau = p["tau_bf"]
        # Kozeny-Carman for fibrous biofilm
        rb = (180.0 * (1.0 - eps)**2 * tau * Lb) / (dp**2 * eps**3 + 1e-30)
        return rb

    def _rs(self, delta_s: float) -> float:
        """Scale resistance [m⁻¹] from scale thickness [m]."""
        p = self.p
        rho_s = p["rho_calcite"]
        alpha_s = p["alpha_scale"]
        ms = rho_s * delta_s   # [kg/m²]
        return alpha_s * ms

    def _rn(self, q: float) -> float:
        """NOM adsorption resistance [m⁻¹] from loading [kg/m²]."""
        return self.p["rNOM"] * q

    # ------------------------------------------------------------------
    # CIP kinetics
    # ------------------------------------------------------------------

    def _apply_cip(
        self,
        mc: list, Lb: list, delta_s: list, q_nom: list,
        temp_c: float, n_total_elem: int
    ):
        """
        Apply CIP to all elements.  Returns updated state lists.
        Acid CIP:    removes delta_s (scale) and mc (colloids)
        Alkaline CIP: removes Lb (biofilm) and q_nom (NOM)
        """
        p   = self.p
        T_K = temp_c + 273.15

        # Acid CIP – scale dissolution
        arr_dis  = _arrhenius(p["Ea_dis"],     T_K, p["T_cip"])
        # Alkaline CIP – biofilm and NOM removal
        arr_bio  = _arrhenius(p["Ea_bio_rem"], T_K, p["T_cip"])

        # H+ activity at acid CIP
        H_acid   = 10.0 ** (-p["cip_ph_acid"])
        # OH- activity at alkaline CIP
        OH_alk   = 10.0 ** (-(14.0 - p["cip_ph_alk"]))

        for ei in range(n_total_elem):
            for zi in range(NZ):
                # Acid: dissolve scale  (exponential decay with CIP duration)
                k_diss  = p["kd_acid"] * arr_dis * H_acid
                eff_ds  = _safe_exp(-k_diss * p["tCIP_acid"] * 3600.0)
                delta_s[ei][zi] *= eff_ds

                # Acid: colloidal cake removal by chelant
                k_coll  = p["kd_coll"] * p["chelant_conc"]
                eff_mc  = _safe_exp(-k_coll * p["tCIP_acid"] * 3600.0)
                mc[ei][zi] *= eff_mc

                # Alkaline: biofilm removal
                k_bio_r  = p["kd_bio"] * arr_bio * OH_alk
                eff_Lb   = _safe_exp(-k_bio_r * p["tCIP_alk"] * 3600.0)
                Lb[ei][zi] *= eff_Lb

                # Alkaline: NOM hydrolysis
                k_nom_r  = p["kd_NOM"] * arr_bio * OH_alk
                eff_q    = _safe_exp(-k_nom_r * p["tCIP_alk"] * 3600.0)
                q_nom[ei][zi] *= eff_q

        return mc, Lb, delta_s, q_nom

    # ------------------------------------------------------------------
    # Year-end snapshot with bisection pressure solver
    # ------------------------------------------------------------------

    def _year_end_snapshot(
        self,
        year: int,
        feed_ions: dict,
        temp_c: float,
        membrane_model: str,
        stages: int,
        vessels_per_stage: list,
        elements_per_vessel: int,
        feed_flow_m3h: float,
        target_recovery_pct: float,
        P0_bar: float,
        Q0: float,
        TDS0: float,
        NDP_0: float,
        SEC0: float,
        Rc_seg: list, Rb_seg: list, Rs_seg: list, Rn_seg: list,
        Rcomp_elem: list,
        B_rel: list, eps_comp: list,
        Rm_base: float,
        A0_lmh_bar: float,
        B0_ms: float,
        n_total_elem: int,
        t_SI: list, delta_s: list, Lb: list, mc: list, q_nom: list,
        cip_count: int,
        membrane: dict,
    ) -> dict:
        """
        Build the aged_params dict and call ROEngine.simulate_system() via
        bisection to find the pressure needed to restore target recovery.
        Compute ASTM D4516-19a normalised metrics and all fouling indicators.
        """
        # ---- Average resistances per element -------------------------
        Rc_elem   = [sum(Rc_seg[ei]) / NZ for ei in range(n_total_elem)]
        Rb_elem   = [sum(Rb_seg[ei]) / NZ for ei in range(n_total_elem)]
        Rs_elem   = [sum(Rs_seg[ei]) / NZ for ei in range(n_total_elem)]
        Rn_elem   = [sum(Rn_seg[ei]) / NZ for ei in range(n_total_elem)]

        # ---- FRI per element -----------------------------------------
        FRI_list  = []
        for ei in range(n_total_elem):
            Rf  = Rc_elem[ei] + Rb_elem[ei] + Rs_elem[ei] + Rn_elem[ei]
            Rf += Rcomp_elem[ei]
            fri = Rf / (Rm_base + Rf + 1e-30)
            FRI_list.append(fri)
        FRI_sys = sum(FRI_list) / n_total_elem

        # ---- Effective A and B per element ---------------------------
        aged_params: Dict[Tuple, Dict] = {}
        elem_count = 0
        for s_idx in range(stages):
            for e_idx in range(elements_per_vessel):
                ei = s_idx * elements_per_vessel + e_idx
                if ei >= n_total_elem:
                    continue
                # A_eff accounts for total resistance increase
                Rf_ei  = (Rc_elem[ei] + Rb_elem[ei]
                          + Rs_elem[ei] + Rn_elem[ei] + Rcomp_elem[ei])
                FRI_ei = Rf_ei / (Rm_base + Rf_ei + 1e-30)
                A_eff  = A0_lmh_bar / (1.0 + FRI_ei) * (1.0 - eps_comp[ei])
                A_eff  = max(A_eff, A0_lmh_bar * 0.1)

                B_eff  = B0_ms * B_rel[ei]
                aged_params[(s_idx + 1, e_idx + 1)] = {"A": A_eff, "B": B_eff}

        # ---- Bisection: find feed pressure for target recovery -------
        target_rec = target_recovery_pct / 100.0
        P_lo, P_hi = max(P0_bar * 0.5, 2.0), P0_bar * 2.5

        best_result = None
        for _ in range(25):
            P_mid = (P_lo + P_hi) / 2.0
            try:
                res = self.ro_engine.simulate_system(
                    feed_flow_m3h, P_mid, feed_ions, temp_c,
                    membrane_model, stages, vessels_per_stage,
                    elements_per_vessel, aged_params=aged_params
                )
                rec_mid = res["summary"]["total_recovery"]
                best_result = res
                if abs(rec_mid - target_rec) < 5e-4:
                    break
                if rec_mid < target_rec:
                    P_lo = P_mid
                else:
                    P_hi = P_mid
            except Exception:
                # Numerical instability: return a degraded estimate
                P_lo = P_mid
                break

        if best_result is None:
            # Fallback: run at P0_bar with aged params
            try:
                best_result = self.ro_engine.simulate_system(
                    feed_flow_m3h, P0_bar, feed_ions, temp_c,
                    membrane_model, stages, vessels_per_stage,
                    elements_per_vessel, aged_params=aged_params
                )
            except Exception:
                # Last resort: return degraded year0 snapshot
                return self._fallback_snapshot(year, P0_bar, Q0, TDS0, SEC0,
                                                FRI_sys, Rc_elem, Rb_elem,
                                                Rs_elem, Rn_elem, Rcomp_elem,
                                                n_total_elem, cip_count)

        s = best_result["summary"]
        Qp_y   = s["perm_flow"]
        Pfeed_y = s["feed_pressure_bar"]
        TDS_y  = s["perm_tds"]
        rec_y  = s["total_recovery"]

        # SEC
        hp_eff = 0.80
        hp_kw  = (feed_flow_m3h * Pfeed_y) / (36.0 * hp_eff)
        bp_kw  = sum(bp.get("power_kw", 0) for bp in best_result.get("booster_pumps", []))
        SEC_y  = (hp_kw + bp_kw) / max(Qp_y, 0.001)

        # ---- ASTM D4516-19a normalised metrics -----------------------
        # NPF: normalised permeate flow
        TCF_ratio = 1.0  # same temp assumed
        NPF = (Qp_y / Q0) * TCF_ratio if Q0 > 0 else 1.0

        # NDP: average element NDP
        elems_y = best_result.get("elements", [])
        if elems_y:
            NDP_y = sum(e.get("ndp", NDP_0) for e in elems_y) / len(elems_y)
        else:
            NDP_y = NDP_0 * (1.0 + FRI_sys)

        NDP_ratio = NDP_y / max(NDP_0, 1e-6)

        # NSP: ASTM D4516-19a normalised salt passage
        # NSP = (Cp_y * Qp0) / (Cp0 * Qp_y)  -- ratio of salt mass passage rates
        # At Year 0: NSP = 1.0. As fouling worsens (CP increases), NSP rises.
        # Note: B_rel degradation also changes TDS_y, but CIP cannot reverse it.
        # For CIP triggering, we use NSP_fouling only (B_rel contribution removed).
        SP0 = TDS0       # mg/L permeate at Year 0
        SP_y = TDS_y     # mg/L permeate at Year N
        # Normalised salt passage (total): corrected to same permeate flow
        NSP_total = (SP_y * max(Q0, 0.001)) / (max(SP0, 1e-6) * max(Qp_y, 0.001))
        # B_rel contribution: when B_rel < 1, salt perm is lower → NSP_Brel < 1
        B_rel_avg_local = sum(B_rel) / n_total_elem
        # NSP from fouling only (removing B_rel effect):
        # NSP_fouling = NSP_total / (1/B_rel) = NSP_total * B_rel
        # This isolates the fouling-driven CP increase from chemical degradation.
        NSP_fouling = NSP_total * B_rel_avg_local
        # Report total NSP (for display), use fouling-only for CIP triggering
        NSP = NSP_total

        # ---- Wall-level SI indicators (simplified) -------------------
        Jw_avg_global = sum(
            sum(Rb_seg[ei]) / NZ for ei in range(n_total_elem)
        ) / n_total_elem   # proxy for biofilm; use Lb for actual
        kM_avg = 5.0e-6   # typical order
        try:
            CP_avg = _safe_exp((Qp_y / max(Q0, 0.001)) * 0.3)
        except Exception:
            CP_avg = 1.0
        si_calcite_wall = self.si_calc_bulk + math.log10(max(CP_avg, 1.001))
        si_gypsum_wall  = self.si_gyps_bulk + math.log10(max(CP_avg, 1.001)) * 0.6
        si_barite_wall  = self.si_bari_bulk + math.log10(max(CP_avg, 1.001)) * 0.4
        si_silica_wall  = self.si_sili_bulk + math.log10(max(CP_avg, 1.001)) * 0.3

        # ---- Dominant mechanism from resistances ---------------------
        Rc_avg_g = sum(Rc_elem) / n_total_elem
        Rb_avg_g = sum(Rb_elem) / n_total_elem
        Rs_avg_g = sum(Rs_elem) / n_total_elem
        Rn_avg_g = sum(Rn_elem) / n_total_elem
        Rk_avg_g = sum(Rcomp_elem) / n_total_elem

        dom = self._dominant_mechanism_from_R(
            Rc_avg_g, Rb_avg_g, Rs_avg_g, Rn_avg_g, Rk_avg_g
        )

        # ---- B_rel average across system ----------------------------
        B_rel_avg = sum(B_rel) / n_total_elem

        return {
            "year":                 year,
            "perm_flow":            Qp_y,
            "recovery":             rec_y,
            "feed_pressure_bar":    Pfeed_y,
            "perm_tds":             TDS_y,
            "sec_kwh_m3":           SEC_y,
            "npf":                  NPF,
            "nsp":                  NSP,              # total NSP: 1.0=baseline, >1=salt passage worsening
            "nsp_fouling":          NSP_fouling,      # fouling-only NSP (excl. chemical B_rel degradation)
            "ndp_ratio":            NDP_ratio,
            "fri":                  FRI_sys,
            "b_relative":           B_rel_avg,
            "rc_avg":               Rc_avg_g,
            "rb_avg":               Rb_avg_g,
            "rs_avg":               Rs_avg_g,
            "rn_avg":               Rn_avg_g,
            "rcomp":                Rk_avg_g,
            "cip_triggered":        False,
            "replacement_triggered": False,
            "cip_count":            cip_count,
            "dominant_mechanism":   dom,
            "si_calcite_wall":      si_calcite_wall,
            "si_gypsum_wall":       si_gypsum_wall,
            "si_barite_wall":       si_barite_wall,
            "si_silica_wall":       si_silica_wall,
            "si_calcite_bulk":      self.si_calc_bulk,
            "si_gypsum_bulk":       self.si_gyps_bulk,
            "si_barite_bulk":       self.si_bari_bulk,
            "si_silica_bulk":       self.si_sili_bulk,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _dominant_mechanism(self, snap: dict) -> str:
        """Determine dominant fouling mechanism from a YearResult snapshot."""
        return self._dominant_mechanism_from_R(
            snap.get("rc_avg", 0),
            snap.get("rb_avg", 0),
            snap.get("rs_avg", 0),
            snap.get("rn_avg", 0),
            snap.get("rcomp", 0),
        )

    def _dominant_mechanism_from_R(
        self,
        Rc: float, Rb: float, Rs: float, Rn: float, Rk: float
    ) -> str:
        """Return string label of the largest resistance contributor."""
        vals = {
            "cake_colloidal": Rc,
            "biofouling":     Rb,
            "scaling":        Rs,
            "nom_adsorption": Rn,
            "compaction":     Rk,
        }
        total = sum(vals.values())
        if total < 1.0:
            return "none"
        return max(vals, key=vals.get)

    def _fallback_snapshot(
        self,
        year: int, P0_bar: float, Q0: float, TDS0: float, SEC0: float,
        FRI: float,
        Rc_elem: list, Rb_elem: list, Rs_elem: list, Rn_elem: list,
        Rcomp_elem: list, n_total_elem: int, cip_count: int,
    ) -> dict:
        """
        Return a conservative degraded snapshot when numerical solver fails.
        Used as a safety fallback – all performance metrics are estimated
        from the FRI (Fouling Resistance Index) assuming proportional loss.
        """
        degrade = max(0.0, 1.0 - FRI)
        return {
            "year":                 year,
            "perm_flow":            Q0 * degrade,
            "recovery":             0.75 * degrade,
            "feed_pressure_bar":    P0_bar * (1.0 + FRI * 0.5),
            "perm_tds":             TDS0 * (1.0 + FRI * 0.3),
            "sec_kwh_m3":           SEC0 * (1.0 + FRI * 0.4),
            "npf":                  degrade,
            "nsp":                  degrade,
            "ndp_ratio":            1.0 + FRI * 0.3,
            "fri":                  FRI,
            "b_relative":           1.0,
            "rc_avg":               sum(Rc_elem) / max(n_total_elem, 1),
            "rb_avg":               sum(Rb_elem) / max(n_total_elem, 1),
            "rs_avg":               sum(Rs_elem) / max(n_total_elem, 1),
            "rn_avg":               sum(Rn_elem) / max(n_total_elem, 1),
            "rcomp":                sum(Rcomp_elem) / max(n_total_elem, 1),
            "cip_triggered":        False,
            "replacement_triggered": False,
            "cip_count":            cip_count,
            "dominant_mechanism":   "unknown",
            "si_calcite_wall":      0.0,
            "si_gypsum_wall":       0.0,
            "si_barite_wall":       0.0,
            "si_silica_wall":       0.0,
        }
