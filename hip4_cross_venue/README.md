# HIP-4 × Polymarket cross-venue overlap

Status: **audited first pass, 2026-05-27**. Bidirectional check between Hyperliquid
HIP-4 outcome markets (live since 2026-05-02) and the Polymarket cohort
data in the rest of this repo. Answers the question *"do the same
operators trade both venues?"*

## TL;DR

Direct address overlap between the venues is **essentially zero** at the
professional tier:

- 0 of the 100 wallets in
  `results/top100_wallets_venue_wide_30d.csv` appear in the HIP-4
  top-127 captured here.
- 0 of the 100 wallets in the exported `results/top20_per_cohort_30d.csv`
  validation sample appear in the same HIP-4 sample.
- 0 of the 25 wallets in `results/lp_rewards_top25.csv` appear in the
  HIP-4 top-127.
- 2 of the top 30 wallets in that exported Polymarket validation sample
  have any Hyperliquid perp activity. **0** have visible HIP-4 activity.
- Of the top 30 HIP-4 address sample, 10 (33%) have ≥1 Polygon
  transaction, but none appear in the Polymarket cohort data here.
  Distribution suggests casual Polygon use, not pro Polymarket trading.

The cross-venue migration path that **does** exist runs HL-perps →
HIP-4. The HIP-4 maker cohort came from the Hyperliquid perps audience,
not Polymarket.

## What It Shows

The professional wallet sets are distinct in this sample. Structural
friction is material: Polygon vs HL signing, USDC.e vs USDC,
validator-vote settlement vs UMA, and EOA-direct flow vs Gnosis-Safe +
meta-tx flow.

## Headline tables

### Polymarket exported-sample top-30 → Hyperliquid

Queried HL `/info` `clearinghouseState` + `userFillsByTime` 2026-05-27.
The input is `results/top20_per_cohort_30d.csv` sorted by touched volume,
not a true venue-wide top-30 wallet export.

| Wallet | Poly 30d touched $ | Poly cohort | HL perp 30d fills | HL perp $ | HIP-4 fills |
|---|---:|---|---:|---:|---:|
| `0xba325e70…` | $70.9M | highMkr_fast | 53 | $100,000 | 0 |
| `0xf6ae6df5…` | $19.3M | highMkr_fast | 175 | $585,229 | 0 |
| *(other 28)* | various | various | 0 | $0 | 0 |

These two wallets are the identified bridges in this exported validation
sample between Polymarket pro-MM behavior and Hyperliquid signing
infrastructure. The claim should be re-run with
`queries/11_top_wallets_30d_with_lp.sql` before treating it as
venue-wide.

### HIP-4 top-30 address sample → Polygon

Queried `eth_getTransactionCount` via `polygon.drpc.org` 2026-05-27.

| HIP-4 wallet | HIP-4 tag | HIP-4 7d $ | Polygon nonce |
|---|---|---:|---:|
| `0xa67fdce2…` | Retail-directional | $788 | 890 |
| `0xdb77d93a…` | Browser-retail | $516 | 395 |
| `0x017e019d…` | MM-unhedged | $695 | 383 |
| `0xb565c088…` | Mostly-maker | $2,247 | 181 |
| `0x639520cf…` | MM-hedger | $7,090 | 31 |
| `0xd501ccbd…` | Mostly-maker | $56,837 | 18 |
| `0xf6afb4d9…` | Mostly-maker | $1,826 | 16 |
| `0x78eb1125…` | Browser-retail | $568 | 5 |
| `0x5ac1b6f6…` | Browser-retail | $806 | 4 |
| `0xe5dfc197…` | MM-hedger | $74 | 1 |
| *(other 20)* | various | various | 0 |

None of these 10 appear in `results/top20_per_cohort_30d.csv` or
`results/lp_rewards_top25.csv`. Polygon nonce > 0 only confirms generic
Polygon activity. A Polymarket-specific Dune query has been added under
`queries/`, but its results are not committed yet.

## HIP-4 cohort context

The HIP-4 sample was captured by direct subscription to the Hyperliquid
WebSocket `trades` channel for all 22 currently-live HIP-4 coin sides
(11 outcomes × 2 sides). 548 unique trades / 127 unique wallets observed
over ~11 hours of activity. The top 50 wallets in that WebSocket sample
were then deepened with 7d `userFillsByTime`. This is a
sample-selected top 50, not a venue-wide top 50.

| Tag | # wallets | $ notional (top-50) | Vol share within top-50 | Fill share |
|---|---:|---:|---:|---:|
| HFT-sweeper (3 distinct operators) | 3 | $160,241 | **48.9%** | 35.2% |
| Mostly-maker | 4 | $100,390 | 30.7% | 32.2% |
| MM-hedger (HL-native delta arb) | 12 | $44,068 | 13.5% | 20.6% |
| Browser-retail (multi-market taker) | 8 | $8,653 | 2.6% | 2.6% |
| Aggressive-taker | 1 | $5,937 | 1.8% | 2.5% |
| Hybrid maker-taker | 7 | $4,562 | 1.4% | 3.0% |
| MM-unhedged | 2 | $2,002 | 0.6% | 3.2% |
| Retail-directional | 4 | $1,677 | 0.5% | 0.7% |
| No visible HIP-4 fills in 7d response | 9 | $0 in 7d HIP-4 | — | — |

The sample-selected top 50 generated $327,530 of visible 7d HIP-4
notional in `userFillsByTime`, equal to 2.5% of the venue's published 7d
volume. Do **not** read this as "the venue top 50 only captured 2.5%":
these wallets were selected from an 11-hour WebSocket sample, not from
the full 7d population.

