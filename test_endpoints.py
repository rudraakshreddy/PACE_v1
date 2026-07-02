import json
from backend.membrane_recommender import MembraneRecommender
from backend.system_engine import SystemEngine

payload = {
    "technology_train": "RO",
    "feed_water": {
        "calcium": 10, "magnesium": 5, "sodium": 150, "potassium": 0,
        "barium": 0, "strontium": 0, "chloride": 200, "sulfate": 30,
        "bicarbonate": 50, "nitrate": 0, "fluoride": 0, "silica": 5,
        "boron": 0, "phosphate": 0, "aluminium": 0, "iron": 0,
        "manganese": 0, "temperature": 25, "ph": 7.5, "tds": 450,
        "tss": 0, "turbidity": 0
    },
    "target_flow_m3h": 50.0,
    "target_recovery_pct": 75.0,
    "target_tds": 50.0,
    "source_type": "LOW_TDS",
    "ro_membrane": "BW30-400",
    "stages": 2,
    "vessels_per_stage": [4, 2],
    "elements_per_vessel": 6
}

try:
    print("Testing /api/calculate-system...")
    engine = SystemEngine()
    calc_res = engine.calculate_system(payload)
    print("Calculate system OK. Keys:", calc_res.keys())
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    print("\nTesting /api/recommend-membrane...")
    recommender = MembraneRecommender()
    rec_res = recommender.recommend(payload)
    print("Recommend membrane OK.")
    for rec in rec_res.get("recommendations", [])[:2]:
        print(f" - {rec['model']}: {rec.get('calculated_metrics')}")
except Exception as e:
    import traceback
    traceback.print_exc()
