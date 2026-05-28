# Polymarket participant segmentation

Reproducible SQL pack + analysis classifying Polymarket wallets into
behavioral cohorts (Pro-MM / Mid-MM / Hybrid-bot / HFT-taker / Active-mixed /
Active-retail) and measuring their share of volume by category and over time.

Built to answer one question for the Verdict (HIP-4 outcome markets on
Hyperliquid) diligence: **who actually drives volume on Polymarket?**

## How the analysis works

We classify every Polymarket wallet that traded in the trailing 30 days
into one of 6 behavioral cohorts using two axes:

| | **fast** (≥100 fills/day) | **med** (1–100 fills/day) |
|---|---|---|
| **highMkr** (≥70% maker share) | Pro-MM | Mid-MM |
| **midMkr** (30–70% maker share) | Hybrid-bot | Active-mixed |
| **lowMkr** (<30% maker share) | HFT-taker | Active-retail |

(A "slow" cadence cell exists in theory but is mathematically empty —
an "active day" requires a fill, so `fills/active_days ≥ 1` always.)

Wallets are aggregated to **owner level** via
`polymarket_polygon.users_address_lookup` so one MM running many proxy
wallets counts as one entity. Known routing contracts (NegRisk adapter
+ CTF Exchange + 2 others) are excluded both before and after
proxy-to-owner mapping; a behavioral safety net (`n_fills ≤ 5M /
window`) catches any router we missed.

Volume is reported two ways: **touched** (maker + taker amounts, used
for participant share) and **single-counted** (touched / 2 — the
Paradigm-style venue notional, comparable to public volume numbers).
LP rewards UNION merkle-distributor claims with direct USDC transfers
from the rewards wallet, deduped by `evt_tx_hash` to avoid
double-counting. Material LP confirmation requires ≥$1,000 all-time.

Full spec in [docs/methodology.md](docs/methodology.md). Reproducible
SQL in [queries/](queries/). External research cross-validation in
[docs/external_research.md](docs/external_research.md).

## TL;DR — May 2026 data (audited + rerun)

- Real Polymarket volume: **~$103M/day single-counted notional** over
  the trailing 30d — about half the headline number, matching
  Paradigm's December 2025 double-counting finding.
- Cohort split by touched volume: **MMs 39.9%, Bots 37.9%, Retail 22.2%**.
- **Retail share dropped from 33% (Q4 2025) to 22% (May 2026)** —
  Polymarket is professionalizing rapidly.
- LP reward concentration: top 3 owners = **20%** of all rewards (not
  34% as the pre-audit doc said); top 50 = **50%**. There's a 40%
  long tail across ~111,000 reward-earning owners.
- Pro-MM-fast top 20 wallets show strong LP-reward overlap: 17/20 have
  any reward history and 11/20 have material rewards (≥$1k). Use the
  material threshold for confirmation; dust rewards are weak evidence.
- **Zero of the 100 venue-wide top Polymarket wallets** (by 30d
  touched volume, query 11) are active on Hyperliquid HIP-4 — see
  [hip4_cross_venue/](hip4_cross_venue/) and
  [results/top100_wallets_venue_wide_30d.csv](results/top100_wallets_venue_wide_30d.csv).
  The venue-wide top-100 is 94% professional cohorts (51 Pro-MM + 23
  HFT-taker + 20 Hybrid-bot). 32 of them have material LP rewards
  (≥$1k). The MM migration path visible so far runs HL-perps → HIP-4,
  not Polymarket → HIP-4.
- Core `results/*.csv` are from the audited rerun. Snapshot CSVs are
  dated 2026-05-27; most SQL uses a rolling `CURRENT_TIMESTAMP` window,
  so reruns will drift unless you pin the `params` CTE dates.

### Volume vs headcount — the asymmetry that matters most

Distinct owner counts from Q1 2026 (90d) as a stable reference; trailing
30d counts are smaller but in the same ratio. Avg trade sizes from the
trailing 30d drilldown ([cohort_x_category_drilldown_30d.csv](results/cohort_x_category_drilldown_30d.csv)).

