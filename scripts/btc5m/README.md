# BTC 5-minute pipeline

Pulls every trade on Polymarket's BTC 5-minute up/down markets from the public data-api and classifies
wallets into the cohort grid. All scripts read and write day files in `PM_DATA_DIR` (default `/tmp`).

| Script | What it does |
|---|---|
| `pull_both_legs_exact_threaded.py DAY [DAY ...]` | For each UTC day: lists the day's markets from the gamma API (with resolved outcomes), then pulls taker legs and all legs per market with transaction hashes. Pages newest-first in chunks of 10,000 (the API's offset cap) and restarts an inclusive `end=` query at the oldest second when a chunk is full, so busy markets are complete. Rate-limited per process (`RATE` requests per second, default 4; `THREADS` per process, default 6) and resumable. Writes `pm5m_outcomes_DAY.json`, `pm5m_taker_tx_DAY.json`, `pm5m_both_tx_DAY.json`. |
| `pull_taker_day.py DAY [DAY ...]` | Lighter taker-only pull without transaction hashes (`pm5m_fills_DAY.json`), enough for taker-side statistics. |
| `cohorts_v1_v2.py DAY [DAY ...]` | Single-day seven-cohort grid (maker share by cadence) and the proposed v2 split, with settlement PnL per cohort. Maker legs are identified by matching each all-legs record to the taker set on (transaction hash, wallet, side, size, price, outcome). |
| `day_features.py DAY [DAY ...]` | Per-day, per-wallet feature cache (`pm5m_wfeat_DAY.json`): fills, maker and taker volume, settlement PnL, sleep gap, active hours, exact-dollar share, two-sidedness, and the day's v1 and v2 cohort labels. Built once, so window grids run in seconds. |
| `grid_from_features.py START END OUT.json` | The seven-cohort grid and v2 over any window from the feature cache: one cohort per wallet, per calendar month and for the whole period, with persistence bands, gain concentration and a daily series. |
| `cohorts_window.py START END OUT.json` | The same grids over a window, one cohort per wallet (cadence per active day, maker share over the window), per calendar month and for the whole period, plus a daily series. |
| `features_and_rules.py` | Per-wallet daily features (fills, sleep gap, active hours, exact-dollar sizing, two-sidedness) and the machine/people rules used in the taker-side notes. |
| `trailing30_taker_stats.py` | Taker-side window statistics: machine share by day, profitability by persistence, cadence and size. |

Settlement PnL per leg: a buy of an outcome pays 1 if it wins, a sell the reverse. No fees (none charged on
these markets), no liquidity rewards, no positions carried across days.
