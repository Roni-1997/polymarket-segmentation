-- Cohort distribution over a single quarter (90-day window), 7-cohort framework.
-- Set w_start/w_end to the quarter you want. We run two copies — Q4 2025
-- and Q1 2026 — to see the time trend.
--
-- Dropped the category dimension to fit Dune's free-tier 2-minute SQL
-- timeout on 90-day windows. For category breakdown per quarter, chunk
-- further (45d or 30d) and combine.
--
-- Output volume is touched volume: maker-side + taker-side. Divide
-- by 2 only when comparing to single-counted venue notional.
--
-- Cost: ~12 credits.

WITH params AS (
  SELECT
    -- Q1 2026: 2026-01-01 to 2026-04-01
    -- Q4 2025: 2025-10-01 to 2026-01-01
    TIMESTAMP '2026-01-01 00:00:00 UTC' AS w_start,
    TIMESTAMP '2026-04-01 00:00:00 UTC' AS w_end
),
excluded_contracts AS (
  SELECT from_hex('e111180000d2663c0091e4f400237545b87b996b') AS addr
  UNION ALL SELECT from_hex('e2222d279d744050d28e00520010520000310f59')
  UNION ALL SELECT from_hex('4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e')
  UNION ALL SELECT from_hex('c5d563a36ae78145c45a50134d48a1215220f80a')
),
trades AS (
  SELECT t.block_time, t.taker, t.maker, t.amount
  FROM polymarket_polygon.market_trades t CROSS JOIN params p
  WHERE t.block_time >= p.w_start AND t.block_time < p.w_end
    AND t.maker IS NOT NULL AND t.taker IS NOT NULL AND t.amount > 0
    AND t.maker NOT IN (SELECT addr FROM excluded_contracts)
    AND t.taker NOT IN (SELECT addr FROM excluded_contracts)
),
wallet_sides_raw AS (
  SELECT COALESCE(u.owner, t.taker) AS wallet, 'taker' AS side, t.amount AS notional, t.block_time
  FROM trades t LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = t.taker
  UNION ALL
  SELECT COALESCE(u.owner, t.maker) AS wallet, 'maker' AS side, t.amount AS notional, t.block_time
  FROM trades t LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = t.maker
),
wallet_sides AS (
  SELECT * FROM wallet_sides_raw WHERE wallet NOT IN (SELECT addr FROM excluded_contracts)
),
wallet_features AS (
  SELECT wallet, COUNT(*) AS n_fills,
    COUNT(DISTINCT date_trunc('day', block_time)) AS n_active_days,
    SUM(notional) AS total_vol,
    SUM(CASE WHEN side='maker' THEN notional ELSE 0 END) AS maker_vol
  FROM wallet_sides GROUP BY 1
  HAVING COUNT(*) <= 5000000
),
cohorts AS (
  SELECT wallet, total_vol, maker_vol,
    CASE
      WHEN n_fills * 1.0 / GREATEST(n_active_days, 1) < 10 THEN 'Retail'
      WHEN n_fills * 1.0 / GREATEST(n_active_days, 1) >= 100 THEN
        CASE
          WHEN maker_vol / NULLIF(total_vol, 0) >= 0.70 THEN 'Pro-MM'
          WHEN maker_vol / NULLIF(total_vol, 0) >= 0.30 THEN 'Hybrid-bot'
          ELSE 'Fast-taker'
        END
      ELSE
        CASE
          WHEN maker_vol / NULLIF(total_vol, 0) >= 0.70 THEN 'Mid-MM'
          WHEN maker_vol / NULLIF(total_vol, 0) >= 0.30 THEN 'Systematic-mixed'
          ELSE 'Systematic-taker'
        END
    END AS cohort
  FROM wallet_features
)
SELECT
  cohort,
  COUNT(*) AS n_wallets,
  ROUND(SUM(total_vol)/1e6, 1) AS total_touched_vol_musd,
  ROUND(SUM(total_vol)/2e6, 1) AS equivalent_single_counted_musd,
  ROUND(SUM(maker_vol)/1e6, 1) AS maker_side_vol_musd,
  ROUND(SUM(total_vol - maker_vol)/1e6, 1) AS taker_side_vol_musd,
  ROUND(SUM(total_vol) / SUM(SUM(total_vol)) OVER () * 100, 1) AS pct_of_touched_volume
FROM cohorts
GROUP BY 1
ORDER BY total_touched_vol_musd DESC;
