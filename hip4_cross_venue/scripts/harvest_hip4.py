import json, subprocess
from collections import defaultdict

outcomes = [
    (100, "Fallback", ["Yes","No"]),
    (101, "CPI<4.3%", ["Yes","No"]),
    (102, "CPI=4.3%", ["Yes","No"]),
    (103, "CPI>4.3%", ["Yes","No"]),
    (104, "FedRate", ["Change","NoChange"]),
    (110, "UCL", ["PSG","Arsenal"]),
    (111, "BTC75668", ["Yes","No"]),
    (112, "RecFallback", ["Yes","No"]),
    (113, "RecNamed0", ["Yes","No"]),
    (114, "RecNamed1", ["Yes","No"]),
    (115, "RecNamed2", ["Yes","No"]),
]

trades_per_coin = {}
for oid, name, sides in outcomes:
    for side_idx, side_name in enumerate(sides):
        coin = f"#{oid*10 + side_idx}"
        try:
            r = subprocess.run(
                ["curl", "-s", "-X", "POST", "https://api.hyperliquid.xyz/info",
                 "-H", "Content-Type: application/json",
                 "-d", '{"type":"recentTrades","coin":"' + coin + '"}'],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(r.stdout) if r.stdout.strip() else None
            if data:
                trades_per_coin[coin] = (name, side_name, data)
        except Exception:
            pass

print(f"Markets with trade data: {len(trades_per_coin)}")

wallet_stats = defaultdict(lambda: {
    "trades": 0, "notional": 0.0, "markets": set(),
    "as_first": 0, "as_second": 0,
    "trades_per_market": defaultdict(int),
})

all_trades = []
for coin, (name, side_name, data) in trades_per_coin.items():
    for t in data:
        users = t.get("users", [])
        px = float(t["px"]); sz = float(t["sz"])
        notional = px * sz
        all_trades.append({"coin": coin, "name": name, "side": side_name, "px": px, "sz": sz,
                           "notional": notional, "users": users,
                           "side_dir": t.get("side"), "time": t.get("time")})
        if len(users) >= 1:
            w = wallet_stats[users[0]]
            w["trades"] += 1; w["notional"] += notional; w["markets"].add(name)
            w["as_first"] += 1; w["trades_per_market"][name] += 1
        if len(users) >= 2:
            w = wallet_stats[users[1]]
            w["trades"] += 1; w["notional"] += notional; w["markets"].add(name)
            w["as_second"] += 1; w["trades_per_market"][name] += 1

print(f"Total trades captured: {len(all_trades)}")
print(f"Unique wallets observed: {len(wallet_stats)}")
print()

print("=" * 120)
hdr = "rank addr                                          trades  notional       mkts  as1  as2   top_market"
print(hdr)
print("=" * 120)
sorted_wallets = sorted(wallet_stats.items(), key=lambda x: x[1]["trades"], reverse=True)
for i, (addr, s) in enumerate(sorted_wallets[:40], 1):
    top_mkt = max(s["trades_per_market"].items(), key=lambda x: x[1])
    notional_str = f"${s['notional']:,.0f}"
    top_str = f"{top_mkt[0]}({top_mkt[1]})"
    print(f"{i:<4} {addr:<44} {s['trades']:>6} {notional_str:>13} {len(s['markets']):>5} {s['as_first']:>4} {s['as_second']:>4}  {top_str}")

print()
print(f"Wallets >1 trade: {sum(1 for _,s in wallet_stats.items() if s['trades']>1)}")
print(f"Wallets =1 trade: {sum(1 for _,s in wallet_stats.items() if s['trades']==1)}")

with open("../data/hip4_wallet_snapshot.json", "w") as f:
    out = []
    for addr, s in sorted_wallets:
        out.append({
            "address": addr, "trades": s["trades"], "notional": s["notional"],
            "markets": list(s["markets"]),
            "as_first": s["as_first"], "as_second": s["as_second"],
            "trades_per_market": dict(s["trades_per_market"]),
        })
    json.dump({"all_trades": all_trades, "wallets": out}, f, indent=2)
print("\nSaved ../data/hip4_wallet_snapshot.json")
