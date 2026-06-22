"""
Multi-Technology System Engine
Orchestrates UF, RO, and NF calculations based on the selected technology train.
"""

from typing import Dict, Any, List
from uf_engine import UFEngine
from calc_engine import ROEngine
from membrane_database import MembraneDatabase

class SystemEngine:
    def __init__(self):
        self.uf_engine = UFEngine()
        self.ro_engine = ROEngine()
        
    def calculate_system(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for system calculation.
        input_data must contain:
        - technology_train: e.g., "UF+RO", "RO", "UF+NF"
        - feed_water: dict of ions, temp, ph, tds
        - target_flow_m3h: float
        - target_recovery_pct: float
        - ro_membrane: str (model name)
        - uf_module: str (model name)
        - stages: int
        - vessels_per_stage: List[int]
        - elements_per_vessel: int
        """
        train = input_data.get("technology_train", "RO")
        feed = input_data["feed_water"]
        target_flow = input_data["target_flow_m3h"]
        
        result = {
            "technology_train": train,
            "feed_water_used": feed,
            "uf_results": None,
            "ro_results": None
        }
        
        # 1. UF Simulation
        if "UF" in train:
            # The system feed flow enters the UF.
            # UF engine expects gross_feed_flow_m3h (intake limited).
            uf_res = self.uf_engine.simulate_uf(
                gross_feed_flow_m3h=target_flow,
                temp_c=feed.get("temperature", 25.0),
                module_name=input_data.get("uf_module", "IntegraTec-SFD-2880"),
                feed_turbidity=feed.get("turbidity", 20.0),
                feed_tss=feed.get("tss", 30.0),
                feed_tds=feed.get("tds", sum([v for k,v in feed.items() if isinstance(v, (int, float)) and k not in ["temperature", "ph", "turbidity", "tss", "tds"]])),
                feed_ph=feed.get("ph", 7.3)
            )
            result["uf_results"] = uf_res
            
            # The feed to the RO/NF system is the UF product
            ro_feed_flow = uf_res["overview"]["net_product_m3h"]
        else:
            # No UF, RO feed is direct from system feed flow
            ro_feed_flow = target_flow
            
        # 2. RO/NF Simulation
        if "RO" in train or "NF" in train:
            # Extract ions from feed
            ions = {
                "Ca": feed.get("calcium", 0),
                "Mg": feed.get("magnesium", 0),
                "Na": feed.get("sodium", 0),
                "K": feed.get("potassium", 0),
                "Cl": feed.get("chloride", 0),
                "SO4": feed.get("sulfate", 0),
                "HCO3": feed.get("bicarbonate", 0),
                "Ba": feed.get("barium", 0),
                "Sr": feed.get("strontium", 0),
                "F": feed.get("fluoride", 0),
                "SiO2": feed.get("silica", 0),
                "B": feed.get("boron", 0),
                "NO3": feed.get("nitrate", 0),
                "PO4": feed.get("phosphate", 0),
                "NH4": feed.get("ammonium", 0),
                "Al": feed.get("aluminium", 0),
                "Fe": feed.get("iron", 0),
                "Mn": feed.get("manganese", 0)
            }
            
            # Determine starting pressure based on TDS (rough estimate for converging solver)
            est_osmotic_bar = (sum(ions.values()) / 1000.0) * 0.7 # rough rule of thumb
            
            # Solve for feed pressure to achieve the target recovery
            target_recovery = input_data.get("target_recovery_pct", 75.0) / 100.0
            
            low_p = max(1.0, est_osmotic_bar - 5.0)
            high_p = max(120.0, est_osmotic_bar + 60.0)
            tol = 0.005 # 0.5% tolerance on recovery
            
            ro_res = None
            for _ in range(25):
                mid_p = (low_p + high_p) / 2.0
                ro_res = self.ro_engine.simulate_system(
                    feed_flow_m3h=ro_feed_flow,
                    feed_pressure_bar=mid_p,
                    feed_ions=ions,
                    temp_c=feed.get("temperature", 25.0),
                    membrane_model=input_data.get("ro_membrane", "BW30-400"),
                    stages=input_data.get("stages", 2),
                    vessels_per_stage=input_data.get("vessels_per_stage", [4, 2]),
                    elements_per_vessel=input_data.get("elements_per_vessel", 6)
                )
                rec = ro_res["summary"]["total_recovery"]
                if abs(rec - target_recovery) < tol:
                    break
                if rec < target_recovery:
                    low_p = mid_p
                else:
                    high_p = mid_p
            
            result["ro_results"] = ro_res
            
            # --- Economic Calculation ---
            eco_params = input_data.get("economic_params")
            if eco_params and ro_res:
                summary = ro_res["summary"]
                mem_type = input_data.get("ro_membrane", "BW30-400")
                membrane = MembraneDatabase.get_ro_membrane(mem_type)
                
                # Always determine membrane price from the membrane type to avoid
                # stale cached values from the frontend's eco-mem-cost input
                if mem_type and "nf" in mem_type.lower():
                    elem_price = 19200.0
                elif membrane and membrane.get("type", "").upper() == "SWRO":
                    elem_price = 30240.0
                elif membrane and membrane.get("nominal_rejection", membrane.get("rejection_pct", 0)) >= 0.995:
                    elem_price = 30240.0
                else:
                    elem_price = 26880.0

                    
                vessels_per_stage = input_data.get("vessels_per_stage", [4, 2])
                n_vessels = sum(vessels_per_stage)
                n_elements = n_vessels * input_data.get("elements_per_vessel", 6)
                
                c_membranes = n_elements * elem_price
                c_vessels = n_vessels * eco_params.get("vessel_cost", 48000.0)
                
                hp_kw = summary.get("hp_pump_power_kw", 0.0)
                bp_kw = summary.get("booster_pump_power_kw", 0.0)
                
                pump_cost_kw = eco_params.get("pump_cost_kw", 96000.0)
                c_hp_pump = hp_kw * pump_cost_kw
                c_bp_pump = bp_kw * pump_cost_kw
                
                c_equip_sub = c_membranes + c_vessels + c_hp_pump + c_bp_pump
                
                ic_factor = eco_params.get("ic_factor", 0.15)
                c_ic = c_equip_sub * ic_factor
                
                contingency_factor = eco_params.get("contingency_factor", 0.10)
                c_contingency = (c_equip_sub + c_ic) * contingency_factor
                
                total_capex = c_equip_sub + c_ic + c_contingency
                
                # OPEX
                avail = eco_params.get("plant_availability", 0.90)
                hours_pa = avail * 8760.0
                
                total_kw = summary.get("total_power_kw", 0.0)
                tariff = eco_params.get("electricity_tariff", 7.50)
                energy_cost_pa = total_kw * hours_pa * tariff
                
                mem_life = eco_params.get("membrane_lifetime", 5.0)
                mem_repl_pa = c_membranes / mem_life if mem_life > 0 else 0
                
                total_opex_pa = energy_cost_pa + mem_repl_pa
                
                # Cost per KL
                discount_rate = eco_params.get("discount_rate", 0.10)
                project_life = eco_params.get("project_life", 20.0)
                crf = 0.0
                if discount_rate > 0 and project_life > 0:
                    crf = (discount_rate * ((1 + discount_rate) ** project_life)) / (((1 + discount_rate) ** project_life) - 1)
                
                annualised_capex = total_capex * crf
                total_annual_cost = annualised_capex + total_opex_pa
                
                q_perm = summary.get("perm_flow", 0.0)
                q_annual = q_perm * hours_pa
                
                cost_per_kl = total_annual_cost / q_annual if q_annual > 0 else 0.0
                
                result["economics"] = {
                    "unit_membrane_cost_inr": elem_price,
                    "capex": {
                        "membranes_inr": round(c_membranes, 2),
                        "vessels_inr": round(c_vessels, 2),
                        "hp_pump_inr": round(c_hp_pump, 2),
                        "booster_pump_inr": round(c_bp_pump, 2),
                        "equip_subtotal_inr": round(c_equip_sub, 2),
                        "ic_inr": round(c_ic, 2),
                        "contingency_inr": round(c_contingency, 2),
                        "total_capex_inr": round(total_capex, 2)
                    },
                    "opex": {
                        "annual_hours": round(hours_pa, 0),
                        "energy_cost_pa_inr": round(energy_cost_pa, 2),
                        "membrane_repl_pa_inr": round(mem_repl_pa, 2),
                        "total_opex_pa_inr": round(total_opex_pa, 2)
                    },
                    "metrics": {
                        "crf": round(crf, 4),
                        "annualised_capex_inr": round(annualised_capex, 2),
                        "total_annual_cost_inr": round(total_annual_cost, 2),
                        "annual_production_kl": round(q_annual, 0),
                        "cost_per_kl_inr": round(cost_per_kl, 2)
                    }
                }
            
        return result

    def calculate_system_with_recycle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper around calculate_system() that implements concentrate recycle.
        Iteratively blends a fraction of the last-stage concentrate back into
        the fresh feed until steady state is reached.

        Additional input_data keys:
          - recycle_ratio: float 0.0–1.0 (fraction of concentrate recycled)
        """
        recycle_ratio = input_data.get("recycle_ratio", 0.0)

        # If recycle is 0 or negligible, just call the normal path
        if recycle_ratio <= 0.001:
            return self.calculate_system(input_data)

        # 1. Run baseline (0% recycle) calculation to return at the top-level
        baseline_input = dict(input_data)
        baseline_input.pop("recycle_enabled", None)
        baseline_input.pop("recycle_ratio", None)
        final_result = self.calculate_system(baseline_input)

        feed = input_data["feed_water"]
        fresh_flow = input_data["target_flow_m3h"]

        # Build fresh-feed ion dict (same extraction as calculate_system)
        ion_keys = [
            ("calcium", "Ca"), ("magnesium", "Mg"), ("sodium", "Na"),
            ("potassium", "K"), ("chloride", "Cl"), ("sulfate", "SO4"),
            ("bicarbonate", "HCO3"), ("barium", "Ba"), ("strontium", "Sr"),
            ("fluoride", "F"), ("silica", "SiO2"), ("boron", "B"),
            ("nitrate", "NO3"), ("phosphate", "PO4"), ("ammonium", "NH4"),
            ("aluminium", "Al"), ("iron", "Fe"), ("manganese", "Mn")
        ]
        fresh_ions = {}
        for feed_key, engine_key in ion_keys:
            fresh_ions[engine_key] = feed.get(feed_key, 0)

        # Iteration state
        max_iter = 15
        tolerance = 0.002  # 0.2 % relative change in permeate flow
        q_r_prev = 0.0
        c_r_prev = {k: v for k, v in fresh_ions.items()}  # placeholder
        q_p_prev = None

        converged = False
        result = None
        iterations_used = 0

        for iteration in range(max_iter):
            iterations_used = iteration + 1

            # 1. Blend feed
            q_blend = fresh_flow + q_r_prev
            c_blend = {}
            for ion in fresh_ions:
                c_blend[ion] = (fresh_ions[ion] * fresh_flow + c_r_prev.get(ion, 0) * q_r_prev) / q_blend

            # 2. Build a modified input_data with blended feed
            blended_feed = dict(feed)
            for feed_key, engine_key in ion_keys:
                blended_feed[feed_key] = c_blend[engine_key]
            blended_feed["tds"] = sum(c_blend.values())

            modified_input = dict(input_data)
            modified_input["feed_water"] = blended_feed
            modified_input["target_flow_m3h"] = q_blend
            # Remove recycle keys so nested call doesn't recurse
            modified_input.pop("recycle_enabled", None)
            modified_input.pop("recycle_ratio", None)

            # 3. Call the EXISTING engine (completely unchanged)
            result = self.calculate_system(modified_input)

            # 4. Extract concentrate info from RO results
            ro_res = result.get("ro_results")
            if not ro_res:
                break

            summary = ro_res["summary"]
            q_p = summary.get("perm_flow", 0)
            q_c = summary.get("conc_flow", 0)

            # Get concentrate ions from the last element of the RO system
            elements_data = ro_res.get("elements", [])
            if elements_data:
                last_elem = elements_data[-1]
                c_c = last_elem.get("rej_ions", c_r_prev)
            else:
                c_c = c_r_prev

            # 5. Update recycle stream
            q_r_new = recycle_ratio * q_c
            c_r_new = {k: v for k, v in c_c.items()}

            # 6. Check convergence
            if q_p_prev is not None and q_p_prev > 0:
                delta = abs(q_p - q_p_prev) / q_p_prev
                if delta < tolerance:
                    converged = True
                    q_r_prev = q_r_new
                    c_r_prev = c_r_new
                    break

            # 7. Store for next iteration
            q_r_prev = q_r_new
            c_r_prev = c_r_new
            q_p_prev = q_p

        # 8. Augment the baseline final_result with recycle metadata
        if result and final_result:
            q_p_final = 0
            feed_pressure_final = 0.0
            perm_tds_final = 0.0
            if result.get("ro_results"):
                ro_sum = result["ro_results"]["summary"]
                q_p_final = ro_sum.get("perm_flow", 0)
                feed_pressure_final = ro_sum.get("feed_pressure_bar", 0.0)
                perm_tds_final = ro_sum.get("perm_tds", 0.0)

            effective_recovery = q_p_final / fresh_flow if fresh_flow > 0 else 0

            final_result["recycle"] = {
                "enabled": True,
                "recycle_ratio": recycle_ratio,
                "recycle_flow_m3h": round(q_r_prev, 4),
                "blended_feed_flow_m3h": round(fresh_flow + q_r_prev, 4),
                "blended_feed_tds_mg_l": round(result["feed_water_used"].get("tds", 0.0), 1),
                "fresh_feed_flow_m3h": fresh_flow,
                "iterations_to_converge": iterations_used,
                "converged": converged,
                "effective_system_recovery": round(effective_recovery, 4),
                "effective_system_recovery_pct": round(effective_recovery * 100, 2),
                "feed_pressure_bar": round(feed_pressure_final, 2),
                "permeate_tds_mg_l": round(perm_tds_final, 1)
            }

            if not converged:
                final_result["recycle"]["warning"] = "Recycle loop did not converge within {} iterations".format(max_iter)

        return final_result
