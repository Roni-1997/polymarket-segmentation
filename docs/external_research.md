# External research — sources, comparisons, open questions

This doc maps each substantive claim in [findings.md](findings.md) to
the external source we cross-validated against, and flags where our
numbers agree or diverge.

## 1. Cross-validation table

| Our claim (May 2026) | Source | Their claim | Agreement |
|---|---|---|---|
| Real volume ~$103M/day single-counted | [Paradigm, Dec 2025](https://www.paradigm.xyz/2025/12/polymarket-volume-is-being-double-counted) | Headline volume ~2× overstated via OrderFilled double-counting; real Oct/Nov 2024 monthly volume ~$1.25B vs $2.5B reported | ✓ Matches the methodology; our $103M/day single-counted = ~$3.1B/month for May 2026 |
| 67–78% of platform flow is automated counterparties | filarm Dune classification (see §3 below) | Fast-market taker volume was 55–62% bots in Feb–Mar 2026 | △ Same direction; our number higher partly because we count maker side too |
| Pro-MM-fast top-20 have 17/20 any LP rewards and 11/20 material LP rewards (≥$1k threshold) | LP rewards distribution from `MerkleDistributor_evt_Claimed` | n/a — we validate against on-chain rewards | ✓ Directionally validates the classifier; use ≥$1k for strong MM-program evidence |
| Top 10 LP-reward owners capture 30% of all rewards | [Solidus Labs / Coindesk, Apr 2026](https://www.coindesk.com/markets/2026/04/29/a-tiny-group-is-winning-on-polymarket-as-under-1-of-wallets-take-half-the-profits) | 0.55% of profitable maker wallets capture 50% of PROFIT gains in politics markets | △ Different metric (rewards vs profit), same direction. Profit concentration likely more extreme than reward concentration. We have not measured PnL. |
| Politics is the most retail-heavy category | Long-standing folklore | Same | ✓ |
| Sports is the largest tagged category by volume (30%); null-tagged Other is larger (35%) | filarm Polymarket Activity dashboard, datadashboards Polymarket Overview | Sports surged in 2025–2026, esports especially | ✓ Directionally, but tag coverage remains incomplete |
| Whale / informed directional share is not separately measured in this repo | [Chainalysis Théo cluster reporting](https://www.chainalysis.com/) | 11 wallets identified as Théo cluster | Open item. The current classifier is maker-share × cadence, not a whale registry. |
| Retail share collapsed 10.7% → 5.3% in 6 months (strict <10/day def) | n/a — novel finding | n/a | ⊕ Unique to this analysis. Possible cause: capital migrated to Kalshi (per Paradigm's note that Kalshi overtook Polymarket in Q1 2026) |
| 0/100 venue-wide top Polymarket wallets active on HIP-4; 0/25 LP-reward recipients on HIP-4 | [hip4_cross_venue/](../hip4_cross_venue/) (sister analysis) | n/a | ⊕ Cross-venue finding from `results/top100_wallets_venue_wide_30d.csv` and the HIP-4 127-wallet sample. HIP-4 maker activity appears HL-native in this sample. |

Legend: ✓ matches, △ partial / directional, ✗ contradicts folklore, ⊕ novel claim.

---

## 2. Primary sources

### Paradigm — "Polymarket Volume Is Being Double-Counted" (Dec 2025)

- **URL**: https://www.paradigm.xyz/2025/12/polymarket-volume-is-being-double-counted
- **Author**: Storm Slivkoff (Research Partner, Paradigm)
- **TL;DR**: Polymarket emits separate OrderFilled events for the maker
  and taker sides of every trade. Dashboards that sum both
  double-count. Real volume is ~half the headline number.
- **What this means for us**: Our `total_touched_musd` column is
  effectively the same as the "double-counted" number; the
  `equivalent_single_counted_musd` (= touched / 2) is what Paradigm
  recommends as the correct venue volume metric.
- **Caveat to disclose if citing**: Paradigm is an investor in Kalshi,
  a direct Polymarket competitor. The methodology is correct and
  independently verifiable on-chain, but the messaging is not neutral.
- **Secondary coverage**:
  - [Cointelegraph](https://cointelegraph.com/news/polymarket-trading-volume-double-counted-research)
  - [Unchained](https://unchainedcrypto.com/paradigm-claims-polymarket-trading-figures-are-double-counted/)
  - [Protos](https://protos.com/polymarket-volume-misreported-as-data-providers-double-count-trades-report/)

### Solidus Labs — "Polymarket Under the Polygraph" (Apr 2026)

- **Coverage**: [Coindesk](https://www.coindesk.com/markets/2026/04/29/a-tiny-group-is-winning-on-polymarket-as-under-1-of-wallets-take-half-the-profits) · [Yellow](https://yellow.com/news/polymarket-1-percent-wallets-half-politics-profits) · [Crypto-Reporter](https://www.crypto-reporter.com/newsfeed/polymarket-under-the-polygraph-solidus-report-uncovers-systemic-risks-in-onchain-prediction-markets-125529/)
- **Period studied**: December 2025 – February 2026
- **TL;DR**: Across politics markets, **0.55% of profitable maker
  wallets captured 50% of $16M in maker-side gains**. 0.26% of
  profitable taker wallets captured ~50% of taker gains. Also flagged
  ~15% of volume in some markets as wash trading consistent with POLY
  airdrop farming.
- **What this means for us**: Volume concentration ≠ profit
  concentration. Our top-10 LP-reward owners get 30% of rewards;
  Solidus's number says top 0.55% capture 50% of *profit*. Profit
  concentration is more extreme because it's a derivative of trading
  edge, not capital deployment.
- **Caveat**: 15% wash trading flag is material. If you re-run our
  classifier on a subset that excludes wash patterns (paired YES+NO
  positions within the same wallet/owner, same condition_id), the
  Systematic-mixed and Retail cohorts will likely shrink further.

### Chainalysis — Théo cluster identification

- **URL**: [chainalysis.com blog](https://www.chainalysis.com/blog/)
  (specific post URL varies by date; search "Polymarket Théo")
- **Claim**: A single trader ("Théo") operates ~11 wallets that bet
  ~$30M on the 2024 US election outcome.
- **What this means for us**: The current repo does not maintain a
  known-whale registry, so whale/informed directional flow is not
  separately measured. Add a manually curated wallet registry before
  making whale-share claims.

---

## 3. Dune dashboards used or referenced

### Forked into this repo

| Query ID | Title | What we used it for |
|---|---|---|
| [5989757](https://dune.com/queries/5989757) | Polymarket Top Liquidity Providers by Rewards Earnt | LP rewards source — forked into our `07_lp_rewards_top_recipients.sql` with dedup fix |

### Referenced for benchmarking

| Query / dashboard | URL | What it covers |
|---|---|---|
| filarm — Bot Analysis by Duration | [dune.com/queries/6841281](https://dune.com/queries/6841281) | Taker-frequency classification used in original memo's "55–62% bots in fast markets" claim |
| filarm — Polymarket Activity | [dune.com/filarm/polymarket-activity](https://dune.com/filarm/polymarket-activity) | DAU, txns, volume, market types, NegRisk vs CTF, bet-size distributions |
| Polymarket — Volume (official-style) | [dune.com/queries/6545441](https://dune.com/queries/6545441) | Notional + maker + taker USDC volume |
| defioasis — Polymarket Trader Cashflow PnL | [dune.com/defioasis/polymarket-pnl](https://dune.com/defioasis/polymarket-pnl) | Per-wallet PnL via USDC in/out — what we'd JOIN if we extend the analysis to profit concentration |
| Polymarket — Open Interest | [dune.com/queries/6555478](https://dune.com/queries/6555478) | OI = open positions × last price |
| Polymarket — TVL | [dune.com/queries/6588784](https://dune.com/queries/6588784) | USDC.e in conditional tokens + neg-risk collateral |
| datadashboards — Polymarket Overview | [dune.com/datadashboards/polymarket-overview](https://dune.com/datadashboards/polymarket-overview) | Category breakdown, active wallets — cross-check filarm |
| datadashboards — Prediction Markets (cross-platform) | [dune.com/datadashboards/prediction-markets](https://dune.com/datadashboards/prediction-markets) | Polymarket + Kalshi + Hyperliquid + Limitless + Myriad |
| gateresearch — Polymarket Builders | [dune.com/gateresearch/pmbuilders](https://dune.com/gateresearch/pmbuilders) | Volume routed via Builder Program (Telegram bots, copy-trading apps) |
| hildobby — Polymarket | [dune.com/hildobby/polymarket](https://dune.com/hildobby/polymarket) | Volume, OI, addresses, TVL — community dashboard listed in Polymarket docs |
| no__hive — Polymarket Airdrop Checker | [dune.com/no__hive/polymarket-airdrop-checker](https://dune.com/no__hive/polymarket-airdrop-checker) | Per-wallet volume aggregation (airdrop framing) |

### Not on Dune

| Source | URL | Notes |
|---|---|---|
| Blockworks Polymarket dashboard | [blockworks.com/analytics/polymarket](https://blockworks.com/analytics/polymarket) | Runs on Allium pipeline (not Dune). Visual benchmark only — can't extract queries. After Paradigm's report, Blockworks updated to remove double-counting. |
| Kalshi public API | [kalshi.com/api](https://kalshi.com/api) | Required for cross-venue arb detection (Polymarket ↔ Kalshi). Gated; FinFeedAPI / AhaSignals offer mirror feeds. |

---

## 4. Polymarket documentation

| Topic | URL |
|---|---|
| Contract addresses | https://docs.polymarket.com/concepts/contracts |
| Blockchain data resources | https://docs.polymarket.com/resources/blockchain-data |
| CLOB API | https://docs.polymarket.com/quickstart/orders/clob-api-introduction |
| Maker rewards program | https://docs.polymarket.com/clob-overview/rewards-program (may have moved — search "Polymarket maker rewards") |

---

## 5. Open questions where more external data would tighten the analysis

1. **PnL by cohort.** Solidus measured profit concentration in politics
   markets only and for a 3-month window. Reproducing across all
   categories and longer windows would let us check whether the
   "0.55% of wallets capture 50% of profit" claim generalizes. Source:
   defioasis PnL dashboard + position-state reconstruction (~1–2 weeks).

2. **Cross-venue arber share.** Paradigm noted Kalshi overtook
   Polymarket by Q1 2026. The retail collapse in our data (10.7% →
   5.3% under strict def) and the parallel shrinking of Systematic-mixed
   (11.6% → 5.2%) may reflect migration to Kalshi. Confirming requires Kalshi
   API access + matching wallet timestamps across the two venues.

3. **Wallet-level firm attribution.** We can identify the LP-reward
   oligopoly top 10 by address, but not by firm (Wintermute, GSR,
   B2C2, Amber, etc.). Manual labeling against public registries +
   on-chain clustering would close this.

4. **Wash-trade exclusion.** Solidus flagged ~15% of some markets as
   wash trading consistent with POLY airdrop farming. Our classifier
   does not exclude these patterns. Filtering paired YES+NO same-owner
   positions in the same condition_id within a short window would
   reduce Systematic-mixed and Retail cohort sizes.

5. **Builder Program flow attribution.** Some bot volume routes through
   the Polymarket Builder Program (231 registered apps as of late
   2025). Joining trades against the Builder registry would let us
   distinguish "direct API bots" from "Telegram bot / copy-trader
   wrapper" volume. Source: gateresearch Builders dashboard.

6. **Polymarket's official tag taxonomy.** Our "Other" bucket is still
   35% of platform volume even after expanded pattern matching, mostly
   null-tagged markets. Direct access to Polymarket's internal
   category taxonomy would resolve this.

---

## 6. Citation rules of thumb

- **Paradigm and Solidus are non-neutral sources.** Paradigm is a
  Kalshi investor; Solidus sells compliance software and benefits from
  reporting on Polymarket integrity issues. Their on-chain methodology
  is verifiable but their framing is not neutral. Cite the data, not
  the conclusions.
- **Polymarket's own dashboards have changed methodology post-Paradigm.**
  Pre-December 2025 volume numbers from Polymarket marketing or
  third-party dashboards are likely double-counted. Use on-chain
  reconstruction (our queries) or post-Dec 2025 reporting only.
- **Dune queries are mutable.** The queries we forked or referenced can
  be edited by their authors. Pin a specific execution_id (visible in
  the Dune URL) if you need to cite a stable snapshot.
- **Twitter / X threads decay fast.** Influencer claims like "3–4
  serious LPs run Polymarket" (defiance_cr) should be treated as
  hypothesis, not data. The Tier-1 oligopoly is real but the actual
  count is more like top-10 owners controlling ~30% of rewards.
