"""Per-day, per-wallet feature cache for Polymarket BTC 5m both-legs data.
For each day: load taker and both-legs files, compute the per-wallet features (fills, maker/taker touched,
settlement PnL, sleep gap, hours, windows, exact-dollar share, two-sidedness, density) plus the v1 and v2
cohort labels for that day, and write a compact JSON (a few MB) so window grids can be built in seconds
without re-reading the raw files. Usage: python3 day_features.py DAY [DAY ...]  (skips days already cached)."""
import os
DATA=os.environ.get('PM_DATA_DIR','/tmp')   # where the day files live
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cohorts_v1_v2 as pc
for day in sys.argv[1:]:
    outp = f'{DATA}/pm5m_wfeat_{day}.json'
    if os.path.exists(outp): print(day, 'exists', flush=True); continue
    if not (os.path.exists(f'{DATA}/pm5m_both_tx_{day}.json') and os.path.exists(f'{DATA}/pm5m_taker_tx_{day}.json')):
        print(day, 'missing inputs', flush=True); continue
    t0 = time.time()
    legs = pc.load(day); n_legs = len(legs); n_taker = sum(1 for l in legs if l[1] == 'taker')
    day0 = (min(l[7] for l in legs) // 86400) * 86400
    F = pc.features_v2(legs, day0); del legs
    for w, f in F.items():
        f['c1'] = pc.cohort(f['ms'], f['fills']); f['c2'] = pc.cohort_v2(f)
    json.dump({'day': day, 'legs': n_legs, 'taker_legs': n_taker, 'wallets': F}, open(outp, 'w'))
    print(day, 'wallets', len(F), 'legs', n_legs, 'secs', int(time.time() - t0), flush=True)
