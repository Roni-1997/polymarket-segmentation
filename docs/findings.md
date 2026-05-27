# Findings — Polymarket participant segmentation

Status: **audit-adjusted methodology AND rerun completed**.
Data window: trailing 30 days (April 27 – May 27, 2026).
Quarterly comparison: Q4 2025 and Q1 2026.

The original exported CSVs had two audit issues that have now been fixed
in the SQL and the queries re-executed against Dune:

1. The cohort queries counted **touched volume** (each fill once on the
   maker side + once on the taker side). Correct for participant-share
   analysis, but 2× single-counted venue notional. Output now carries
   both columns explicitly.
2. Known router/system contracts were filtered as raw maker/taker
   addresses, but not after `users_address_lookup` mapped proxy wallets
   to owners. Now filtered at both stages.
3. LP rewards UNIONed merkle claims with direct USDC transfers, which
   double-counted: merkle claims trigger a USDC transfer in the same tx.
   Direct transfers are now deduped against merkle claims by `evt_tx_hash`.

---

## Audited numbers (trailing 30 days, May 2026)

### Cohort distribution by single-counted notional ($M)

| Cohort | Touched $M | Single-counted $M | % of touched |
|---|---:|---:|---:|
| Pro-MM (highMkr_fast) | 1,950 | **975** | **31.4%** |
| HFT-taker (lowMkr_fast) | 1,269 | 635 | 20.5% |
| Hybrid-bot (midMkr_fast) | 1,079 | 539 | 17.4% |
| Active-retail (lowMkr_med) | 1,008 | 504 | 16.2% |
| Mid-MM (highMkr_med) | 527 | 263 | 8.5% |
| Active-mixed (midMkr_med) | 374 | 187 | 6.0% |
| **Total** | **6,206** | **3,103** | 100% |

Real volume: **~$103M/day single-counted notional** over the trailing
30 days. This matches Paradigm's December 2025 finding that Polymarket's
~$200M/day headline number is ~2× overstated via OrderFilled
double-counting.

Note: the pre-audit version of this doc stated $210M/day, which was
touched volume mislabeled as notional. The corrected number is half
that.

### Collapsed three-bucket view

| Bucket | % of touched |
|---|---:|
| **MMs** (Pro + Mid) | **39.9%** |
| **Bots** (HFT + Hybrid) | **37.9%** |
| **Retail** (Active-retail + Active-mixed) | **22.2%** |

### Cohort distribution by quarter (% of touched volume)

| Cohort | Q4 2025 | Q1 2026 | T30d |
|---|---:|---:|---:|
| Pro-MM | 23.2% | 29.1% | 31.4% |
| HFT-taker | 11.5% | 17.1% | 20.5% |
| Hybrid-bot | 22.8% | 22.0% | 17.4% |
| Mid-MM | 9.7% | 6.6% | 8.5% |
| Active-retail | 18.0% | 15.2% | 16.2% |
| Active-mixed | 14.7% | 10.0% | 6.0% |

Collapsed retail share: 33% → 25% → 22%. Direction holds; magnitudes
unchanged from pre-audit because the cohort-level fixes were tiny.

### Volume in dollars (single-counted)

| Period | $B / qtr (single-counted) | $M / day |
|---|---:|---:|
| Q4 2025 | 5.2 | 57 |
| Q1 2026 | 11.1 | 123 |
| T30d (May 2026) | 3.1 | **103** |

Q1 2026 was a 2× volume spike vs Q4 2025; T30d sits ~85% of the Q1
peak. Likely drivers: NCAA + crypto rally + post-inauguration markets.

---

## LP rewards — major correction

The pre-audit doc said "top 100 wallets capture 100% of rewards" — that
was an artifact of fetching only the top 50 from a paginated result.
After deduping merkle claims against direct USDC transfers and
aggregating to owner level, the actual picture is:

