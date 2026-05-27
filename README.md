# Polymarket participant segmentation

Reproducible SQL pack + analysis classifying Polymarket wallets into
behavioral cohorts (Pro-MM / Mid-MM / Hybrid-bot / HFT-taker / Active-mixed /
Active-retail) and measuring their share of volume by category and over time.

Built to answer one question for the Verdict (HIP-4 outcome markets on
Hyperliquid) diligence: **who actually drives volume on Polymarket?**

## TL;DR — audit status

- The SQL classifies actors on a **touched-volume basis**: every fill is
  counted once for the maker and once for the taker. This is the right
  denominator for participant share, but it is **2x single-counted venue
  notional**.
- The current SQL excludes known routing/system contracts both as raw
  trade counterparties and again **after proxy-to-owner mapping**. This
  matters because some system addresses can reappear as mapped owners.
- LP rewards are deduped across merkle claims and direct USDC transfers.
  Dust rewards are reported separately from material LP-reward
  confirmation.
- Existing files in `results/` are legacy exports from the pre-audit
  query version. Rerun the SQL before citing exact cohort percentages or
  dollar volumes.

See [docs/findings.md](docs/findings.md) for the full memo.

## What's in here

| Path | What |
|---|---|
| [docs/findings.md](docs/findings.md) | Strategic findings and Verdict implications |
| [docs/methodology.md](docs/methodology.md) | Classifier rules, contract exclusions, caveats |
| [queries/](queries/) | Per-query SQL files — one per analysis step, paste into Dune to reproduce |
| [results/](results/) | Legacy CSV dumps; rerun queries before citing exact numbers |

## How to reproduce

1. Open [dune.com](https://dune.com), create a new query, paste any
   file from [queries/](queries/), save, run.
2. Total cost ~300 credits across all 8 queries — well within the
   Dune free tier's 2,500/month allowance.
3. Recommended order: `01_action_enum_probe.sql` → `02_tags_probe.sql`
   → `03_other_category_probe.sql` → `04_cohort_x_category_30d.sql`
   (the main result) → `05_top20_per_cohort_with_lp.sql` (validation)
   → `06_cohort_per_quarter.sql` (run twice with different windows
   for the time trend) → `07_lp_rewards_top_recipients.sql`
   → `08_lp_rewards_concentration.sql`.

If you have a Dune Plus API key, see [docs/methodology.md](docs/methodology.md)
for the MCP-driven workflow we used to drive Dune from the command line.

## Key data sources

All free + on-chain via [Dune curated tables](https://docs.dune.com/data-catalog/curated/prediction-markets/polymarket/overview):

- `polymarket_polygon.market_trades` — every fill on CTF + NegRisk
- `polymarket_polygon.market_details` — market metadata + tags
- `polymarket_polygon.users_address_lookup` — proxy → owner mapping
- `polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed`
  + USDC transfers from `0xc28848...` — LP rewards ground truth

## What's NOT in here

- The Dune API key used to drive the live queries — rotate yours and
  set `DUNE_API_KEY` in your env.
- Cross-venue arber detection (Polymarket ↔ Kalshi) — needs Kalshi
  data, which isn't on Dune.
- Complete-set arber cohorting — Dune exposes split/merge events, but
  the current main classifier is only maker-share × cadence. Add
  split/merge features before making arber-share claims.
- PnL by cohort — would require position-state reconstruction.
- Wallet-level identity attribution (Wintermute, GSR, etc.) — needs
  manual labeling against public address registries.

## Caveats — read before citing any number

1. **Window is 30 days for the main analysis, with 90d-per-quarter
   historical comparisons.** Dune's free-tier 2-minute SQL timeout
   blocks longer windows in one shot. Chunk into 30d or 90d.

2. **Known routing/system contracts excluded** (`0xe111...996b`,
   `0xe2222...0f59`, `0x4bfb41...82e`, `0xc5d563...80a`) — they
   route NegRisk basket trades and/or appear as system actors. They are
   excluded both before and after owner mapping. There may be additional
   routers; the `n_fills <= 5M / window` safety net catches obvious ones.

3. **"Other" category can still be large** even after expanded tag
   matching. Most residual is null-tagged markets (often recurring
   high-frequency crypto/sports markets that lost their tags
   somewhere). Can be resolved with an external market-to-tag registry.

4. **MM/HFT/Retail are not mutually exclusive in real behavior** —
   the classifier forces them into discrete buckets via first-match
   rule order. Wallets near the boundaries (e.g., 60-70% maker
   share) can land in either MM or Hybrid-bot depending on
   threshold choice. The 9-cohort 2D view (`maker_share × cadence`)
   is more honest.

5. **Numbers shift ~5pp with threshold changes.** Treat as
   directional, not precise.
