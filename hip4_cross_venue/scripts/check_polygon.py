import json
import subprocess
import time

from common import DATA_DIR, write_json

addrs = [
    a.strip().lower()
    for a in (DATA_DIR / "hip4_addrs.txt").read_text().split(",")
    if a.strip()
]
RPCS = ["https://polygon.drpc.org", "https://1rpc.io/matic", "https://polygon-bor-rpc.publicnode.com"]

def get_nonce(addr):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getTransactionCount","params":[addr,"latest"]})
    for rpc in RPCS:
        try:
            r = subprocess.run(
                ["curl","-sS","--max-time","20","-X","POST", rpc,
                 "-H","Content-Type: application/json",
                 "-A","Mozilla/5.0",
                 "-d", payload],
                capture_output=True, text=True, timeout=25
            )
            d = json.loads(r.stdout)
            if "result" in d and d["result"]:
                return int(d["result"], 16), rpc
        except Exception:
            continue
    return None, None

results = []
for i, addr in enumerate(addrs, 1):
    nonce, rpc = get_nonce(addr)
    results.append({"addr": addr, "polygon_nonce": nonce, "rpc": rpc})
    marker = "✓ POLYGON ACTIVE" if (nonce and nonce > 0) else ("(no polygon tx)" if nonce==0 else "RPC_ERR")
    rpc_short = rpc.split("//")[1][:20] if rpc else "-"
    print(f"{i:>2}. {addr} nonce={str(nonce):>6} via {rpc_short:<22}  {marker}")
    time.sleep(0.7)
    if i % 5 == 0:
        write_json(DATA_DIR / "hip4_polygon_check.json", results)

write_json(DATA_DIR / "hip4_polygon_check.json", results)

active = [r for r in results if r["polygon_nonce"] and r["polygon_nonce"] > 0]
zero = [r for r in results if r["polygon_nonce"] == 0]
err = [r for r in results if r["polygon_nonce"] is None]
print(f"\n=== Summary ===")
print(f"Total: {len(results)}, with Polygon tx: {len(active)}, no Polygon tx: {len(zero)}, RPC error: {len(err)}")
print()
print("Polygon-active wallets (sorted by nonce):")
for r in sorted(active, key=lambda x: -x["polygon_nonce"]):
    print(f"  {r['addr']} nonce={r['polygon_nonce']:>6}")