| Top N (owners) | $ rewards | % of all rewards |
|---|---:|---:|
| 3 | $4.24M | **20.1%** |
| 10 | $6.42M | **30.3%** |
| 20 | $8.12M | 38.4% |
| 50 | $10.60M | 50.1% |
| 100 | $12.57M | 59.4% |
| **All (111,217 owners)** | **$21.16M** | 100% |

**Pre-audit said top 10 = 51%; audited says 30.3%.** Pre-audit said
top 100 = 100%; audited says 59.4%, with a 40% long tail across
~111,000 reward-earning wallets.

The Tier-1 oligopoly is real — top 3 captured $4.24M (20%) — but
much more diluted by a long tail than the original analysis suggested.

Top 3 owners by all-time LP rewards (deduped):
- `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb` — $2.43M
- `0x9d84ce0306f8551e02efef1680475fc0f1dc1344` — $1.27M
- `0x96bde0dd1d5ba5cc8e1c74cdec14041564a1363a` — $545k

---

## What remains robust

The directional market-structure conclusion is still supported:

- Polymarket is not primarily a one-off retail venue. A large share of
  activity comes from maker-heavy wallets, high-cadence takers, and
  hybrid maker/taker strategies.
- Participant segmentation should be measured at the **owner** level, not
  proxy-wallet level.
- MMs can and do take liquidity. The right metric is therefore segment
  share of maker+taker touched volume, not maker-side volume alone.
- LP rewards are useful ground truth for MM participation, but only after
  deduping merkle claims vs direct transfers and ignoring dust rewards as
  weak identity evidence.
- Crypto/short-duration markets should be expected to skew more automated
  than politics or slower event markets.

---

## Counting convention

Use two separate denominators:

| Metric | Definition | Use |
|---|---|---|
| Single-counted notional | One row per fill from `market_trades.amount` | Venue volume, dollars/day, comparison to public volume numbers |
| Touched volume | Maker-side amount + taker-side amount | Participant share, because both counterparties participated |

If `04_cohort_x_category_30d.sql` reports `total_touched_musd = 6,000`,
the equivalent single-counted venue notional is `3,000` million. Cohort
shares from touched volume are still meaningful because all fills have two
sides; absolute dollar-volume claims must use the single-counted column.

---

## Where to find each result

Each cited number above maps to a specific CSV under `results/`:

1. Trailing-30d cohort × category — `results/cohort_x_category_30d_clean.csv`
   from `queries/04_cohort_x_category_30d.sql`.
2. Quarterly trend — `results/cohort_q1_2026.csv` and
   `results/cohort_q4_2025.csv` from `queries/06_cohort_per_quarter.sql`
   (run twice with different date windows).
3. Wallet-level validation — `results/top20_per_cohort_30d.csv` from
   `queries/05_top20_per_cohort_with_lp.sql`. Use
   `lp_rewards_confirmed_1k` as the strong signal, not
   `lp_rewards_observed`.
4. LP rewards concentration — `results/lp_rewards_concentration.csv`
   from `queries/08_lp_rewards_concentration.sql`.

---

## Verdict implications (rerun-confirmed)

1. **Design for professional flow early.** Crypto and financial outcome
   markets are naturally quoteable, hedgeable, and automation-friendly.
   Verdict should prioritize API quality, deterministic settlement, and
   maker tooling before broad retail discovery work.

2. **Internal liquidity still matters, but measure it correctly.**
   Baseline liquidity should be evaluated by quote uptime, spread, depth,
   markouts, and inventory bounds, not headline volume.

3. **Hybrid maker/taker bots are strategically important.** These actors
   bridge pure MM and pure taker flow: they quote when rewarded, take when
   inventory or cross-market pricing demands it, and are easier to
   onboard than a small set of top-tier institutional MMs.

4. **Retail is still useful even if not dominant.** Less informed flow is
   what lets market makers earn the spread. A venue with only professional
   flow becomes an adverse-selection contest.

5. **Avoid overfitting to politics.** Verdict's HIP-4 edge is strongest
   in objective, fast-resolving, hedgeable crypto/financial markets.
