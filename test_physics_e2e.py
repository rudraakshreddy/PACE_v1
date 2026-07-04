import sys
sys.path.insert(0, 'backend')
from physics_aging_engine import PhysicsAgingEngine

baseline = {
    'summary': {
        'perm_flow': 45.0, 'total_recovery': 0.75, 'feed_pressure_bar': 12.0,
        'perm_tds': 35.0, 'sec_kwh_m3': 0.52, 'concentrate_flow': 15.0, 'concentrate_tds': 2800.0
    },
    'elements': [
        {'stage': 1, 'vessel': 1, 'element': i, 'jw_lmh': 18.0, 'cp': 0.0004,
         'p_feed_bar': 12.0 - i*0.05, 'p_perm_bar': 0.5, 'osm_feed_bar': 2.5,
         'tmp_bar': 9.0, 're': 110.0, 'sh': 45.0, 'kmt_ms': 2.5e-5,
         'perm_flow_m3h': 2.1, 'cf': 1.15}
        for i in range(6)
    ]
}
ions = {
    'Ca': 80, 'Mg': 25, 'Na': 120, 'K': 5, 'Cl': 200, 'SO4': 150, 'HCO3': 180,
    'Ba': 0.05, 'Sr': 1.0, 'F': 0.5, 'SiO2': 15, 'B': 0.3, 'NO3': 5,
    'PO4': 0.1, 'NH4': 0, 'Al': 0, 'Fe': 0.1, 'Mn': 0.05
}

engine = PhysicsAgingEngine()
result = engine.run_physics_projection(
    baseline_ro_result=baseline, feed_ions=ions, temp_c=25.0, ph=7.5,
    membrane_model='BW30-400', stages=2, vessels_per_stage=[4, 2],
    elements_per_vessel=6, target_recovery_pct=75.0, feed_flow_m3h=60.0, n_years=5,
    feed_quality={'sdi15': 3.5, 'toc_mg_l': 2.0, 'cl2_residual_mg_l': 0.0},
    cip_config={'acid_ph': 2.5, 'alk_ph': 11.5, 'interval_months': 12, 'duration_h': 4.0},
    antiscalant_dosed=True
)

snaps = result['annual_snapshots']
y0 = snaps[0]

# Assertions
assert abs(y0['npf'] - 1.0) < 1e-9, f"Year 0 NPF={y0['npf']}"
assert abs(y0['fri']) < 1e-9, f"Year 0 FRI={y0['fri']}"
assert abs(y0['perm_flow'] - 45.0) < 1e-6, f"Year 0 flow={y0['perm_flow']}"
assert abs(y0['feed_pressure_bar'] - 12.0) < 1e-6, f"Year 0 pressure={y0['feed_pressure_bar']}"
assert len(snaps) == 6, f"Expected 6, got {len(snaps)}"

required_keys = ['year','npf','nsp','fri','b_irr','perm_flow','recovery',
    'feed_pressure_bar','perm_tds','sec_kwh_m3','rc_avg','rb_avg','rs_avg','rn_avg',
    'rcomp','si_calcite_wall','si_gypsum_wall','si_barite_wall','si_silica_wall',
    'cip_triggered','replacement_triggered']
for snap in snaps:
    for k in required_keys:
        assert k in snap, f"Missing key {k} in Year {snap['year']}"

print("PASS: Year 0 exact match with baseline")
print("PASS: All " + str(len(snaps)) + " snapshots present with all required keys")
print("Dominant mechanism:", result['dominant_mechanism'])
print("CIP events:", result['cip_events'])
print()
print("{:>4}  {:>8}  {:>7}  {:>7}  {:>9}  {}".format("Year", "P_feed", "Qp", "NPF", "FRI", "CIP"))
print("-" * 55)
for s in snaps:
    cip_tag = "CIP" if s['cip_triggered'] else ""
    repl_tag = "[REPL]" if s['replacement_triggered'] else ""
    print("{:>4}  {:>8.2f}  {:>7.2f}  {:>7.4f}  {:>9.5f}  {}{}".format(
        s['year'], s['feed_pressure_bar'], s['perm_flow'], s['npf'], s['fri'], cip_tag, repl_tag))
print()
print("ALL ASSERTIONS PASSED")
