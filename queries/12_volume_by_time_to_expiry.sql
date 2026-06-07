-- Volume attribution by time-to-expiry (trailing 30 days).
--
-- Output: one row per expiry bucket showing how much single-counted
-- notional traded when the market was 0-5m / 5-15m / 15m-1h / 1-6h /
-- 6-12h / 12-24h / 1-3d / 3-7d / 7-30d / 30d+ from resolution/end time.
--
-- Use case: measure whether Polymarket volume is event-day / near-expiry
-- flow versus longer-horizon thesis flow.
--
-- Notes:
--   * Single-counted notional is SUM(market_trades.amount), not touched
--     maker+taker volume.
--   * Uses resolved_on_timestamp first, then market_end_time. Using only
--     market_end_time materially overstates stale/past-end metadata for
--     sports and fast markets.
--   * Keeps unknown/past-end buckets visible because metadata can still be
--     stale or imperfect for some markets.
--   * For month-by-month attribution, pin w_start/w_end to the desired
--     calendar month and rerun. The compact 30d version stays under Dune's
--     2-minute timeout; the all-category 12-month daily/monthly version did
--     not.
--
-- Cost: ~20-40 credits.

WITH params AS (
  SELECT CURRENT_TIMESTAMP - INTERVAL '30' DAY AS w_start, CURRENT_TIMESTAMP AS w_end
),
excluded_contracts AS (
  SELECT from_hex('e111180000d2663c0091e4f400237545b87b996b') AS addr
  UNION ALL SELECT from_hex('e2222d279d744050d28e00520010520000310f59')
  UNION ALL SELECT from_hex('4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e')
  UNION ALL SELECT from_hex('c5d563a36ae78145c45a50134d48a1215220f80a')
),
base_trades AS (
  SELECT t.block_time, t.amount, t.condition_id
  FROM polymarket_polygon.market_trades t
  CROSS JOIN params p
  WHERE t.block_time >= p.w_start
    AND t.block_time < p.w_end
    AND t.maker IS NOT NULL
    AND t.taker IS NOT NULL
    AND t.amount > 0
    AND t.maker NOT IN (SELECT addr FROM excluded_contracts)
    AND t.taker NOT IN (SELECT addr FROM excluded_contracts)
),
trade_conditions AS (
  SELECT DISTINCT '0x' || LOWER(to_hex(condition_id)) AS condition_id
  FROM base_trades
),
market_meta AS (
  SELECT
    md.condition_id,
    MAX(
      COALESCE(
        CAST(md.resolved_on_timestamp AS timestamp),
        COALESCE(
          try_cast(md.market_end_time AS timestamp),
          CAST(try(from_iso8601_timestamp(md.market_end_time)) AS timestamp)
        )
      )
    ) AS end_ts
  FROM polymarket_polygon.market_details md
  JOIN trade_conditions tc ON tc.condition_id = md.condition_id
  GROUP BY 1
),
bucketed AS (
  SELECT
    CASE
      WHEN mm.end_ts IS NULL THEN 99
      WHEN date_diff('second', bt.block_time, mm.end_ts) < 0 THEN 98
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 5 * 60 THEN 1
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 15 * 60 THEN 2
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 60 * 60 THEN 3
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 6 * 60 * 60 THEN 4
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 12 * 60 * 60 THEN 5
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 24 * 60 * 60 THEN 6
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 3 * 24 * 60 * 60 THEN 7
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 7 * 24 * 60 * 60 THEN 8
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 30 * 24 * 60 * 60 THEN 9
      ELSE 10
    END AS expiry_bucket_order,
    CASE
      WHEN mm.end_ts IS NULL THEN 'unknown_expiry'
      WHEN date_diff('second', bt.block_time, mm.end_ts) < 0 THEN 'past_end_metadata'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 5 * 60 THEN '0-5m'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 15 * 60 THEN '5-15m'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 60 * 60 THEN '15m-1h'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 6 * 60 * 60 THEN '1-6h'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 12 * 60 * 60 THEN '6-12h'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 24 * 60 * 60 THEN '12-24h'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 3 * 24 * 60 * 60 THEN '1-3d'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 7 * 24 * 60 * 60 THEN '3-7d'
      WHEN date_diff('second', bt.block_time, mm.end_ts) <= 30 * 24 * 60 * 60 THEN '7-30d'
      ELSE '30d+'
    END AS expiry_bucket,
    bt.amount
  FROM base_trades bt
  LEFT JOIN market_meta mm ON mm.condition_id = '0x' || LOWER(to_hex(bt.condition_id))
),
agg AS (
  SELECT
    expiry_bucket_order,
    expiry_bucket,
    COUNT(*) AS fills,
    SUM(amount) AS notional
  FROM bucketed
  GROUP BY 1, 2
),
tot AS (
  SELECT SUM(notional) AS total_notional FROM agg
)
SELECT
  expiry_bucket_order,
  expiry_bucket,
  fills,
  ROUND(notional / 1e6, 3) AS single_counted_musd,
  ROUND(100 * notional / NULLIF(total_notional, 0), 2) AS share_pct,
  ROUND(
    100 * SUM(notional) OVER (ORDER BY expiry_bucket_order) / NULLIF(total_notional, 0),
    2
  ) AS cumulative_share_pct
FROM agg CROSS JOIN tot
ORDER BY expiry_bucket_order;
