# Findings — Polymarket participant segmentation

Status: audit-adjusted methodology, exact numbers require rerun.

The original exported CSVs showed a strongly professionalized participant
mix, but two audit issues made the exact dollar-volume and cohort-share
claims too strong:

1. The cohort queries counted **touched volume**: every fill appears once
   on the maker side and once on the taker side. This is correct for
   participant-share analysis, but it is 2x single-counted venue notional.
2. Known router/system contracts were excluded as raw maker/taker
   addresses, but not after `users_address_lookup` mapped proxy wallets to
   owners. At least one excluded system address appeared in the top-wallet
   output through owner mapping.

The SQL in `queries/` now fixes both problems. Rerun the queries before
citing exact cohort shares, category shares, or dollar volumes.

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

## Reproducible outputs to cite after rerun

After rerunning:

1. Use `04_cohort_x_category_30d.sql` for the trailing-30d cohort x
   category matrix.
2. Use `06_cohort_per_quarter.sql` for Q4 2025 and Q1 2026 trend
   comparisons.
3. Use `05_top20_per_cohort_with_lp.sql` for wallet-level validation.
   Prefer `lp_rewards_confirmed_1k = true` over `lp_rewards_observed =
   true`.
4. Use `08_lp_rewards_concentration.sql` for LP-reward concentration
   claims.

Do not cite the checked-in CSVs as final; they are retained only as a
legacy snapshot of the pre-audit run.

---

## Verdict implications that likely survive rerun

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
