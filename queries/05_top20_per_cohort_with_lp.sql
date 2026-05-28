-- Top 20 wallets per cohort (30d), 7-cohort framework, with overlay tags.
-- Overlay tags ship in this query:
--   lp_rewards_observed    — any LP reward history (any $)
--   lp_rewards_confirmed_1k — material LP reward (>= $1k all-time)
--   complete_set_arber     — n_split + n_merge events >= 5 in window
--   large_ticket_whale     — high vol per fill ($/fill >= $500 AND total_vol >= $100k)
--   confidence             — High / Medium / Low based on threshold-boundary proximity
--
-- Cost: ~50 credits.

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
  SELECT * FROM wallet_sides_raw WHERE wallet NOT IN (SELECT addr FROM excluded_contracts)
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
),
-- LP rewards (deduped merkle + direct transfers)
merkle_rewards AS (
  SELECT evt_tx_hash, tokenReceiver AS recipient, amount/1e6 AS amt
  FROM polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed
),
direct_rewards AS (
  SELECT tr.evt_tx_hash, tr."to" AS recipient, tr.value/1e6 AS amt
  FROM erc20_polygon.evt_Transfer tr
  WHERE tr."from" = from_hex('c288480574783bd7615170660d71753378159c47')
    AND tr.contract_address = from_hex('2791bca1f2de4661ed88a30c99a7a9449aa84174')
    AND NOT EXISTS (SELECT 1 FROM merkle_rewards mr WHERE mr.evt_tx_hash = tr.evt_tx_hash)
),
lp_rewards_raw AS (
  SELECT recipient, amt FROM merkle_rewards UNION ALL SELECT recipient, amt FROM direct_rewards
),
mm_confirmed AS (
  SELECT COALESCE(u.owner, r.recipient) AS wallet, SUM(r.amt) AS rewards_usd
  FROM lp_rewards_raw r
  LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = r.recipient
  GROUP BY 1
),
-- Complete-set arber signal: count splits + merges per stakeholder (owner-mapped) in window
split_merge AS (
  SELECT COALESCE(u.owner, addr.stakeholder) AS wallet, COUNT(*) AS n_split_merge
  FROM (
    SELECT stakeholder, evt_block_time FROM polymarket_polygon.ctf_evt_positionsplit
    UNION ALL
    SELECT stakeholder, evt_block_time FROM polymarket_polygon.ctf_evt_positionsmerge
  ) addr
  CROSS JOIN params p
  LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = addr.stakeholder
  WHERE addr.evt_block_time >= p.w_start AND addr.evt_block_time < p.w_end
  GROUP BY 1
),
ranked AS (
  SELECT c.*, ROW_NUMBER() OVER (PARTITION BY c.cohort ORDER BY c.total_vol DESC) AS rnk
  FROM cohorts c
  WHERE c.total_vol >= 10000
)
SELECT
  r.cohort,
  r.rnk AS rank,
  CONCAT('0x', LOWER(to_hex(r.wallet))) AS wallet,
  ROUND(r.total_vol/1e6, 2) AS touched_vol_musd,
  ROUND(r.maker_share, 3) AS maker_share,
  r.n_fills,
  r.n_unique_markets,
  CAST(ROUND(r.fills_per_day, 0) AS INTEGER) AS fills_per_day,
  CAST(ROUND(COALESCE(m.rewards_usd, 0), 0) AS BIGINT) AS lp_rewards_usd,
  COALESCE(m.rewards_usd, 0) > 0 AS lp_rewards_observed,
  COALESCE(m.rewards_usd, 0) >= 1000 AS lp_rewards_confirmed_1k,
  COALESCE(sm.n_split_merge, 0) >= 5 AS complete_set_arber,
  r.total_vol >= 100000 AND (r.total_vol / NULLIF(r.n_fills, 0)) >= 500 AS large_ticket_whale,
  CASE
    -- High confidence: LP-confirmed (Pro-MM/Mid-MM) or strong arb evidence
    WHEN COALESCE(m.rewards_usd, 0) >= 1000
      AND r.cohort IN ('Pro-MM', 'Mid-MM') THEN 'High'
    WHEN COALESCE(sm.n_split_merge, 0) >= 5
      AND r.cohort IN ('Hybrid-bot', 'Systematic-mixed') THEN 'High'
    -- Low confidence: wallet sits on a threshold boundary
    WHEN r.maker_share BETWEEN 0.65 AND 0.75 THEN 'Low'
    WHEN r.maker_share BETWEEN 0.25 AND 0.35 THEN 'Low'
    WHEN r.fills_per_day BETWEEN 8 AND 12 THEN 'Low'
    WHEN r.fills_per_day BETWEEN 90 AND 110 THEN 'Low'
    -- Default: medium
    ELSE 'Medium'
  END AS confidence
FROM ranked r
LEFT JOIN mm_confirmed m ON m.wallet = r.wallet
LEFT JOIN split_merge sm ON sm.wallet = r.wallet
WHERE r.rnk <= 20
ORDER BY r.cohort, r.rnk;
