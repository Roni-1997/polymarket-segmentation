"""Seven-cohort grid (v1) and the proposed v2 over any window, from the per-day feature cache
(<PM_DATA_DIR>/pm5m_wfeat_<day>.json, built by day_features.py). One cohort per wallet per window, as the segmentation
repo defines it: cadence = fills per active day within the window, maker share = maker touched / total touched
within the window. Reports per calendar month and for the whole period, plus a daily series.
Usage: python3 grid_from_features.py START END OUT.json"""
import os
DATA=os.environ.get('PM_DATA_DIR','/tmp')   # where the day files live
import json, os, sys, collections, statistics as st, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cohorts_v1_v2 as pc
start, end, outp = sys.argv[1], sys.argv[2], sys.argv[3]
d0 = dt.date.fromisoformat(start)
days = [(d0 + dt.timedelta(i)).isoformat() for i in range((dt.date.fromisoformat(end) - d0).days + 1)]
have = [d for d in days if os.path.exists(f'{DATA}/pm5m_wfeat_{d}.json')]
missing = [d for d in days if d not in have]
print(f'days {len(have)}/{len(days)} cached; missing: {missing[:10]}{"..." if len(missing) > 10 else ""}', flush=True)

def fresh(): return {'fills': 0, 'mk': 0.0, 'tk': 0.0, 'pnl': 0.0, 'cov': 0.0, 'days': 0, 'v2': collections.Counter()}
W_all = collections.defaultdict(fresh)
W_month = collections.defaultdict(lambda: collections.defaultdict(fresh))
daily = []; month_days = collections.Counter()
MACH = ('Neutral bot', 'Directional bot'); PEOPLE = ('Session trader', 'Retail')
for d in have:
    D = json.load(open(f'{DATA}/pm5m_wfeat_{d}.json')); F = D['wallets']; m = d[:7]; month_days[m] += 1
    touched = sum(f['mk'] + f['tk'] for f in F.values())
    row = {'day': d, 'touched': touched, 'wallets': len(F), 'legs': D['legs']}
    for c in pc.ORDER: row[c] = 100 * sum(f['mk'] + f['tk'] for f in F.values() if f['c1'] == c) / touched
    for lab, grp in (('machines', MACH), ('people', PEOPLE)):
        fs = [f for f in F.values() if f['c2'] in grp]; cv = sum(f['cov'] for f in fs)
        row[lab + '_pct'] = 100 * sum(f['mk'] + f['tk'] for f in fs) / touched
        row[lab + '_pnl'] = 100 * sum(f['pnl'] for f in fs) / cv if cv else 0.0
    row['profitable_pct'] = 100 * sum(1 for f in F.values() if f['pnl'] > 0.01) / len(F)
    daily.append(row)
    for w, f in F.items():
        for a in (W_all[w], W_month[m][w]):
            a['fills'] += f['fills']; a['mk'] += f['mk']; a['tk'] += f['tk']; a['pnl'] += f['pnl']; a['cov'] += f['cov']
            a['days'] += 1; a['v2'][f['c2']] += 1

