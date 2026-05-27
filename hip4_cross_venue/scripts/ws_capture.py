"""Subscribe to HL WebSocket trades for all HIP-4 coins, append to a JSONL file.
Runs until killed."""
import asyncio, json, time, sys
import websockets

from common import DATA_DIR, hl_info

WS = "wss://api.hyperliquid.xyz/ws"

def current_hip4_coins():
    meta = hl_info({"type": "outcomeMeta"}, timeout=20)
    if not isinstance(meta, dict):
        raise RuntimeError("failed to fetch Hyperliquid outcomeMeta")
    coins = []
    for outcome in meta.get("outcomes", []):
        oid = int(outcome["outcome"])
        for side_idx, _side in enumerate(outcome.get("sideSpecs", [])):
            coins.append(f"#{oid*10 + side_idx}")
    return coins

OUT = DATA_DIR / "hip4_trades.jsonl"
LOG = DATA_DIR / "hip4_ws.log"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
    with LOG.open("a") as f:
        f.write(line)
    sys.stdout.write(line)
    sys.stdout.flush()

async def run():
    coins = current_hip4_coins()
    log(f"connecting to {WS}, {len(coins)} coins")
    async with websockets.connect(WS, ping_interval=20, ping_timeout=20) as ws:
        for c in coins:
            sub = {"method": "subscribe", "subscription": {"type": "trades", "coin": c}}
            await ws.send(json.dumps(sub))
        log(f"sent {len(coins)} subscription messages")

        n_trades = 0
        n_other = 0
        start = time.time()
        last_report = start
        with OUT.open("a") as f:
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                ch = msg.get("channel")
                if ch == "trades":
                    data = msg.get("data", [])
                    for t in data:
                        f.write(json.dumps(t) + "\n")
                    n_trades += len(data)
                    f.flush()
                else:
                    n_other += 1
                now = time.time()
                if now - last_report > 30:
                    elapsed = int(now - start)
                    log(f"t+{elapsed}s trades={n_trades} other_msgs={n_other}")
                    last_report = now

if __name__ == "__main__":
    # Truncate old file
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("")
    LOG.write_text("")
    while True:
        try:
            asyncio.run(run())
        except Exception as e:
            log(f"error {type(e).__name__}: {e} — reconnecting in 3s")
            time.sleep(3)
