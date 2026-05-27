"""Subscribe to HL WebSocket trades for all HIP-4 coins, append to a JSONL file.
Runs until killed."""
import asyncio, json, time, sys, os
import websockets

WS = "wss://api.hyperliquid.xyz/ws"

# All current HIP-4 outcome coin sides (from outcomeMeta as of 2026-05-27)
OUTCOMES = [100, 101, 102, 103, 104, 110, 111, 112, 113, 114, 115]
COINS = []
for o in OUTCOMES:
    COINS.append(f"#{o*10}")     # side 0
    COINS.append(f"#{o*10+1}")   # side 1

OUT = "../data/hip4_trades.jsonl"
LOG = "../data/hip4_ws.log"

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
    with open(LOG, "a") as f:
        f.write(line)
    sys.stdout.write(line)
    sys.stdout.flush()

async def run():
    log(f"connecting to {WS}, {len(COINS)} coins")
    async with websockets.connect(WS, ping_interval=20, ping_timeout=20) as ws:
        for c in COINS:
            sub = {"method": "subscribe", "subscription": {"type": "trades", "coin": c}}
            await ws.send(json.dumps(sub))
        log(f"sent {len(COINS)} subscription messages")

        n_trades = 0
        n_other = 0
        start = time.time()
        last_report = start
        with open(OUT, "a") as f:
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
    open(OUT, "w").close()
    open(LOG, "w").close()
    while True:
        try:
            asyncio.run(run())
        except Exception as e:
            log(f"error {type(e).__name__}: {e} — reconnecting in 3s")
            time.sleep(3)
