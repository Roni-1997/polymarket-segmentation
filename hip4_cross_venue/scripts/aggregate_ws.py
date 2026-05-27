"""Aggregate ../data/hip4_trades.jsonl into per-wallet rollup."""
import json, sys
from collections import defaultdict

OUTCOME_NAMES = {
    100: "Fallback", 101: "CPI<4.3%", 102: "CPI=4.3%", 103: "CPI>4.3%",
    104: "FedRate", 110: "UCL", 111: "BTC75668", 112: "RecFallback",
    113: "RecNamed0", 114: "RecNamed1", 115: "RecNamed2",
}

def coin_to_market(coin):
    if not coin.startswith("#"): return coin
    try:
        n = int(coin[1:])
        oid = n // 10
        side = n % 10
        return f"{OUTCOME_NAMES.get(oid, f'#{oid}')}/{side}"
    except: return coin

trades = []
seen_tid = set()
for line in open("../data/hip4_trades.jsonl"):
    try:
        t = json.loads(line)
        tid = t.get("tid")
        if tid in seen_tid:
            continue
        seen_tid.add(tid)
        trades.append(t)
    except: pass

print(f"Unique trades: {len(trades)}")

wallet_stats = defaultdict(lambda: {
    "trades": 0, "notional": 0.0, "markets": set(),
    "as_first": 0, "as_second": 0,
    "trades_per_market": defaultdict(int),
    "first_seen": None, "last_seen": None,
})

for t in trades:
    px = float(t["px"]); sz = float(t["sz"])
    notional = px * sz
    mkt = coin_to_market(t["coin"])
    users = t.get("users", [])
    ts = t.get("time", 0)
    for idx, u in enumerate(users):
        w = wallet_stats[u]
        w["trades"] += 1
        w["notional"] += notional
        w["markets"].add(mkt)
        w["trades_per_market"][mkt] += 1
        if idx == 0: w["as_first"] += 1
        else: w["as_second"] += 1
        if w["first_seen"] is None or ts < w["first_seen"]: w["first_seen"] = ts
        if w["last_seen"] is None or ts > w["last_seen"]: w["last_seen"] = ts

print(f"Unique wallets: {len(wallet_stats)}")

# Volume distribution
sorted_w = sorted(wallet_stats.items(), key=lambda x: -x[1]["trades"])
total_trade_slots = sum(s["trades"] for _,s in sorted_w)
total_notional = sum(s["notional"] for _,s in sorted_w) / 2  # each trade counted twice

print(f"Total trade-slots (2× trades): {total_trade_slots}")
print(f"Total notional (deduped): ${total_notional:,.0f}")
print()
print("=" * 110)
print(f"{'rk':<4}{'addr':<46}{'tr':>5}{'%':>5}{'$':>10}{'mk':>4}{'a1':>4}{'a2':>4}  top_mkt")
print("=" * 110)
cum = 0
for i, (a, s) in enumerate(sorted_w[:30], 1):
    cum += s["trades"]
    pct = 100 * cum / total_trade_slots
    top = max(s["trades_per_market"].items(), key=lambda x: x[1])
    n_str = f"${s['notional']:,.0f}"
    print(f"{i:<4}{a:<46}{s['trades']:>5}{pct:>4.0f}%{n_str:>10}{len(s['markets']):>4}{s['as_first']:>4}{s['as_second']:>4}  {top[0]}({top[1]})")

print()
print("=== Concentration ===")
print(f"Top 5  wallets: {100*sum(s['trades'] for _,s in sorted_w[:5])/total_trade_slots:.1f}% of trade-slots")
print(f"Top 10 wallets: {100*sum(s['trades'] for _,s in sorted_w[:10])/total_trade_slots:.1f}%")
print(f"Top 20 wallets: {100*sum(s['trades'] for _,s in sorted_w[:20])/total_trade_slots:.1f}%")
print(f"Top 30 wallets: {100*sum(s['trades'] for _,s in sorted_w[:30])/total_trade_slots:.1f}%")
print(f"Wallets with 1 trade-slot only: {sum(1 for _,s in sorted_w if s['trades']==1)} / {len(sorted_w)} ({100*sum(1 for _,s in sorted_w if s['trades']==1)/len(sorted_w):.0f}%)")
print(f"Wallets with >=10 trade-slots:   {sum(1 for _,s in sorted_w if s['trades']>=10)}")
print(f"Wallets with >=50 trade-slots:   {sum(1 for _,s in sorted_w if s['trades']>=50)}")
print(f"Wallets with >=100 trade-slots:  {sum(1 for _,s in sorted_w if s['trades']>=100)}")

# Per-market activity
print("\n=== Trades per market ===")
mkt_count = defaultdict(int)
for t in trades:
    mkt_count[coin_to_market(t["coin"])] += 1
for m, c in sorted(mkt_count.items(), key=lambda x: -x[1])[:25]:
    print(f"  {m:<25} {c}")

# Save full output
out = []
for a, s in sorted_w:
    out.append({
        "addr": a, "trades": s["trades"], "notional": s["notional"],
        "markets": list(s["markets"]),
        "as_first": s["as_first"], "as_second": s["as_second"],
        "trades_per_market": dict(s["trades_per_market"]),
        "first_seen_ms": s["first_seen"], "last_seen_ms": s["last_seen"],
    })
with open("../data/hip4_ws_wallets.json", "w") as f:
    json.dump({
        "trade_count": len(trades),
        "wallet_count": len(wallet_stats),
        "total_notional": total_notional,
        "wallets": out
    }, f, indent=2)
print("\nSaved ../data/hip4_ws_wallets.json")
