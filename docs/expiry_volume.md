# Prediction markets are event-day markets

This note measures Polymarket volume by time remaining until market
resolution/end time. The goal is to distinguish longer-horizon thesis
trading from event-day trading.

## Result

Trailing 30 days, Dune execution `01KTHRWXFQ0YWV6A7WRJQFZK09`, run on
2026-06-07:

| Time to resolution/end | Single-counted volume | Share | Cumulative share |
|---|---:|---:|---:|
| 0-5m | $388.1M | 12.0% | 12.0% |
| 5-15m | $92.3M | 2.9% | 14.9% |
| 15m-1h | $100.4M | 3.1% | 18.0% |
| 1-6h | $1.136B | 35.2% | 53.2% |
| 6-12h | $342.5M | 10.6% | 63.8% |
| 12-24h | $201.8M | 6.3% | 70.1% |
| 1-3d | $306.1M | 9.5% | 79.5% |
| 3-7d | $123.6M | 3.8% | 83.4% |
| 7-30d | $181.4M | 5.6% | 89.0% |
| 30d+ | $173.3M | 5.4% | 94.4% |
| Past-end metadata | $178.9M | 5.5% | 99.9% |
| Unknown expiry | $3.2M | 0.1% | 100.0% |

Headline:

> Roughly 70% of trailing-30d Polymarket notional traded inside the
> final 24 hours before resolution/end time; roughly 53% traded inside
> the final 6 hours.

## Interpretation

Polymarket is often described as a forecasting venue, but its volume
profile looks more like an event-driven trading venue. Most notional is
not spread evenly across a market's life. It clusters near resolution,
when information arrival is dense, mark-to-resolution risk is lower,
market makers can price tighter, and traders have a concrete catalyst.

This matters for market design:

- **Market count is the wrong launch metric.** A large inactive catalog
  does not create volume. Markets need a near-term catalyst, clear
  resolution path, and enough pre-resolution volatility.
- **Liquidity should be scheduled, not static.** The highest-value
  quoting window is the final day, especially the final 6 hours. A
  venue should not subsidize every market equally from creation to
  expiry.
- **Long-dated markets need catalysts.** Outrights can trade well, but
  their active periods are usually around news, lineup changes, polls,
  injuries, macro prints, or other information shocks.
- **Resolution metadata is part of market structure.** The query keeps
  stale/unknown buckets visible. A non-trivial residual still has
  imperfect metadata, even after using `resolved_on_timestamp` before
  `market_end_time`.

## Method

Source query: [`queries/12_volume_by_time_to_expiry.sql`](../queries/12_volume_by_time_to_expiry.sql)

Source result:
[`results/volume_by_time_to_expiry_30d.csv`](../results/volume_by_time_to_expiry_30d.csv)

For each `polymarket_polygon.market_trades` fill in the trailing 30-day
window:

1. Exclude known system/router contracts.
2. Join `market_details` on `condition_id`.
3. Use `resolved_on_timestamp` as the primary end timestamp, falling
   back to parsed `market_end_time`.
4. Bucket `date_diff('second', block_time, end_ts)`.
5. Aggregate single-counted notional, not maker+taker touched volume.

The query intentionally reports `past_end_metadata` and
`unknown_expiry` instead of dropping those rows. Dropping them would make
the clean buckets look stronger while hiding metadata quality issues.

## Caveats

- The result is a trailing 30-day snapshot, not a permanent venue law.
  Sports calendars, elections, geopolitical shocks, and crypto fast
  markets can shift the exact bucket mix.
- `resolved_on_timestamp` is a better proxy than `market_end_time`, but
  it is not perfect. Some rows still land in `past_end_metadata`.
- This analysis measures volume timing, not profitability, accuracy, or
  user identity.
- The result is single-counted venue notional. It should not be compared
  directly to touched maker+taker cohort volume.

## Publishable takeaway

Prediction-market liquidity is not mostly about passively listing every
possible market. It is about concentrating market creation, liquidity,
and distribution around the short windows when users and market makers
actually have reason to trade.
