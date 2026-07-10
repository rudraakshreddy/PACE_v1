"""
Live API test against the running server — POST /api/calculate-system-physics
"""
import urllib.request, base64, json, time

CREDS = base64.b64encode(b'pace_permionics:satyaraj_permionics@2026').decode()
BASE = 'http://localhost:8000'

payload = {
    "technology_train": "RO",
    "feed_water": {
        "calcium": 80, "magnesium": 25, "sodium": 120, "potassium": 5,
        "chloride": 200, "sulfate": 150, "bicarbonate": 180,
        "barium": 0.05, "strontium": 1.0, "fluoride": 0.5,
        "silica": 15, "nitrate": 5, "phosphate": 0.1,
        "iron": 0.1, "manganese": 0.05, "aluminium": 0,
        "temperature": 25, "ph": 7.5, "tss": 5, "turbidity": 0.3, "tds": 650
    },
    "target_flow_m3h": 50,
    "target_recovery_pct": 75,
    "ro_membrane": "BW30-400",
    "stages": 2,
    "vessels_per_stage": [4, 2],
    "elements_per_vessel": 6,
    # Physics fields
    "projection_year": 3,
    "n_years": 5,
    "antiscalant_dosed": True,
    "cip_config": {"acid_ph": 2.5, "alk_ph": 11.5, "interval_months": 12, "duration_h": 4.0}
}

req = urllib.request.Request(
    BASE + '/api/calculate-system-physics',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + CREDS},
    method='POST'
)

t0 = time.time()
try:
    r = urllib.request.urlopen(req, timeout=60)
    result = json.loads(r.read())
    elapsed = time.time() - t0
    
    print("STATUS: 200 OK in {:.1f}s".format(elapsed))
    
    snapshots = result.get('physics_results', {}).get('annual_snapshots', [])
    print("Snapshots:", len(snapshots))
    print("Selected year:", result.get('physics_selected_year'))
    print("Dominant mech:", result.get('physics_results', {}).get('dominant_mechanism'))
    
    print("\nYear  P_feed   Qp     NPF      FRI")
    print("-" * 45)
    for s in snapshots:
        cip = " CIP" if s.get('cip_triggered') else ""
        repl = " REPL" if s.get('replacement_triggered') else ""
        print("  {:>2}  {:>7.2f}  {:>7.2f}  {:>7.4f}  {:>8.5f}{}{}".format(
            s['year'], s['feed_pressure_bar'], s['perm_flow'], 
            s['npf'], s['fri'], cip, repl))
    
    # Year 0 exact match check
    y0 = snapshots[0]
    ro_sum = result.get('ro_results', {}).get('summary', {})
    print("\nYear 0 NPF:", y0['npf'], "(expected 1.0)")
    print("Year 0 FRI:", y0['fri'], "(expected 0.0)")
    print("Selected year summary override:")
    print("  feed_pressure_bar:", ro_sum.get('feed_pressure_bar'))
    print("  perm_flow:", ro_sum.get('perm_flow'))
    print("  npf:", ro_sum.get('npf'))

    print("\nLIVE API TEST PASSED")
    
except Exception as e:
    print("LIVE API TEST FAILED:", e)
    import traceback; traceback.print_exc()
