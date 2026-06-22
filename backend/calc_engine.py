"""
RO/NF Element-wise Calculation Engine
Implements Solution-Diffusion and Spiegler-Kedem mass transport models.
"""

import math
from typing import Dict, List, Any
from membrane_database import MembraneDatabase

class ROEngine:
    def __init__(self):
        # Universal constants
        self.R_gas = 0.08314 # L*bar/(mol*K)
        
        self.MM = {
            "Ca": 40.078, "Mg": 24.305, "Na": 22.990, "K": 39.098,
            "Cl": 35.45, "SO4": 96.06, "HCO3": 61.0168, "Ba": 137.327,
            "Sr": 87.62, "F": 18.998, "SiO2": 60.08, "B": 10.81,
            "NO3": 62.00, "PO4": 94.97, "NH4": 18.04,
            "Al": 26.982, "Fe": 55.845, "Mn": 54.938
        }
        
    def _calculate_osmotic_pressure(self, ions: Dict[str, float], temp_c: float) -> float:
        """
        Calculates osmotic pressure (bar) using van't Hoff equation with a simple
        osmotic coefficient assumption for mixed electrolytes.
        ions: concentration in mg/L
        """
        temp_k = temp_c + 273.15
        total_molarity = 0.0
        
        for ion, conc_mg_l in ions.items():
            if ion in self.MM and conc_mg_l > 0:
                molarity = (conc_mg_l / 1000.0) / self.MM[ion]
                total_molarity += molarity
                
        # Calculate total TDS to determine dynamic osmotic coefficient (phi)
        tds = sum(ions.values())
        if tds >= 35000:
            phi = 0.90
        elif tds > 10000:
            # Interpolate between 10000 (0.93) and 35000 (0.90)
            phi = 0.93 - ((tds - 10000) / 25000.0) * 0.03
        elif tds > 1000:
            phi = 0.93
        elif tds > 500:
            phi = 0.95
        elif tds > 100:
            # Interpolate between 100 (0.98) and 500 (0.95)
            phi = 0.98 - ((tds - 100) / 400.0) * 0.03
        else:
            phi = 1.0
            
        pi = total_molarity * self.R_gas * temp_k * phi
        return pi
        
    def _calculate_tcf(self, temp_c: float) -> float:
        """Temperature Correction Factor for water permeability"""
        temp_k = temp_c + 273.15
        # Exponent selections based on temperature reference:
        # U = 2640 for T <= 25°C, U = 3020 for T > 25°C
        U = 2640.0 if temp_c <= 25.0 else 3020.0
        return math.exp(U * (1.0/298.0 - 1.0/temp_k))
        
    def _calculate_cp_beta(self, flux_lmh: float, feed_flow_m3h: float, conc_flow_m3h: float, temp_c: float, membrane: Dict[str, Any]) -> float:
        """
        Calculate Concentration Polarization factor (Beta = Cm/Cb) using film theory and the Schock-Miquel mass transfer correlation:
        Sh = 0.04 * Re^0.75 * Sc^0.33
        k = Sh * D_AB / d_h
        """
        # Average volumetric flow rate in m3/h -> m3/s
        avg_flow_m3h = max(0.001, (feed_flow_m3h + conc_flow_m3h) / 2.0)
        avg_flow_m3s = avg_flow_m3h / 3600.0

        # Spacer geometry properties
        spacer_mil = membrane.get("feed_spacer_mil", 34)
        t_fs = spacer_mil * 2.54e-5 # spacer thickness in meters
        d_h = 2.0 * t_fs
        
        # Unrolled feed channel width W (m) approximated from active area and element length
        area_m2 = membrane.get("active_area_m2", 37.2)
        length_m = membrane.get("length_m", 1.016)
        w_total = area_m2 / (2.0 * length_m)
        
        # Cross-sectional flow area (assuming void fraction epsilon = 0.90)
        epsilon = 0.90
        a_cross = w_total * t_fs * epsilon
        
        # Linear cross-flow velocity v (m/s)
        v = avg_flow_m3s / a_cross if a_cross > 0 else 0.1
        
        # Water dynamic viscosity mu_T (Pa*s) at temperature temp_c
        mu_T = 1.0e-3 * math.exp(1808.0 / (temp_c + 273.15) - 6.354)
        rho = 1000.0
        nu = mu_T / rho
        
        # Reynolds number Re
        Re = (d_h * v) / nu if nu > 0 else 100.0
        
        # Diffusivity of solute (m2/s) corrected for temperature using Stokes-Einstein
        mu_25 = 1.0e-3 * math.exp(1808.0 / 298.15 - 6.354)
        D_AB_25 = 1.6e-9 # m2/s
        D_AB = D_AB_25 * (temp_c + 273.15) / 298.15 * (mu_25 / mu_T)
        
        # Schmidt number Sc
        Sc = nu / D_AB if D_AB > 0 else 600.0
        
        # Sherwood number Sh
        Sh = 0.04 * math.pow(Re, 0.75) * math.pow(Sc, 0.33)
        
        # Mass transfer coefficient k (m/s)
        k = Sh * D_AB / d_h
        
        # Water flux Jv in m/s
        jv_ms = (flux_lmh / 1000.0) / 3600.0
        
        # Polarization factor Beta
        if k > 0:
            beta = math.exp(jv_ms / k)
        else:
            beta = 1.0
            
        return beta

    def _calculate_pressure_drop(self, feed_flow_m3h: float, conc_flow_m3h: float, temp_c: float, membrane: Dict[str, Any]) -> float:
        """
        Calculate pressure drop per element (bar) using the Schock-Miquel friction correlation:
        dp = lambda * (L / d_h) * (rho * v^2 / 2)
        lambda = 6.23 * Re^-0.3
        """
        avg_flow_m3h = max(0.001, (feed_flow_m3h + conc_flow_m3h) / 2.0)
        avg_flow_m3s = avg_flow_m3h / 3600.0

        spacer_mil = membrane.get("feed_spacer_mil", 34)
        t_fs = spacer_mil * 2.54e-5 # spacer thickness in meters
        d_h = 2.0 * t_fs
        
        area_m2 = membrane.get("active_area_m2", 37.2)
        length_m = membrane.get("length_m", 1.016)
        w_total = area_m2 / (2.0 * length_m)
        
        epsilon = 0.90
        a_cross = w_total * t_fs * epsilon
        
        v = avg_flow_m3s / a_cross if a_cross > 0 else 0.1
        
        mu_T = 1.0e-3 * math.exp(1808.0 / (temp_c + 273.15) - 6.354)
        rho = 1000.0
        nu = mu_T / rho
        Re = (d_h * v) / nu if nu > 0 else 100.0
        
        friction_factor = 6.23 * math.pow(Re, -0.3)
        dp_pa = friction_factor * (length_m / d_h) * (rho * v**2 / 2.0)
        dp_bar = dp_pa / 100000.0
        
        return max(0.001, min(dp_bar, 1.5))


    def simulate_element(self, 
                         feed_flow_m3h: float, 
                         feed_pressure_bar: float,
                         feed_ions: Dict[str, float],
                         temp_c: float,
                         membrane: Dict[str, Any],
                         element_idx: int) -> Dict[str, Any]:
        """
        Simulate a single RO/NF element performance.
        Self-consistent mass-balanced solver for flux and permeate concentration.
        """
        # Initial guesses
        recovery = 0.10
        perm_flow_m3h = feed_flow_m3h * recovery
        conc_flow_m3h = feed_flow_m3h - perm_flow_m3h
        
        A = membrane["permeability_A"]
        B = membrane["permeability_B"]
        area = membrane["active_area_m2"]
        sigmas = membrane.get("sigma", {})
        
        tcf = self._calculate_tcf(temp_c)
        
        # Iterative loop to converge on permeate flow and pressure
        max_iter = 20
        tolerance = 0.001
        
        current_perm_flow = perm_flow_m3h
        
        # We will compute these in the loop
        perm_ions = {}
        rej_ions = {}
        beta_actual = 1.0
        ndp = 0.0
        dp = 0.0
        
        for i in range(max_iter):
            # Estimate permeate flow -> flux
            flux_lmh = (current_perm_flow * 1000.0) / area
            
            # Calculate CP Beta
            beta_actual = self._calculate_cp_beta(flux_lmh, feed_flow_m3h, conc_flow_m3h, temp_c, membrane)
            beta_calc = min(beta_actual, 1.25)
            
            # Ratio r = Qp / (2 * Qc)
            r = current_perm_flow / (2.0 * max(0.001, feed_flow_m3h - current_perm_flow))
            
            # Calculate concentrations self-consistently
            surface_ions = {}
            loop_perm_ions = {}
            
            for ion, feed_c in feed_ions.items():
                if feed_c <= 0:
                    loop_perm_ions[ion] = 0.0
                    surface_ions[ion] = 0.0
                    continue
                    
                sigma = sigmas.get(ion, 0.99)
                P_s_ms = B * (1.0 - sigma) / 0.01 
                P_s_mh = P_s_ms * 3600.0
                
                jv_mh = flux_lmh / 1000.0
                
                # Spiegler-Kedem Rejection (True Rejection)
                if jv_mh > 0 and P_s_mh > 0:
                    exponent = - (jv_mh * (1 - sigma)) / P_s_mh
                    try:
                        exp_val = math.exp(exponent)
                        F_i = (1 - sigma) / (1 - sigma * exp_val)
                        R_true = 1.0 - F_i
                    except OverflowError:
                        R_true = sigma
                else:
                    R_true = 0.0
                    
                # Self-consistent calculations:
                denom = R_true + beta_calc * (1.0 - R_true)
                F_factor = (beta_calc * (1.0 - R_true)) / denom if denom > 0 else 0.0
                
                # Cp = feed_c * F_factor * (1 + r) / (1 + F_factor * r)
                Cp = feed_c * (F_factor * (1.0 + r)) / (1.0 + F_factor * r)
                
                # Cb = feed_c * (1 + r) / (1 + F_factor * r)
                bulk_c = feed_c * (1.0 + r) / (1.0 + F_factor * r)
                
                # Cm = bulk_c * beta_calc / denom
                Cm = bulk_c * beta_calc / denom if denom > 0 else bulk_c * beta_calc
                
                loop_perm_ions[ion] = Cp
                surface_ions[ion] = Cm
                
            # Osmotic pressure at surface and permeate
            pi_surface = self._calculate_osmotic_pressure(surface_ions, temp_c)
            pi_perm = self._calculate_osmotic_pressure(loop_perm_ions, temp_c)
            delta_pi = max(0.0, pi_surface - pi_perm)
            
            # Pressure drop across element (Schock-Miquel friction correlation)
            dp = self._calculate_pressure_drop(feed_flow_m3h, conc_flow_m3h, temp_c, membrane)
            
            avg_feed_pressure = feed_pressure_bar - dp/2.0
            if avg_feed_pressure < 1.0:
                avg_feed_pressure = 1.0
                
            perm_pressure = 0.5
            
            # Net Driving Pressure
            ndp = avg_feed_pressure - perm_pressure - delta_pi
            if ndp < 0:
                ndp = 0
                
            # Calculate new flux
            new_flux_lmh = A * ndp * tcf
            new_perm_flow = (new_flux_lmh * area) / 1000.0
            
            # Update flows
            old_perm_flow = current_perm_flow
            current_perm_flow = 0.7 * current_perm_flow + 0.3 * new_perm_flow
            
            if current_perm_flow > 0.99 * feed_flow_m3h:
                current_perm_flow = 0.99 * feed_flow_m3h
                
            conc_flow_m3h = feed_flow_m3h - current_perm_flow
            
            # Keep track of the final concentrations
            perm_ions = loop_perm_ions
            
            if abs(new_perm_flow - old_perm_flow) < tolerance:
                break
                
        # Final flow state
        perm_flow_m3h = current_perm_flow
        flux_lmh = (perm_flow_m3h * 1000.0) / area
        element_recovery = perm_flow_m3h / feed_flow_m3h
        
        # Final reject concentrations via mass balance
        for ion in feed_ions.keys():
            if feed_flow_m3h > 0 and conc_flow_m3h > 0:
                mass_in = feed_flow_m3h * feed_ions[ion]
                mass_perm = perm_flow_m3h * perm_ions[ion]
                rej_c = (mass_in - mass_perm) / conc_flow_m3h
                rej_ions[ion] = max(0.0, rej_c)
            else:
                rej_ions[ion] = 0.0
                
        return {
            "element_idx": element_idx,
            "feed_flow": feed_flow_m3h,
            "perm_flow": perm_flow_m3h,
            "conc_flow": conc_flow_m3h,
            "feed_pressure": feed_pressure_bar,
            "conc_pressure": feed_pressure_bar - dp,
            "dp": dp,
            "flux": flux_lmh,
            "ndp": ndp,
            "beta": beta_actual,
            "recovery": element_recovery,
            "feed_ions": feed_ions,
            "perm_ions": perm_ions,
            "rej_ions": rej_ions
        }

    def simulate_system(self,
                        feed_flow_m3h: float,
                        feed_pressure_bar: float,
                        feed_ions: Dict[str, float],
                        temp_c: float,
                        membrane_model: str,
                        stages: int,
                        vessels_per_stage: List[int],
                        elements_per_vessel: int) -> Dict[str, Any]:
        """
        Simulate an entire RO/NF array with interstage booster pump calculations.
        vessels_per_stage: e.g., [4, 2] for a 2-stage system
        """
        membrane = MembraneDatabase.get_ro_membrane(membrane_model)
        
        system_results = {
            "stages": [],
            "elements": [],
            "booster_pumps": [],
            "warnings": []
        }
        
        current_feed_flow = feed_flow_m3h
        current_feed_pressure = feed_pressure_bar
        current_ions = feed_ions.copy()
        
        total_perm_flow = 0.0
        total_perm_mass = {k: 0.0 for k in feed_ions.keys()}
        total_booster_power_kw = 0.0
        
        for stage_idx in range(stages):
            vessels = vessels_per_stage[stage_idx] if stage_idx < len(vessels_per_stage) else 1
            
            # Flow per vessel
            vessel_feed_flow = current_feed_flow / vessels
            
            stage_perm_flow = 0.0
            stage_perm_mass = {k: 0.0 for k in feed_ions.keys()}
            
            vessel_current_flow = vessel_feed_flow
            vessel_current_pressure = current_feed_pressure
            vessel_current_ions = current_ions.copy()
            
            for elem_idx in range(elements_per_vessel):
                global_elem_idx = stage_idx * elements_per_vessel + elem_idx + 1
                
                # Check limits
                if vessel_current_flow > membrane["max_feed_flow_m3h"]:
                    system_results["warnings"].append({
                        "type": f"Feed Flow > Max (S{stage_idx+1}-E{elem_idx+1})",
                        "element": f"S{stage_idx+1}-E{elem_idx+1}",
                        "limit": membrane["max_feed_flow_m3h"],
                        "value": vessel_current_flow
                    })
                
                if vessel_current_flow < membrane["min_conc_flow_m3h"]:
                     system_results["warnings"].append({
                        "type": f"Flow < Min Conc Flow (S{stage_idx+1}-E{elem_idx+1})",
                        "element": f"S{stage_idx+1}-E{elem_idx+1}",
                        "limit": membrane["min_conc_flow_m3h"],
                        "value": vessel_current_flow
                    })

                res = self.simulate_element(
                    vessel_current_flow, vessel_current_pressure, vessel_current_ions,
                    temp_c, membrane, global_elem_idx
                )
                
                # Check feed pressure limit
                if vessel_current_pressure > membrane.get("max_pressure_bar", 41.0):
                    system_results["warnings"].append({
                        "type": f"Feed Pressure > Max (S{stage_idx+1}-E{elem_idx+1})",
                        "element": f"S{stage_idx+1}-E{elem_idx+1}",
                        "limit": membrane["max_pressure_bar"],
                        "value": vessel_current_pressure
                    })
                    
                # Check element recovery limit
                elem_rec_pct = res["recovery"] * 100.0
                if elem_rec_pct > membrane.get("max_recovery_pct", 15.0):
                    system_results["warnings"].append({
                        "type": f"Element Recovery > Max (S{stage_idx+1}-E{elem_idx+1})",
                        "element": f"S{stage_idx+1}-E{elem_idx+1}",
                        "limit": membrane["max_recovery_pct"],
                        "value": elem_rec_pct
                    })

                # Check Concentration Polarization limit (beta >= 1.20)
                beta_val = res["beta"]
                if beta_val >= 1.20:
                    system_results["warnings"].append({
                        "type": f"Polarization Beta > 1.20 (S{stage_idx+1}-E{elem_idx+1})",
                        "element": f"S{stage_idx+1}-E{elem_idx+1}",
                        "limit": 1.20,
                        "value": beta_val
                    })
                
                # Element-wise results scaled up by number of vessels in stage for system view
                elem_sys_view = res.copy()
                elem_sys_view["stage"] = stage_idx + 1
                elem_sys_view["position"] = elem_idx + 1
                
                system_results["elements"].append(elem_sys_view)
                
                # Accumulate permeate
                stage_perm_flow += res["perm_flow"] * vessels
                for ion in current_ions.keys():
                    stage_perm_mass[ion] += res["perm_ions"][ion] * res["perm_flow"] * vessels
                    
                # Setup next element in series
                vessel_current_flow = res["conc_flow"]
                vessel_current_pressure = res["conc_pressure"]
                vessel_current_ions = res["rej_ions"].copy()
                
            # Stage completed. Capture exit conditions before inter-stage transition
            stage_exit_pressure = vessel_current_pressure
            stage_exit_flow = vessel_current_flow * vessels  # Total concentrate flow from all vessels
            stage_exit_ions = vessel_current_ions.copy()
            
            # Accumulate to system total
            total_perm_flow += stage_perm_flow
            for ion in current_ions.keys():
                total_perm_mass[ion] += stage_perm_mass[ion]
                
            system_results["stages"].append({
                "stage": stage_idx + 1,
                "feed_flow": vessel_feed_flow * vessels,
                "perm_flow": stage_perm_flow,
                "conc_flow": stage_exit_flow,
                "recovery": stage_perm_flow / (vessel_feed_flow * vessels)
            })
            
            # --- INTERSTAGE BOOSTER PUMP CALCULATION ---
            if stage_idx < stages - 1:
                # Calculate osmotic pressure of the concentrate leaving this stage
                pi_conc = self._calculate_osmotic_pressure(stage_exit_ions, temp_c)
                
                # Required feed pressure for the next stage:
                # Need enough NDP to maintain balanced flux across stages.
                # Target NDP: set to average NDP of the preceding stage.
                stage_elements = [el for el in system_results["elements"] if el["stage"] == stage_idx + 1]
                avg_stage_ndp = sum(el["ndp"] for el in stage_elements) / len(stage_elements) if stage_elements else 1.0
                target_ndp = max(0.5, avg_stage_ndp) # ensure at least positive NDP
                
                permeate_backpressure = 0.5  # bar
                piping_loss = 0.5  # bar, inter-stage piping friction
                
                p_required = pi_conc + target_ndp + permeate_backpressure
                p_available = stage_exit_pressure - piping_loss
                
                boost_dp = max(0.0, p_required - p_available)
                
                # Booster pump power: P = Q * ΔP / (36 * η)
                # η = 0.75 for typical centrifugal booster pump
                pump_efficiency = 0.75
                booster_flow = stage_exit_flow  # Total concentrate flow through booster
                
                if boost_dp > 0:
                    booster_power_kw = (booster_flow * boost_dp) / (36.0 * pump_efficiency)
                    booster_required = True
                else:
                    booster_power_kw = 0.0
                    booster_required = False
                
                total_booster_power_kw += booster_power_kw
                
                booster_data = {
                    "location": f"Between Stage {stage_idx + 1} and Stage {stage_idx + 2}",
                    "from_stage": stage_idx + 1,
                    "to_stage": stage_idx + 2,
                    "flow_m3h": round(booster_flow, 2),
                    "inlet_pressure_bar": round(p_available, 2),
                    "osmotic_pressure_bar": round(pi_conc, 2),
                    "required_pressure_bar": round(p_required, 2),
                    "outlet_pressure_bar": round(p_available + boost_dp, 2),
                    "boost_dp_bar": round(boost_dp, 2),
                    "power_kw": round(booster_power_kw, 2),
                    "required": booster_required,
                    "pump_efficiency": pump_efficiency
                }
                
                system_results["booster_pumps"].append(booster_data)
                
                # Update feed conditions for next stage
                current_feed_flow = stage_exit_flow
                current_feed_pressure = p_available + boost_dp  # Pressure after booster
                current_ions = stage_exit_ions.copy()
            else:
                # Last stage — no booster needed
                current_feed_flow = stage_exit_flow
                current_ions = stage_exit_ions.copy()
            
        # Final System summary
        system_perm_ions = {}
        system_perm_tds = 0.0
        feed_tds = sum(feed_ions.values())
        conc_tds = sum(current_ions.values())
        
        for ion in feed_ions.keys():
            if total_perm_flow > 0:
                c = total_perm_mass[ion] / total_perm_flow
                system_perm_ions[ion] = c
                system_perm_tds += c
            else:
                system_perm_ions[ion] = 0.0
                
        total_area = sum(vessels_per_stage) * elements_per_vessel * membrane["active_area_m2"]
        avg_flux = (total_perm_flow * 1000.0) / total_area
        system_recovery = total_perm_flow / feed_flow_m3h
        
        # SEC Calculation — includes high pressure pump + all booster pumps
        # High pressure pump: Power = Q * P / (36 * efficiency)
        hp_pump_efficiency = 0.80
        hp_pump_power_kw = (feed_flow_m3h * feed_pressure_bar) / (36.0 * hp_pump_efficiency)
        total_power_kw = hp_pump_power_kw + total_booster_power_kw
        sec = total_power_kw / total_perm_flow if total_perm_flow > 0 else 0
        
        system_results["summary"] = {
            "total_recovery": system_recovery,
            "feed_flow": feed_flow_m3h,
            "perm_flow": total_perm_flow,
            "conc_flow": current_feed_flow,
            "avg_flux_lmh": avg_flux,
            "feed_pressure_bar": feed_pressure_bar,
            "hp_pump_power_kw": round(hp_pump_power_kw, 2),
            "booster_pump_power_kw": round(total_booster_power_kw, 2),
            "total_power_kw": round(total_power_kw, 2),
            "sec_kwh_m3": sec,
            "feed_tds": feed_tds,
            "perm_tds": system_perm_tds,
            "conc_tds": conc_tds,
            "perm_ions": system_perm_ions,
            "conc_ions": current_ions,
            "vessels_per_stage": vessels_per_stage
        }
        
        return system_results
