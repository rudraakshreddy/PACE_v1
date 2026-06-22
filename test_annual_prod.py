import json
import sys
import os

# Add backend to PYTHONPATH
sys.path.insert(0, os.path.abspath('backend'))

from backend.system_engine import SystemEngine

engine = SystemEngine()

payload = {
    "technology_train": "RO",
    "feed_water": {
        "calcium": 40,
        "magnesium": 12,
        "sodium": 105,
        "potassium": 0,
        "chloride": 190,
        "sulfate": 27,
        "bicarbonate": 14,
        "strontium": 0,
        "fluoride": 0,
        "silica": 0,
        "boron": 0,
        "nitrate": 0,
        "phosphate": 0,
        "ammonium": 0,
        "iron": 0,
        "manganese": 0,
        "temperature": 25,
        "ph": 7.5,
        "tds": 388,
        "tss": 0,
        "turbidity": 0
    },
    "target_flow_m3h": 50,
    "target_recovery_pct": 75,
    "ro_membrane": "HPA-4040",
    "uf_module": None,
    "stages": 2,
    "vessels_per_stage": [4, 2],
    "elements_per_vessel": 6,
    "economic_params": {
        "electricity_tariff": 7.50,
        "membrane_cost": 26880,
        "vessel_cost": 48000,
        "pump_cost_kw": 96000,
        "ic_factor": 0.15,
        "contingency_factor": 0.10,
        "membrane_lifetime": 5,
        "plant_availability": 0.90,
        "discount_rate": 0.10,
        "project_life": 20
    }
}

res = engine.calculate_system(payload)
print("Flow: 50")
print("Perm Flow:", res['ro_results']['summary']['perm_flow'])
print("Annual Prod:", res['economics']['metrics']['annual_production_kl'])

payload["target_flow_m3h"] = 100
res2 = engine.calculate_system(payload)
print("\nFlow: 100")
print("Perm Flow:", res2['ro_results']['summary']['perm_flow'])
print("Annual Prod:", res2['economics']['metrics']['annual_production_kl'])
