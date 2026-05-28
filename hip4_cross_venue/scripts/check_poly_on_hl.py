import csv
import json
import time

from common import DATA_DIR, RESULTS_DIR, hl_info, is_hip4_coin, polymarket_volume_musd

# Load top Polymarket wallets from the audited cohort validation output.
# This file is top-per-cohort, not a venue-wide ranking. If Dune API
# results are fetched with the default 100-row limit, the 140-row query
# can also be clipped.
poly_top = []
with (RESULTS_DIR / "top20_per_cohort_30d.csv").open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        poly_top.append(row)

cohorts = sorted({row["cohort"] for row in poly_top})
expected_cohorts = {
    "Pro-MM", "Mid-MM", "Hybrid-bot", "Systematic-mixed",
    "Fast-taker", "Systematic-taker", "Retail",
}
if len(poly_top) < 140 or not expected_cohorts.issubset(cohorts):
    print(
        "WARNING: top20_per_cohort_30d.csv appears to be an exported/capped "
        f"validation sample ({len(poly_top)} rows, cohorts={cohorts}). "
        "Use repo-root queries/11_top_wallets_30d_with_lp.sql for a true venue-wide top-wallet sample."
    )

# Sort by volume and take top 30 within the exported validation sample.
poly_top.sort(key=lambda r: -polymarket_volume_musd(r))
top30 = poly_top[:30]
print("Checking top 30 wallets in exported Polymarket validation sample for any HL activity")
print()

end_ms = int(time.time() * 1000)
start_ms_30d = end_ms - 30*24*60*60*1000

results = []
for i, pw in enumerate(top30, 1):
    addr = pw["wallet"].lower()
    cohort = pw["cohort"]
    poly_touched_vol_musd = polymarket_volume_musd(pw)

    # Check HL portfolio state - does this address have any HL assets?
    state = hl_info({"type": "clearinghouseState", "user": addr}, timeout=15)
    has_perp_position = bool(state and isinstance(state, dict) and state.get("assetPositions"))

    # Pull 30d fills
    fills = hl_info(
        {
            "type": "userFillsByTime",
            "user": addr,
            "startTime": start_ms_30d,
            "endTime": end_ms,
            "aggregateByTime": False,
        },
        timeout=15,
    )
    api_error = fills is None
    if not isinstance(fills, list): fills = []

    hip4_fills = [f for f in fills if is_hip4_coin(f.get("coin", ""))]
    perp_fills = [f for f in fills if not is_hip4_coin(f.get("coin", ""))]
    hip4_n = sum(float(f.get("px",0))*float(f.get("sz",0)) for f in hip4_fills)
    perp_n = sum(float(f.get("px",0))*float(f.get("sz",0)) for f in perp_fills)

    status = (
        "api_error"
        if api_error
        else ("ACTIVE-HL" if (hip4_fills or perp_fills) else ("open_position_only" if has_perp_position else "no_HL_activity"))
    )
    results.append({
        "addr": addr, "poly_cohort": cohort,
        "poly_30d_touched_vol_musd": poly_touched_vol_musd,
        "poly_n_fills": int(pw["n_fills"]), "poly_maker_share": float(pw["maker_share"]),
        "hl_status": status,
        "hl_30d_total_fills": len(fills),
        "hl_30d_hip4_fills": len(hip4_fills), "hl_30d_hip4_notional": round(hip4_n, 0),
        "hl_30d_perp_fills": len(perp_fills), "hl_30d_perp_notional": round(perp_n, 0),
        "hl_has_open_position": has_perp_position,
        "hl_api_error": api_error,
    })
    print(f"{i:>2}. {addr} poly_cohort={cohort:<14} poly30d_touched=${poly_touched_vol_musd:>7.1f}M  ->  HL: {status:<18} hip4_fills={len(hip4_fills):>4} ${hip4_n:>10,.0f}  perp_fills={len(perp_fills):>4} ${perp_n:>12,.0f}")

# Summarize
api_errors = [r for r in results if r["hl_api_error"]]
active_on_hl = [r for r in results if r["hl_status"] == "ACTIVE-HL"]
print(f"\n=== Summary ===")
print(f"Rows with HL API errors: {len(api_errors)}")
print(f"Top-30 Polymarket wallets with ANY HL activity (30d): {len(active_on_hl)}")
print(f"Of which with HIP-4 activity (30d): {sum(1 for r in active_on_hl if r['hl_30d_hip4_fills']>0)}")
print(f"Of which with HL perp activity only: {sum(1 for r in active_on_hl if r['hl_30d_hip4_fills']==0 and r['hl_30d_perp_fills']>0)}")

with (DATA_DIR / "poly_x_hl_top30.json").open("w") as f:
    json.dump(results, f, indent=2)
    f.write("\n")
print(f"\nSaved {DATA_DIR / 'poly_x_hl_top30.json'}")
