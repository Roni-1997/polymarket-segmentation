import csv

from common import DATA_DIR, RESULTS_DIR, read_json, polymarket_volume_musd

# Load Polymarket wallets
poly_wallets = {}
with (RESULTS_DIR / "top20_per_cohort_30d.csv").open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        addr = row["wallet"].lower()
        poly_wallets[addr] = row

# Add LP reward recipients separately
poly_lp = {}
with (RESULTS_DIR / "lp_rewards_top25.csv").open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        poly_lp[row["wallet"].lower()] = float(row["lp_rewards_usd"])

print(f"Polymarket top-20 per cohort wallets: {len(poly_wallets)}")
cohorts = sorted({row["cohort"] for row in poly_wallets.values()})
if len(poly_wallets) < 120 or "midMkr_med" not in cohorts:
    print(
        "WARNING: top20_per_cohort_30d.csv is an exported/capped validation "
        f"sample ({len(poly_wallets)} rows, cohorts={cohorts}), not a true venue-wide top-100."
    )
print(f"Polymarket LP-reward top-25 wallets: {len(poly_lp)}")
print()

# Load HIP-4 wallets (full snapshot of 127)
hip4_snap = read_json(DATA_DIR / "hip4_ws_wallets.json")
hip4_wallets = {w["addr"].lower(): w for w in hip4_snap["wallets"]}
print(f"HIP-4 wallets observed (WS sample, top 127): {len(hip4_wallets)}")

# Load HIP-4 top-50 classified
hip4_classified = {p["addr"].lower(): p for p in read_json(DATA_DIR / "hip4_top50_classified.json")}
print(f"HIP-4 wallets with 7d classification: {len(hip4_classified)}")
print()

# Overlap
overlap_polysnap_hip4 = set(poly_wallets.keys()) & set(hip4_wallets.keys())
overlap_polylp_hip4 = set(poly_lp.keys()) & set(hip4_wallets.keys())

print(f"=== Polymarket top-20-per-cohort wallets ∩ HIP-4 observed wallets ===")
print(f"Overlap count: {len(overlap_polysnap_hip4)}")
for a in overlap_polysnap_hip4:
    pw = poly_wallets[a]
    hw = hip4_wallets[a]
    hc = hip4_classified.get(a)
    tag = hc["tag"] if hc else "(not in top-50 classification)"
    print(f"  {a}")
    print(f"    POLY: cohort={pw['cohort']:<14} rank={pw['rank']:>2}  touched_vol=${polymarket_volume_musd(pw)*1e6:>14,.0f} mkr={pw['maker_share']:>5}  n_fills={pw['n_fills']:>8} n_mkts={pw['n_unique_markets']:>5}  fpd={pw['fills_per_day']:>7}  lp=${float(pw['lp_rewards_usd']):>9,.0f}")
    print(f"    HIP4: tag={tag:<20} fills(WS sample)={hw['trades']:>4} 7d_$={hc['hip4_notional'] if hc else '?'}  7d_perp$={hc['perp_notional'] if hc else '?'}")
    print()

print(f"=== Polymarket LP-reward top-25 ∩ HIP-4 observed wallets ===")
print(f"Overlap count: {len(overlap_polylp_hip4)}")
for a in overlap_polylp_hip4:
    lp = poly_lp[a]
    hw = hip4_wallets[a]
    print(f"  {a}  poly_lp_rewards=${lp:,.0f}  hip4_fills={hw['trades']}")

# Also check case sensitivity edge cases (full list of all HIP-4 wallets vs all poly addresses)
print()
print(f"=== Diagnostic: any HIP-4 wallets that look 'system-like' (zero, 0xdeadbeef, etc)? ===")
suspicious = [a for a in hip4_wallets if a in ('0x0000000000000000000000000000000000000000', '0xdead', '0xdeadbeef')]
print(f"  {suspicious}")
