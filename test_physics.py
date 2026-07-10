import requests
import json

payload = {
    "technology_train": "RO",
    "feed_water": {
        "calcium": 85, "magnesium": 28, "sodium": 130, "potassium": 4.5, "barium": 0.05,
        "strontium": 1.2, "chloride": 180, "sulfate": 110, "bicarbonate": 180, "nitrate": 15,
        "fluoride": 0.6, "silica": 18, "boron": 0, "phosphate": 0.1, "aluminium": 0.03,
        "iron": 0.05, "manganese": 0.02, "temperature": 25, "ph": 7.2, "tds": 753.6,
        "tss": 0, "turbidity": 0.2
    },
    "target_flow_m3h": 50.0,
    "target_recovery_pct": 75.0,
    "target_tds": 50.0,
    "source_type": "LOW_TDS",
    "ro_membrane": "HPA-4040",
    "stages": 2,
    "vessels_per_stage": [4, 2],
    "elements_per_vessel": 6,
    "n_years": 5,
    "recycle_enabled": False,
    "recycle_ratio": 0.0,
    "pass1": {
        "membrane": "HPA-4040", "stages": 2, "vessels_per_stage": [4, 2],
        "elements_per_vessel": 6, "target_recovery_pct": 75.0
    },
    "pass2": None,
    "conditioning": {
        "enabled": False, "target_ph": 9.8, "chemical": "NaOH", "co2_degassing": False
    },
    "recycle": {"enabled": False, "recycle_ratio": 0.0}
}

r = requests.post("http://127.0.0.1:8000/api/calculate-system-physics", json=payload, auth=("pace_permionics", "satyaraj_permionics@2026"))
try:
    data = r.json()
    with open("snapshots.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
except Exception as e:
    print("Failed to decode JSON. Status code:", r.status_code)
    try:
        print("Response text:", r.text)
    except:
        pass

