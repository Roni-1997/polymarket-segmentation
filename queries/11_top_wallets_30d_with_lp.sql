-- Venue-wide top wallets (30d) with LP-rewards flags.
--
-- Use this for cross-venue checks that need the true top-N Polymarket
-- wallets by touched volume. Do not use 05_top20_per_cohort_with_lp.sql
-- for "top 100 venue-wide" claims; query 05 is intentionally stratified
-- by cohort for validation.
--
-- Output volume is touched volume: maker-side + taker-side volume. Divide
-- by 2 only when comparing aggregate sums to single-counted venue notional.
--
-- Cost: similar to query 05.

WITH params AS (
  SELECT CURRENT_TIMESTAMP - INTERVAL '30' DAY AS w_start, CURRENT_TIMESTAMP AS w_end
),
excluded_contracts AS (
  SELECT from_hex('e111180000d2663c0091e4f400237545b87b996b') AS addr
  UNION ALL SELECT from_hex('e2222d279d744050d28e00520010520000310f59')
  UNION ALL SELECT from_hex('4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e')
  UNION ALL SELECT from_hex('c5d563a36ae78145c45a50134d48a1215220f80a')
),
trades AS (
  SELECT t.block_time, t.taker, t.maker, t.amount, t.condition_id
  FROM polymarket_polygon.market_trades t CROSS JOIN params p
  WHERE t.block_time >= p.w_start AND t.block_time < p.w_end
    AND t.maker IS NOT NULL AND t.taker IS NOT NULL AND t.amount > 0
    AND t.maker NOT IN (SELECT addr FROM excluded_contracts)
    AND t.taker NOT IN (SELECT addr FROM excluded_contracts)
),
wallet_sides_raw AS (
  SELECT COALESCE(u.owner, t.taker) AS wallet, 'taker' AS side, t.amount AS notional, t.block_time, t.condition_id
  FROM trades t LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = t.taker
  UNION ALL
  SELECT COALESCE(u.owner, t.maker) AS wallet, 'maker' AS side, t.amount AS notional, t.block_time, t.condition_id
  FROM trades t LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = t.maker
),
wallet_sides AS (
  SELECT *
  FROM wallet_sides_raw
  WHERE wallet NOT IN (SELECT addr FROM excluded_contracts)
),
wallet_features AS (
  SELECT wallet,
    COUNT(*) AS n_fills,
    COUNT(DISTINCT date_trunc('day', block_time)) AS n_active_days,
    COUNT(DISTINCT condition_id) AS n_unique_markets,
    SUM(notional) AS total_vol,
    SUM(CASE WHEN side='maker' THEN notional ELSE 0 END) AS maker_vol
  FROM wallet_sides
  GROUP BY 1
  HAVING COUNT(*) <= 5000000
),
cohorts AS (
  SELECT wallet, total_vol, maker_vol, n_fills, n_active_days, n_unique_markets,
    maker_vol / NULLIF(total_vol, 0) AS maker_share,
    n_fills * 1.0 / GREATEST(n_active_days, 1) AS fills_per_day,
    CASE
      WHEN maker_vol / NULLIF(total_vol, 0) >= 0.70 THEN 'highMkr'
      WHEN maker_vol / NULLIF(total_vol, 0) >= 0.30 THEN 'midMkr'
      ELSE 'lowMkr'
    END AS maker_band,
    CASE
      WHEN n_fills * 1.0 / GREATEST(n_active_days, 1) >= 100 THEN 'fast'
      WHEN n_fills * 1.0 / GREATEST(n_active_days, 1) >= 1   THEN 'med'
      ELSE 'slow'
    END AS cadence_band
  FROM wallet_features
),
merkle_rewards AS (
  SELECT evt_tx_hash, tokenReceiver AS recipient, amount/1e6 AS amt
  FROM polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed
),
direct_rewards AS (
  SELECT tr.evt_tx_hash, tr."to" AS recipient, tr.value/1e6 AS amt
  FROM erc20_polygon.evt_Transfer tr
  WHERE tr."from" = from_hex('c288480574783bd7615170660d71753378159c47')
    AND tr.contract_address = from_hex('2791bca1f2de4661ed88a30c99a7a9449aa84174')
    AND NOT EXISTS (
      SELECT 1
      FROM merkle_rewards mr
      WHERE mr.evt_tx_hash = tr.evt_tx_hash
    )
),
lp_rewards_raw AS (
  SELECT recipient, amt FROM merkle_rewards
  UNION ALL
  SELECT recipient, amt FROM direct_rewards
),
mm_confirmed AS (
  SELECT COALESCE(u.owner, r.recipient) AS wallet, SUM(r.amt) AS rewards_usd
  FROM lp_rewards_raw r
  LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = r.recipient
  GROUP BY 1
),
ranked AS (
  SELECT
    c.*,
    ROW_NUMBER() OVER (ORDER BY c.total_vol DESC) AS rank_by_touched_volume
  FROM cohorts c
  WHERE c.total_vol >= 10000
)
SELECT
  r.rank_by_touched_volume AS rank,
  CONCAT('0x', LOWER(to_hex(r.wallet))) AS wallet,
  r.maker_band || '_' || r.cadence_band AS cohort,
  ROUND(r.total_vol/1e6, 2) AS touched_vol_musd,
  ROUND(r.total_vol/2e6, 2) AS equivalent_single_counted_musd,
  ROUND(r.maker_share, 3) AS maker_share,
  r.n_fills,
  r.n_unique_markets,
  CAST(ROUND(r.fills_per_day, 0) AS INTEGER) AS fills_per_day,
  CAST(ROUND(COALESCE(m.rewards_usd, 0), 0) AS BIGINT) AS lp_rewards_usd,
  COALESCE(m.rewards_usd, 0) > 0 AS lp_rewards_observed,
  COALESCE(m.rewards_usd, 0) >= 1000 AS lp_rewards_confirmed_1k
FROM ranked r
LEFT JOIN mm_confirmed m ON m.wallet = r.wallet
WHERE r.rank_by_touched_volume <= 100
ORDER BY r.rank_by_touched_volume;
