-- Find what's in the "other" bucket — markets whose tags didn't match
-- any of the main category patterns. Reveals leakage (Iran/Ukraine
-- should map to geopolitics, Awards/MrBeast to culture, etc.) and the
-- size of the null-tagged residual.
-- Cost: ~3 credits.

WITH params AS (
  SELECT CURRENT_TIMESTAMP - INTERVAL '30' DAY AS w_start
),
market_cat AS (
  SELECT condition_id, MAX(tags) AS tags
  FROM polymarket_polygon.market_details
  GROUP BY 1
),
other_trades AS (
  SELECT t.amount, mc.tags
  FROM polymarket_polygon.market_trades t
  CROSS JOIN params p
  LEFT JOIN market_cat mc ON mc.condition_id = '0x' || LOWER(to_hex(t.condition_id))
  WHERE t.block_time >= p.w_start
    AND (mc.tags IS NULL
         OR NOT (mc.tags LIKE 'Crypto%' OR mc.tags LIKE 'Sports%' OR mc.tags LIKE 'Politic%'
                 OR mc.tags LIKE 'Pop Culture%' OR mc.tags LIKE 'Culture%' OR mc.tags LIKE 'Entertain%'
                 OR mc.tags LIKE 'Business%' OR mc.tags LIKE 'Econ%' OR mc.tags LIKE 'Fed%'
                 OR mc.tags LIKE 'Trade Wars%' OR mc.tags LIKE 'Macro%' OR mc.tags LIKE 'Finance%'
                 OR mc.tags LIKE 'Stocks%' OR mc.tags LIKE 'Markets%'
                 OR mc.tags LIKE 'Geopolit%' OR mc.tags LIKE 'World%' OR mc.tags LIKE 'Middle East%'
                 OR mc.tags LIKE 'War%'
                 OR mc.tags LIKE 'AI%' OR mc.tags LIKE 'Science%' OR mc.tags LIKE 'Tech%'))
)
SELECT COALESCE(SPLIT_PART(tags, ',', 1), '<<NULL_TAGS>>') AS primary_tag,
  ROUND(SUM(amount)/1e6, 2) AS vol_musd,
  COUNT(*) AS n_fills
FROM other_trades
GROUP BY 1
ORDER BY vol_musd DESC
LIMIT 30;
