import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from system_engine import SystemEngine

payload = {
    "technology_train": "RO",
    "feed_water": {
        "calcium": 85, "magnesium": 28, "sodium": 130, "potassium": 4.5,
        "barium": 0.05, "strontium": 1.2, "chloride": 180, "sulfate": 110,
        "bicarbonate": 180, "nitrate": 15, "fluoride": 0.6, "silica": 18,
        "boron": 0, "phosphate": 0.1, "aluminium": 0.03, "iron": 0.05,
        "manganese": 0.02, "temperature": 25, "ph": 7.2, "tds": 753.6,
        "tss": 0, "turbidity": 0.2
    },
    "target_flow_m3h": 50.0,
    "target_recovery_pct": 75.0,
    "target_tds": 50.0,
    "source_type": "WELL_WATER",
    "ro_membrane": "BW30-400",
    "stages": 2,
    "vessels_per_stage": [4, 2],
    "elements_per_vessel": 6
}

engine = SystemEngine()
res = engine.calculate_system(payload)
ro = res.get("ro_results", {})
print("Warnings for standard input:")
for w in ro.get("warnings", []):
    print(w)
