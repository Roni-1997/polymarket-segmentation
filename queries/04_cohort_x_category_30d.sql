-- Cohort × category cross-tab (trailing 30 days), CLEAN version.
-- All three fixes applied:
--   1. Excludes routing contracts (NegRisk adapter + 3 others).
--   2. Expanded category mapping to catch Iran/Ukraine/Awards/MrBeast/etc.
--   3. market_details pre-aggregated to one row per condition_id
--      (otherwise binary YES/NO + NegRisk multi-outcome inflate JOIN
--      by 2-5x).
--
-- Output: one row per (cohort), columns by category, ordered by total
-- volume. Re-aggregate categories with column sums for a category-only
-- view; collapse cohorts to MM/HFT/Retail to compare to original memo.
--
-- Cost: ~30 credits on Dune free tier. Runs in ~60-90 sec.

WITH params AS (
  SELECT CURRENT_TIMESTAMP - INTERVAL '30' DAY AS w_start, CURRENT_TIMESTAMP AS w_end
),
excluded_contracts AS (
  SELECT from_hex('e111180000d2663c0091e4f400237545b87b996b') AS addr
  UNION ALL SELECT from_hex('e2222d279d744050d28e00520010520000310f59')
  UNION ALL SELECT from_hex('4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e')
  UNION ALL SELECT from_hex('c5d563a36ae78145c45a50134d48a1215220f80a')
),
market_cat AS (
  SELECT condition_id, MAX(tags) AS tags
  FROM polymarket_polygon.market_details
  WHERE tags IS NOT NULL AND tags <> ''
  GROUP BY 1
),
trades_cat AS (
  SELECT t.block_time, t.taker, t.maker, t.amount, t.condition_id,
    CASE
      WHEN mc.tags LIKE 'Crypto%' THEN 'crypto'
      WHEN mc.tags LIKE 'Sports%' THEN 'sports'
      WHEN mc.tags LIKE 'Politic%' OR mc.tags LIKE 'Trump%' OR mc.tags LIKE 'Elections%' THEN 'politics'
      WHEN mc.tags LIKE 'Pop Culture%' OR mc.tags LIKE 'Culture%' OR mc.tags LIKE 'Entertain%'
        OR mc.tags LIKE 'Awards%' OR mc.tags LIKE 'MrBeast%' OR mc.tags LIKE 'YouTube%'
        OR mc.tags LIKE 'Movies%' OR mc.tags LIKE 'Music%' OR mc.tags LIKE 'box office%'
        OR mc.tags LIKE 'Celebrities%' OR mc.tags LIKE 'SpaceX%' OR mc.tags LIKE 'Breaking News%'
        OR mc.tags LIKE 'Prediction Markets%' OR mc.tags LIKE 'football%' THEN 'culture'
      WHEN mc.tags LIKE 'Business%' OR mc.tags LIKE 'Econ%' OR mc.tags LIKE 'Fed%'
        OR mc.tags LIKE 'Trade Wars%' OR mc.tags LIKE 'Macro%' OR mc.tags LIKE 'Finance%'
        OR mc.tags LIKE 'Stocks%' OR mc.tags LIKE 'Markets%'
        OR mc.tags LIKE 'Oil%' OR mc.tags LIKE 'Inflation%' OR mc.tags LIKE 'interest rates%' THEN 'finance'
      WHEN mc.tags LIKE 'Geopolit%' OR mc.tags LIKE 'World%' OR mc.tags LIKE 'Middle East%' OR mc.tags LIKE 'War%'
        OR mc.tags LIKE 'Iran%' OR mc.tags LIKE 'Ukraine%' OR mc.tags LIKE 'Russia%' OR mc.tags LIKE 'China%'
        OR mc.tags LIKE 'Venezuela%' OR mc.tags LIKE 'Syria%' OR mc.tags LIKE 'Gaza%'
        OR mc.tags LIKE 'world affairs%' OR mc.tags LIKE 'strike%'
        OR mc.tags LIKE 'Brazil%' OR mc.tags LIKE 'UK%' THEN 'geopolitics'
      WHEN mc.tags LIKE 'Weather%' THEN 'weather'
      WHEN mc.tags LIKE 'AI%' OR mc.tags LIKE 'Science%' OR mc.tags LIKE 'Tech%' THEN 'tech'
      ELSE 'other'
    END AS category
  FROM polymarket_polygon.market_trades t
  CROSS JOIN params p
  LEFT JOIN market_cat mc ON mc.condition_id = '0x' || LOWER(to_hex(t.condition_id))
  WHERE t.block_time >= p.w_start AND t.block_time < p.w_end
    AND t.maker IS NOT NULL AND t.taker IS NOT NULL AND t.amount > 0
    AND t.maker NOT IN (SELECT addr FROM excluded_contracts)
    AND t.taker NOT IN (SELECT addr FROM excluded_contracts)
),
wallet_sides AS (
  SELECT COALESCE(u.owner, t.taker) AS wallet, 'taker' AS side, t.amount AS notional, t.block_time, t.condition_id, t.category
  FROM trades_cat t LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = t.taker
  UNION ALL
  SELECT COALESCE(u.owner, t.maker) AS wallet, 'maker' AS side, t.amount AS notional, t.block_time, t.condition_id, t.category
  FROM trades_cat t LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = t.maker
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
  HAVING COUNT(DISTINCT condition_id) <= 50000  -- safety net for unidentified routers
),
cohorts AS (
  SELECT wallet,
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
wallet_cat_vol AS (
  SELECT ws.wallet, ws.category, SUM(ws.notional) AS vol
  FROM wallet_sides ws
  JOIN wallet_features wf ON wf.wallet = ws.wallet
  GROUP BY 1, 2
),
coh_cat AS (
  SELECT c.maker_band || '_' || c.cadence_band AS cohort, wc.category, SUM(wc.vol) AS vol
  FROM cohorts c
  JOIN wallet_cat_vol wc ON wc.wallet = c.wallet
  GROUP BY 1, 2
)
SELECT cohort,
  ROUND(SUM(CASE WHEN category='sports'      THEN vol ELSE 0 END)/1e6, 1) AS sports_musd,
  ROUND(SUM(CASE WHEN category='politics'    THEN vol ELSE 0 END)/1e6, 1) AS politics_musd,
  ROUND(SUM(CASE WHEN category='crypto'      THEN vol ELSE 0 END)/1e6, 1) AS crypto_musd,
  ROUND(SUM(CASE WHEN category='finance'     THEN vol ELSE 0 END)/1e6, 1) AS finance_musd,
  ROUND(SUM(CASE WHEN category='culture'     THEN vol ELSE 0 END)/1e6, 1) AS culture_musd,
  ROUND(SUM(CASE WHEN category='geopolitics' THEN vol ELSE 0 END)/1e6, 1) AS geopol_musd,
  ROUND(SUM(CASE WHEN category='weather'     THEN vol ELSE 0 END)/1e6, 1) AS weather_musd,
  ROUND(SUM(CASE WHEN category='tech'        THEN vol ELSE 0 END)/1e6, 1) AS tech_musd,
  ROUND(SUM(CASE WHEN category='other'       THEN vol ELSE 0 END)/1e6, 1) AS other_musd,
  ROUND(SUM(vol)/1e6, 1) AS total_musd
FROM coh_cat
GROUP BY 1
ORDER BY total_musd DESC;
