import json
from backend.system_engine import SystemEngine

engine = SystemEngine()
payload = {
    "feed_water": {
        "calcium": 400,
        "magnesium": 1200,
        "sodium": 10500,
        "chloride": 19000,
        "sulfate": 2700,
        "bicarbonate": 140,
        "temperature": 25.0
    },
    "target_flow_m3h": 50,
    "ro_membrane": "HPA-4040",
    "target_recovery_pct": 50,
    "stages": 2,
    "vessels_per_stage": [4, 2],
    "elements_per_vessel": 6,
    "economic_params": {
        "electricity_tariff": 7.5,
        "vessel_cost": 48000,
        "pump_cost_kw": 96000,
        "membrane_cost": 26880,
        "discount_rate": 0.1,
        "project_life": 20,
        "membrane_lifetime": 5,
        "plant_availability": 0.9,
        "ic_factor": 0.15,
        "contingency_factor": 0.1
    }
}
res = engine.calculate_system(payload)
print(json.dumps(res, indent=2))
