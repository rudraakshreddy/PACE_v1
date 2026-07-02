import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from system_engine import SystemEngine

engine = SystemEngine()

payload = {
    "technology_train": "2P-RO",
    "feed_water": {
        "temperature": 25.0,
        "sodium": 200.0,
        "chloride": 300.0
    },
    "target_flow_m3h": 100.0,
    "pass1": {
        "target_recovery_pct": 80.0,
        "membrane": "BW30-400",
        "stages": 2,
        "vessels_per_stage": [4, 2],
        "elements_per_vessel": 6
    },
    "pass2": {
        "target_recovery_pct": 85.0,
        "membrane": "BW30-400",
        "stages": 1,
        "vessels_per_stage": [2],
        "elements_per_vessel": 6,
        "p2_max_flux_lmh": 40.0
    }
}

res = engine.simulate_two_pass_system(payload)

print("Pass 1 Elements:")
for e in res["pass1_results"]["elements"]:
    print(f"S{e['stage']}E{e['position']} Flux={e['flux']:.1f} LMH, FeedFlow={e['feed_flow']:.1f} m3/h, Beta={e['beta']:.2f}")

print("\nPass 2 Elements:")
for e in res["pass2_results"]["elements"]:
    print(f"S{e['stage']}E{e['position']} Flux={e['flux']:.1f} LMH, FeedFlow={e['feed_flow']:.1f} m3/h, Beta={e['beta']:.2f}")
