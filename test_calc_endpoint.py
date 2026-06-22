import requests

payload = {
    "technology_train": "RO",
    "feed_water": {"tds": 500},
    "target_flow_m3h": 100,
    "target_recovery_pct": 75,
    "ro_membrane": "SW30HRLE-400",
    "stages": 2,
    "vessels_per_stage": [4, 2],
    "elements_per_vessel": 6,
    "economic_params": {
        "electricity_tariff": 7.5,
        "membrane_cost": 26880,
        "vessel_cost": 48000,
        "pump_cost_kw": 96000,
        "ic_factor": 0.15,
        "contingency_factor": 0.10,
        "membrane_lifetime": 5,
        "plant_availability": 0.90,
        "discount_rate": 0.1,
        "project_life": 20
    }
}

r = requests.post("http://localhost:8000/api/calculate-system", json=payload)
print(r.status_code)
if r.status_code == 200:
    res = r.json()
    print("Economics output:")
    print(res.get("economics", "No economics found!"))
else:
    print(r.text)
