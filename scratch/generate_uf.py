import json

def parse_flux(flux_str):
    try:
        parts = flux_str.replace(" ", "").split('-')
        return float(parts[0]), float(parts[1])
    except:
        return 50.0, 150.0 # fallback

def generate_uf_dict():
    with open('modules_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    modules = {}
    
    for i, row in enumerate(data):
        if i < 5: continue # Skip headers
        
        model = row[1]
        if not model or str(model).strip() == "" or str(model) == "None": continue
        
        area = float(row[2]) if row[2] else 50.0
        flux_str = row[3]
        design_flux, max_flux = parse_flux(str(flux_str))
        
        # Lower bound as design flux, upper bound as max filtration flux
        modules[model] = {
            "type": "UF",
            "manufacturer": "Permionics",
            "membrane_area_m2": area,
            "fiber_id_mm": 0.8,
            "max_filtration_flux_lmh": max_flux,
            "design_flux_lmh": design_flux,
            "clean_tmp_max_bar": 1.2,
            "fouled_tmp_max_bar": 2.1,
            "max_tmp_bar": 2.5,
            "backwash_flux_lmh": 150.0,
            "backwash_duration_s": 45,
            "air_scour_flow_m3h": 12.0,
            "min_forward_flush_m3h": 1.5,
            "permeability_Lp20": 400.0,
            "unit_cost_inr": 100000.0,
            "feed_pump_kw_per_module": 0.75,
            "backwash_pump_kw_per_module": 1.10
        }
    
    # Generate python code
    lines = ["    UF_MODULES = {"]
    for model, props in modules.items():
        lines.append(f'        "{model}": {{')
        for k, v in props.items():
            if isinstance(v, str):
                lines.append(f'            "{k}": "{v}",')
            else:
                lines.append(f'            "{k}": {v},')
        lines.append('        },')
    lines.append("    }")
    
    with open('scratch/uf_modules_code.py', 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
if __name__ == "__main__":
    generate_uf_dict()