| Cohort | Distinct owners (Q1 2026, 90d) | % platform volume (T30d) | Avg trade size (T30d, $/fill) |
|---|---:|---:|---:|
| Pro-MM (highMkr_fast) | **8,095** | 31% | $22.70 overall; $7 crypto, $415 geopolitics |
| HFT-taker (lowMkr_fast) | 40,910 | 21% | $19.10 overall; $554 geopolitics |
| Hybrid-bot (midMkr_fast) | 11,603 | 17% | $26.73 overall |
| Active-retail (lowMkr_med) | **849,631** | 16% | $39.54 overall; $110 politics |
| Mid-MM (highMkr_med) | 160,046 | 9% | $89.16 overall; $552 geopolitics |
| Active-mixed (midMkr_med) | 183,232 | 6% | $51.85 overall |

**~221,000 MM/bot-classified owners generate ~78% of volume; ~1.03M
retail-tier owners generate ~22%.** The three fast professional cohorts
alone are ~60,600 owners and generate ~69% of volume. Polymarket has
retail in the sense of headcount, not in the sense of dollars. The
diligence question "who drives volume" answers itself once you see this
asymmetry: design for the professional cohort, even though the homepage
looks retail-facing.

A few category-level trade-size signals worth flagging:

- **Crypto fills average $7 (Pro-MM) to $33 (Mid-MM)** — the 5m/15m
  recurring binaries are tiny bets repeated thousands of times. Pro-MM
  fires 26.8M fills/30d on crypto alone at $7 avg = capital turns over
  fast, no inventory builds up.
- **Geopolitics fills average $400–$550 across all cohorts** — chunky,
  human-driven bets on Iran/Ukraine/world events. Even bots that trade
  this category trade it at much bigger size.
- **Politics retail averages $110/fill** — retail in politics is real
  money, not dust. ~167,000 retail wallets average $110/fill = retail
  takes politics seriously.
- **Sports fills $57 (retail) → $91 (Pro-MM)** — pretty flat across
  cohorts, suggesting standardized sports betting sizes regardless of
  who's behind the wallet.

Full per-cell breakdown (cohort × category × wallets / fills / avg
trade size) in
[results/cohort_x_category_drilldown_30d.csv](results/cohort_x_category_drilldown_30d.csv).

See [docs/findings.md](docs/findings.md) for the full memo.

## What's in here

| Path | What |
|---|---|
| [docs/findings.md](docs/findings.md) | Strategic findings and Verdict implications |
| [docs/methodology.md](docs/methodology.md) | Classifier rules, contract exclusions, caveats |
| [docs/external_research.md](docs/external_research.md) | External sources (Paradigm, Solidus, Chainalysis, Dune dashboards), cross-validation table, open questions |
| [queries/](queries/) | Per-query SQL files — one per analysis step, paste into Dune to reproduce |
| [results/](results/) | CSV dumps of every result table (from the audited rerun) |
| [hip4_cross_venue/](hip4_cross_venue/) | Bidirectional overlap check between HIP-4 and Polymarket wallets (sister analysis) |

## How to reproduce

1. Open [dune.com](https://dune.com), create a new query, paste any
   file from [queries/](queries/), save, run.
2. Total cost ~350 credits across the core queries — well within the
   Dune free tier's 2,500/month allowance.
3. Recommended order: `01_action_enum_probe.sql` → `02_tags_probe.sql`
   → `03_other_category_probe.sql` → `04_cohort_x_category_30d.sql`
   (the main result) → `05_top20_per_cohort_with_lp.sql` (validation)
   → `06_cohort_per_quarter.sql` (run twice with different windows
   for the time trend) → `07_lp_rewards_top_recipients.sql`
   → `08_lp_rewards_concentration.sql` → `09_cohort_x_category_drilldown.sql`
   → `10_cohort_x_category_maker_taker.sql`.
4. Optional but recommended for cross-venue work:
   `11_top_wallets_30d_with_lp.sql` returns a true venue-wide top-wallet
   sample; `05_top20_per_cohort_with_lp.sql` is a per-cohort validation
   sample and can be clipped by Dune API defaults if you do not request
   enough rows.

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