def grid(W):
    touched = sum(a['mk'] + a['tk'] for a in W.values()); mk = sum(a['mk'] for a in W.values()); tk = sum(a['tk'] for a in W.values())
    for a in W.values():
        tot = a['mk'] + a['tk']; a['ms'] = a['mk'] / tot if tot else 0; a['cad'] = a['fills'] / a['days']
        a['c1'] = pc.cohort(a['ms'], a['cad']); a['c2'] = a['v2'].most_common(1)[0][0]
    out = {'touched': touched, 'maker': mk, 'taker': tk, 'wallets': len(W), 'v1': {}, 'v2': {}}
    for key, order, slot in (('c1', pc.ORDER, 'v1'), ('c2', pc.ORDER2, 'v2')):
        for c in order:
            ws = [a for a in W.values() if a[key] == c]
            if not ws: continue
            t = sum(a['mk'] + a['tk'] for a in ws); p = sum(a['pnl'] for a in ws); cv = sum(a['cov'] for a in ws)
            out[slot][c] = dict(wallets=len(ws), touched=100 * t / touched, maker=100 * sum(a['mk'] for a in ws) / mk,
                                taker=100 * sum(a['tk'] for a in ws) / tk, pnl=100 * p / cv if cv else 0, pnl_usd=p,
                                profitable=100 * sum(1 for a in ws if a['pnl'] > 0.01) / len(ws),
                                median=100 * st.median(a['pnl'] / a['cov'] for a in ws if a['cov'] > 0) if any(a['cov'] > 0 for a in ws) else 0,
                                avg_days=st.mean(a['days'] for a in ws))
    out['profitable_pct'] = 100 * sum(1 for a in W.values() if a['pnl'] > 0.01) / len(W)
    out['median_pnl'] = 100 * st.median(a['pnl'] / a['cov'] for a in W.values() if a['cov'] > 0)
    gains = sorted((a['pnl'] for a in W.values() if a['pnl'] > 0), reverse=True)
    out['top1pct_gain_share'] = 100 * sum(gains[:max(1, len(W) // 100)]) / sum(gains) if gains else 0
    out['top01pct_gain_share'] = 100 * sum(gains[:max(1, len(W) // 1000)]) / sum(gains) if gains else 0
    for lab, lo, hi in (('d1', 1, 2), ('d2_4', 2, 5), ('d5_9', 5, 10), ('d10_19', 10, 20), ('d20p', 20, 999)):
        ws = [a for a in W.values() if lo <= a['days'] < hi]
        if ws: out['persist_' + lab] = dict(wallets=len(ws), share=100 * sum(a['mk'] + a['tk'] for a in ws) / touched,
                                            profitable=100 * sum(1 for a in ws if a['pnl'] > 0.01) / len(ws),
                                            median=100 * st.median(a['pnl'] / a['cov'] for a in ws if a['cov'] > 0) if any(a['cov'] > 0 for a in ws) else 0)
    return out

ROLL1 = (('MMs', ['Pro-MM', 'Mid-MM']), ('Bots+Algo', ['Fast-taker', 'Hybrid-bot', 'Systematic-taker', 'Systematic-mixed']), ('Retail', ['Retail']))
ROLL2 = (('MMs', ['Pro-MM', 'Part-time MM']), ('Machines', ['Neutral bot', 'Directional bot']), ('People', ['Session trader', 'Retail']))
def show(label, g, ndays):
    print(f"\n=== {label}: {ndays} days, touched ${g['touched']/1e6:.1f}M (${g['touched']/max(ndays,1)/1e6:.2f}M/day), wallets {g['wallets']:,}, "
          f"profitable {g['profitable_pct']:.1f}%, median PnL/$ {g['median_pnl']:+.2f}%, top 1% take {g['top1pct_gain_share']:.0f}% of gains")
    for slot, order, roll in (('v1', pc.ORDER, ROLL1), ('v2', pc.ORDER2, ROLL2)):
        print(f"  {slot:3s} {'cohort':17s} {'wallets':>8s} {'%touched':>8s} {'%maker':>7s} {'%taker':>7s} {'PnL/$':>7s} {'PnL $':>12s} {'profit.':>7s} {'median':>7s}")
        for c in order:
            r = g[slot].get(c)
            if r: print(f"      {c:17s} {r['wallets']:8,} {r['touched']:7.1f}% {r['maker']:6.1f}% {r['taker']:6.1f}% {r['pnl']:+6.2f}% {r['pnl_usd']:+12,.0f} {r['profitable']:6.1f}% {r['median']:+6.2f}%")
        for p, cs in roll:
            rs = [g[slot][c] for c in cs if c in g[slot]]
            print(f"      {p:17s} {sum(r['wallets'] for r in rs):8,} {sum(r['touched'] for r in rs):7.1f}% {sum(r['maker'] for r in rs):6.1f}% {sum(r['taker'] for r in rs):6.1f}% {'':7s} {sum(r['pnl_usd'] for r in rs):+12,.0f}")

result = {'days': have, 'missing': missing, 'daily': daily, 'months': {}}
for m in sorted(W_month):
    g = grid(W_month[m]); g['days'] = month_days[m]; result['months'][m] = g; show(m, g, month_days[m])
g = grid(W_all); g['days'] = len(have); result['period'] = g; show(f'{start} to {end}', g, len(have))
json.dump(result, open(outp, 'w'), indent=1); print('\nwritten', outp)
