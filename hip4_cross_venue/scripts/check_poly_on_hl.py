import json, subprocess, csv, time

# Load top 30 Polymarket wallets (5 from each of the 6 cohorts to get a mix)
poly_top = []
with open("../../results/top20_per_cohort_30d.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        poly_top.append(row)

# Sort by volume and take top 30
poly_top.sort(key=lambda r: -float(r["vol_musd"]))
top30 = poly_top[:30]
print(f"Checking top 30 Polymarket wallets (by 30d vol) for any HL activity")
print()

end_ms = int(time.time() * 1000)
start_ms_7d = end_ms - 7*24*60*60*1000
start_ms_30d = end_ms - 30*24*60*60*1000

def hl_call(payload):
    r = subprocess.run(
        ["curl","-s","-X","POST","https://api.hyperliquid.xyz/info",
         "-H","Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=15
    )
    try:
        return json.loads(r.stdout) if r.stdout.strip() else None
    except:
        return None

def is_hip4(coin):
    return coin and coin.startswith("#") and coin[1:].isdigit() and int(coin[1:]) >= 1000

results = []
for i, pw in enumerate(top30, 1):
    addr = pw["wallet"].lower()
    cohort = pw["cohort"]

    # Check HL portfolio state - does this address have any HL assets?
    state = hl_call({"type":"clearinghouseState","user":addr})
    has_perp_position = bool(state and isinstance(state, dict) and state.get("assetPositions"))

    # Pull 30d fills
    fills = hl_call({"type":"userFillsByTime","user":addr,"startTime":start_ms_30d,"endTime":end_ms,"aggregateByTime":False})
    if not isinstance(fills, list): fills = []

    hip4_fills = [f for f in fills if is_hip4(f.get("coin",""))]
    perp_fills = [f for f in fills if not is_hip4(f.get("coin",""))]
    hip4_n = sum(float(f.get("px",0))*float(f.get("sz",0)) for f in hip4_fills)
    perp_n = sum(float(f.get("px",0))*float(f.get("sz",0)) for f in perp_fills)

    status = "ACTIVE-HL" if (hip4_fills or perp_fills) else ("PERP-ONLY" if has_perp_position else "no_HL_activity")
    results.append({
        "addr": addr, "poly_cohort": cohort, "poly_30d_vol": float(pw["vol_musd"]),
        "poly_n_fills": int(pw["n_fills"]), "poly_maker_share": float(pw["maker_share"]),
        "hl_status": status,
        "hl_30d_total_fills": len(fills),
        "hl_30d_hip4_fills": len(hip4_fills), "hl_30d_hip4_notional": round(hip4_n, 0),
        "hl_30d_perp_fills": len(perp_fills), "hl_30d_perp_notional": round(perp_n, 0),
        "hl_has_open_position": has_perp_position,
    })
    print(f"{i:>2}. {addr} poly_cohort={cohort:<14} poly30d=${float(pw['vol_musd']):>7.1f}M  →  HL: {status:<15} hip4_fills={len(hip4_fills):>4} ${hip4_n:>10,.0f}  perp_fills={len(perp_fills):>4} ${perp_n:>12,.0f}")

# Summarize
active_on_hl = [r for r in results if r["hl_status"] == "ACTIVE-HL"]
print(f"\n=== Summary ===")
print(f"Top-30 Polymarket wallets with ANY HL activity (30d): {len(active_on_hl)}")
print(f"Of which with HIP-4 activity (30d): {sum(1 for r in active_on_hl if r['hl_30d_hip4_fills']>0)}")
print(f"Of which with HL perp activity only: {sum(1 for r in active_on_hl if r['hl_30d_hip4_fills']==0 and r['hl_30d_perp_fills']>0)}")

with open("../data/poly_x_hl_top30.json","w") as f:
    json.dump(results, f, indent=2)
print("\nSaved ../data/poly_x_hl_top30.json")
