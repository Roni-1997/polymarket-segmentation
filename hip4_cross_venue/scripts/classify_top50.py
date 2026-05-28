"""Pull 7d userFillsByTime for sample-selected top wallets and classify."""
import time
from collections import defaultdict, Counter

from common import DATA_DIR, hl_info, is_hip4_coin, read_json, write_json

snap = read_json(DATA_DIR / "hip4_ws_wallets.json")
wallets = snap["wallets"]

end_ms = int(time.time() * 1000)
start_ms = end_ms - 7*24*60*60*1000

def fetch_user_fills(addr):
    return hl_info(
        {"type": "userFillsByTime", "user": addr, "startTime": start_ms, "endTime": end_ms, "aggregateByTime": False},
        timeout=20,
    )

profiles = []
N = 50
for i, w in enumerate(wallets[:N], 1):
    addr = w["addr"]
    fills = fetch_user_fills(addr)
    api_error = fills is None
    if not isinstance(fills, list): fills = []
    hip4 = [f for f in fills if is_hip4_coin(f.get("coin",""))]
    perp = [f for f in fills if not is_hip4_coin(f.get("coin",""))]

    hip4_mkr = sum(1 for f in hip4 if f.get("crossed") == False)
    hip4_tkr = sum(1 for f in hip4 if f.get("crossed") == True)
    hip4_total = len(hip4)
    hip4_notional = sum(float(f.get("px",0)) * float(f.get("sz",0)) for f in hip4)
    hip4_mkts = set(f["coin"] for f in hip4)
    hip4_avg_ticket = hip4_notional / max(hip4_total, 1)

    perp_notional = sum(float(f.get("px",0)) * float(f.get("sz",0)) for f in perp)
    perp_total = len(perp)

    mkr_ratio = hip4_mkr / max(hip4_total, 1)
    hedge_ratio = perp_notional / max(hip4_notional, 1)

    # Classify
    if api_error:
        tag = "api-error"
    elif hip4_total == 0:
        tag = "no-visible-HIP4-fills"
    elif mkr_ratio >= 0.9 and perp_notional > max(hip4_notional, 100) * 0.3:
        tag = "MM-hedger"
    elif mkr_ratio >= 0.9:
        tag = "MM-unhedged"
    elif mkr_ratio <= 0.1 and hip4_total >= 200 and len(hip4_mkts) >= 5:
        tag = "Fast-sweeper"
    elif mkr_ratio <= 0.1 and hip4_total >= 50:
        tag = "Aggressive-taker"
    elif mkr_ratio <= 0.1 and len(hip4_mkts) >= 3:
        tag = "Browser-retail"
    elif mkr_ratio <= 0.1:
        tag = "Retail-directional"
    elif 0.3 <= mkr_ratio <= 0.7:
        tag = "Hybrid"
    else:
        tag = "Mostly-maker"

    profiles.append({
        "rank": i, "addr": addr, "tag": tag,
        "hip4_total": hip4_total, "hip4_mkr": hip4_mkr, "hip4_tkr": hip4_tkr,
        "mkr_pct": round(100*mkr_ratio, 0),
        "hip4_notional": round(hip4_notional, 0),
        "hip4_mkts": len(hip4_mkts),
        "avg_ticket": round(hip4_avg_ticket, 1),
        "perp_total": perp_total, "perp_notional": round(perp_notional, 0),
        "perp_hedge_ratio": round(hedge_ratio, 1),
        "api_error": api_error,
    })
    print(f"{i:>2}. {addr[:10]}.. {tag:<22} hip4={hip4_total:>5} mkr={int(mkr_ratio*100):>3}% mkts={len(hip4_mkts):>2} $={hip4_notional:>10,.0f} perpN=${perp_notional:>10,.0f} hedgeX={hedge_ratio:>5.1f}")

tag_counts = Counter(p["tag"] for p in profiles)
tag_vol = defaultdict(float)
tag_n = defaultdict(int)
for p in profiles:
    tag_vol[p["tag"]] += p["hip4_notional"]
    tag_n[p["tag"]] += p["hip4_total"]
total_v = sum(tag_vol.values())
total_n = sum(tag_n.values())

print("\n=== Tag distribution (top 50 wallets) ===")
print(f"{'tag':<25}{'count':>7}{'volume$':>14}{'vol_%':>7}{'fills':>9}{'fill_%':>8}")
for tag, ct in tag_counts.most_common():
    v = tag_vol[tag]
    f = tag_n[tag]
    print(f"{tag:<25}{ct:>7}{('$'+f'{v:,.0f}'):>14}{(100*v/max(total_v,1)):>6.1f}%{f:>9}{(100*f/max(total_n,1)):>7.1f}%")

print(f"\nTop 50 cumulative HIP-4 notional (7d): ${total_v:,.0f}")
print(f"Top 50 cumulative HIP-4 fills (7d):    {total_n:,}")
print(f"(Venue 7d: $13,226,041 / 181,221 fills — sample-selected top 50 visible profile is ~{100*total_v/13226041:.1f}% notional, {100*total_n/181221:.1f}% fills)")

write_json(DATA_DIR / "hip4_top50_classified.json", profiles)
print(f"\nSaved {DATA_DIR / 'hip4_top50_classified.json'}")
