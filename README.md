# Polymarket participant segmentation

Reproducible SQL pack + analysis classifying Polymarket wallets into
behavioral cohorts (Pro-MM / Mid-MM / Hybrid-bot / HFT-taker / Active-mixed /
Active-retail) and measuring their share of volume by category and over time.

Built to answer one question for the Verdict (HIP-4 outcome markets on
Hyperliquid) diligence: **who actually drives volume on Polymarket?**

## TL;DR — what we found (May 2026 data)

- Polymarket's real volume is **~$210M/day notional** — ~50% of headline,
  matching Paradigm's December 2025 finding that OrderFilled events
  double-count via NegRisk router contracts.
- Cohort distribution today: **MMs ~40%, Bots ~38%, Retail ~22%**.
- Crypto markets are **~76% automated** counterparties. Retail is
  effectively absent.
- Politics is the **most retail-heavy** category (Active-retail = 26% of
  politics volume, the largest cohort there).
- Pro-MM cohort top-20 are **17/20 LP-rewards-confirmed** — the
  classifier finds the real MM oligopoly.
- **Retail share dropped 11 percentage points** in 6 months (Q4 2025 →
  May 2026) — Polymarket is professionalizing rapidly.

See [docs/findings.md](docs/findings.md) for the full memo.

## What's in here

| Path | What |
|---|---|
| [docs/findings.md](docs/findings.md) | Strategic findings and Verdict implications |
| [docs/methodology.md](docs/methodology.md) | Classifier rules, contract exclusions, caveats |
| [queries/](queries/) | Per-query SQL files — one per analysis step, paste into Dune to reproduce |
| [results/](results/) | CSV dumps of every result table |

## How to reproduce

1. Open [dune.com](https://dune.com), create a new query, paste any
   file from [queries/](queries/), save, run.
2. Total cost ~300 credits across all 7 queries — well within the
   Dune free tier's 2,500/month allowance.
3. Recommended order: `01_action_enum_probe.sql` → `02_tags_probe.sql`
   → `03_other_category_probe.sql` → `04_cohort_x_category_30d.sql`
   (the main result) → `05_top20_per_cohort_with_lp.sql` (validation)
   → `06_cohort_per_quarter.sql` (run twice with different windows
   for the time trend) → `07_lp_rewards_top_recipients.sql`.

If you have a Dune Plus API key, see [docs/methodology.md](docs/methodology.md)
for the MCP-driven workflow we used to drive Dune from the command line.

## Key data sources

All free + on-chain via [Dune curated tables](https://docs.dune.com/data-catalog/curated/prediction-markets/polymarket/overview):

- `polymarket_polygon.market_trades` — every fill on CTF + NegRisk
- `polymarket_polygon.market_details` — market metadata + tags
- `polymarket_polygon.users_address_lookup` — proxy → owner mapping
- `polymarket_polygon.ctf_evt_positionsplit` / `ctf_evt_positionsmerge`
  — complete-set arber signal
- `polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed`
  + USDC transfers from `0xc28848...` — LP rewards ground truth

## What's NOT in here

- The Dune API key used to drive the live queries — rotate yours and
  set `DUNE_API_KEY` in your env.
- Cross-venue arber detection (Polymarket ↔ Kalshi) — needs Kalshi
  data, which isn't on Dune.
- PnL by cohort — would require position-state reconstruction.
- Wallet-level identity attribution (Wintermute, GSR, etc.) — needs
  manual labeling against public address registries.

## Caveats — read before citing any number

1. **Window is 30 days for the main analysis, with 90d-per-quarter
   historical comparisons.** Dune's free-tier 2-minute SQL timeout
   blocks longer windows in one shot. Chunk into 30d or 90d.

2. **Two routing contracts excluded** (`0xe111...996b`,
   `0xe2222...0f59`, `0x4bfb41...82e`, `0xc5d563...80a`) — they
   route NegRisk basket trades and were inflating "HFT-taker"
   volume by ~$3B/month. There may be additional routers; the
   `n_fills <= 5M / quarter` safety net catches obvious ones.

3. **"Other" category is ~35% of volume** even after expanded tag
   matching. Most is genuinely null-tagged markets (recurring
   high-frequency crypto/sports markets that lost their tags
   somewhere). Can be resolved with an external market-to-tag
   registry.

4. **MM/HFT/Retail are not mutually exclusive in real behavior** —
   the classifier forces them into discrete buckets via first-match
   rule order. Wallets near the boundaries (e.g., 60-70% maker
   share) can land in either MM or Hybrid-bot depending on
   threshold choice. The 9-cohort 2D view (`maker_share × cadence`)
   is more honest.

5. **Numbers shift ~5pp with threshold changes.** Treat as
   directional, not precise.