Venue-level context (huskereth Dune query 7427890, livefetch via HL
`/info`):

| Metric | Value |
|---|---:|
| HIP-4 1d notional | $1,757,175 |
| HIP-4 7d notional | $13,226,041 |
| HIP-4 7d trade count | 181,221 |
| HIP-4 7d unique markets | 37 |
| HIP-4 share of (HIP-4 + Polymarket + Kalshi) 1d | 0.68% |
| Polymarket implied 7d single-counted notional from this repo's T30d average | ~$724M |
| Polymarket implied 7d / HIP-4 7d ratio | ~55× |

## Methodology

### Polymarket pros → HL check
1. For venue-wide address overlap, intersect
   `results/top100_wallets_venue_wide_30d.csv` with
   `data/hip4_ws_wallets.json`.
2. For the deeper HL activity check, read
   `results/top20_per_cohort_30d.csv`, sort by
   `touched_vol_musd` desc, take top 30. This is an exported
   top-per-cohort validation sample.
3. For each wallet, call HL `/info` `clearinghouseState` (checks open
   positions) and `userFillsByTime` for the last 30 days.
4. Tag HL fills as HIP-4 (coin starts with `#` and integer ≥ 1000) vs.
   perp/spot otherwise.

### HIP-4 wallets → Polygon check
1. From `data/hip4_addrs.txt`, check the fixed top-30 address sample.
2. For each wallet, call `eth_getTransactionCount` on Polygon mainnet
   via `polygon.drpc.org` (free public RPC, no key). Nonce > 0 ⇒ has
   sent ≥1 Polygon transaction.

### HIP-4 cohort capture (upstream of this overlap check)
1. HL `/info` `outcomeMeta` to enumerate all 11 live HIP-4 outcomes.
2. WebSocket subscribe to `trades` channel for all 22 coin sides
   (outcome × YES/NO).
3. Aggregate captured trades by wallet (each `trades` message carries
   `users: [addr_a, addr_b]`); rank by appearance count.
4. For top 50 wallets, query HL `/info` `userFillsByTime` over the last
   7 days; classify with the heuristic in `scripts/classify_top50.py`.

Maker/taker classification on HIP-4 uses HL's native `crossed` flag in
the `userFillsByTime` response (`crossed: false` = maker; `crossed:
true` = taker). This is venue-attested side direction, not inferred.

## Limitations

1. **Polygon nonce ≠ Polymarket activity.** A Polygon transaction
   could be USDC bridging, QuickSwap, Aave, etc. A Dune SQL JOIN of
   these HIP-4 addresses against `polymarket_polygon.market_trades` now
   exists at `queries/01_hip4_addresses_polymarket_overlap.sql`, but it
   has not been executed and exported into `results/` yet.

2. **The HIP-4 sample is shallow.** 127 wallets were observed in the
   WebSocket capture, and only 50 were deepened with 7d fill history. The
   deep tail may contain Polymarket-experienced retail, but this sample
   is aimed at MM/pro-flow overlap, not exhaustive retail overlap.

3. **Polymarket data here is exported top-per-cohort sample + top-25
   LP.** Polymarket has ~1M+ wallets per `results/cohort_q1_2026.csv`
   (including ~926K Retail owners). Long-tail overlap is plausible but
   does not change the top-tier overlap finding.

4. **HL `userFillsByTime` caps at 2,000 rows.** For very active
   wallets, the most recent 2,000 perp fills can hide their HIP-4
   activity if HIP-4 represents <0.1% of their total trading. Therefore
   "no visible HIP-4 fills" means no HIP-4 fills in the returned API
   window, not a proof of lifetime non-participation.

## Reproducing

```bash
# Requires: python3, curl, gh CLI (for repo data), an installed
# `websockets` python library
pip install websockets

# 1. Snapshot all current HIP-4 markets from HL /info
python3 scripts/harvest_hip4.py            # → data/hip4_wallet_snapshot.json

# 2. (Optional) Run a longer WebSocket capture
python3 scripts/ws_capture.py &            # → data/hip4_trades.jsonl
sleep 300; kill %1
python3 scripts/aggregate_ws.py            # → data/hip4_ws_wallets.json

# 3. Classify the top 50 wallets with 7d userFillsByTime
python3 scripts/classify_top50.py          # → data/hip4_top50_classified.json

# 4. Reverse direction — check Polymarket pros on HL
python3 scripts/check_poly_on_hl.py        # → data/poly_x_hl_top30.json

# 5. Forward direction — check HIP-4 wallets on Polygon
python3 scripts/check_polygon.py           # → data/hip4_polygon_check.json
```

## Files

- `data/hip4_ws_wallets.json` — 127-wallet rollup from 548 WS trades.
- `data/hip4_top50_classified.json` — top 50 with 7d profile + tag.
- `data/hip4_polygon_check.json` — Polygon nonce per HIP-4 wallet.
- `data/poly_x_hl_top30.json` — HL activity for the top 30 wallets
  within the exported Polymarket validation sample.
- `data/hip4_addrs.txt` — comma-separated address list for downstream
  SQL.
- `queries/01_hip4_addresses_polymarket_overlap.sql` — Dune query to
  check the HIP-4 address sample against Polymarket-specific trades and
  proxy owners.
- `scripts/` — Python scripts that produced the above.

## Interpretation

The observed HIP-4 professional cohort is HL-native, not
Polymarket-derived. The sample shows 12 HIP-4 MM-hedgers with HL perp
activity and no visible Polymarket activity at the exported cohort-data
tier. Two Polymarket pro-MM wallets in the validation sample also traded
HL perps, but neither showed HIP-4 activity in the checked window.
