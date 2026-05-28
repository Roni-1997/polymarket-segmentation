# Results

CSVs from the audited query versions, re-executed against Dune on
2026-05-27.

## Files

| File | Source query | Notes |
|---|---|---|
| `cohort_x_category_30d_clean.csv` | `04_cohort_x_category_30d.sql` | Trailing 30d; both touched and single-counted columns. |
| `top20_per_cohort_30d.csv` | `05_top20_per_cohort_with_lp.sql` | Top 20 wallets per cohort with LP confirmation flags. |
| `cohort_q1_2026.csv` | `06_cohort_per_quarter.sql` | Jan 1 – Apr 1, 2026. |
| `cohort_q4_2025.csv` | `06_cohort_per_quarter.sql` (dates swapped) | Oct 1 2025 – Jan 1 2026. |
| `lp_rewards_top25.csv` | `07_lp_rewards_top_recipients.sql` | Top 25 owners by deduped LP rewards. |
| `lp_rewards_concentration.csv` | `08_lp_rewards_concentration.sql` | Top-N concentration (3 / 10 / 20 / 50 / 100). |
| `other_tags_top30.csv` | `03_other_category_probe.sql` | What's leaking into the "Other" bucket. |
| `tags_top30.csv` | `02_tags_probe.sql` | Most common market tags. |
| `cohort_x_category_drilldown_30d.csv` | `09_cohort_x_category_drilldown.sql` | Long-format: per (cohort, category) wallet count, touched and single-counted volume, fills, avg trade size. |
| `cohort_x_category_maker_taker_30d.csv` | `10_cohort_x_category_maker_taker.sql` | Long-format: per (cohort, category) maker_vol, taker_vol, touched. Source for the three-view matrices (depth providers vs flow consumers). |

## Conventions

- **Touched volume** = maker-side + taker-side amounts. Use for
  participant share calculations.
- **Single-counted notional** = touched / 2. Use for venue volume
  ($/day) and comparisons to public Polymarket numbers.
- **lp_rewards_confirmed_1k** = TRUE if owner received ≥$1,000 in LP
  rewards (material participation). Dust rewards are weak evidence.
- All wallet addresses are aggregated to **owner** level via
  `polymarket_polygon.users_address_lookup`.
- System/router contracts are excluded both pre- and post-mapping.
  Hardcoded list in queries 04, 05, 06.

## What's not here

- PnL by cohort (would require position-state reconstruction).
- Cross-venue arber detection (needs Kalshi data).
- Wallet-level identity labels (Wintermute, GSR, etc.).
