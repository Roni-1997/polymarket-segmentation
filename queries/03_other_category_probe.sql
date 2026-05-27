-- Find what's in the "other" bucket — markets whose tags didn't match
-- any of the main category patterns. Reveals residual tag leakage and the
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
         OR NOT (mc.tags LIKE 'Crypto%' OR mc.tags LIKE 'Sports%' OR mc.tags LIKE 'Soccer%'
                 OR mc.tags LIKE 'Football%' OR mc.tags LIKE 'football%' OR mc.tags LIKE 'Politic%'
                 OR mc.tags LIKE 'Pop Culture%' OR mc.tags LIKE 'Culture%' OR mc.tags LIKE 'Entertain%'
                 OR mc.tags LIKE 'Awards%' OR mc.tags LIKE 'MrBeast%' OR mc.tags LIKE 'YouTube%'
                 OR mc.tags LIKE 'Movies%' OR mc.tags LIKE 'Music%' OR mc.tags LIKE 'box office%'
                 OR mc.tags LIKE 'Celebrities%' OR mc.tags LIKE 'SpaceX%' OR mc.tags LIKE 'Breaking News%'
                 OR mc.tags LIKE 'Prediction Markets%'
                 OR mc.tags LIKE 'Business%' OR mc.tags LIKE 'Econ%' OR mc.tags LIKE 'Fed%'
                 OR mc.tags LIKE 'Trade Wars%' OR mc.tags LIKE 'Macro%' OR mc.tags LIKE 'Finance%'
                 OR mc.tags LIKE 'Stocks%' OR mc.tags LIKE 'Markets%' OR mc.tags LIKE 'Oil%'
                 OR mc.tags LIKE 'Inflation%' OR mc.tags LIKE 'interest rates%'
                 OR mc.tags LIKE 'Geopolit%' OR mc.tags LIKE 'World%' OR mc.tags LIKE 'Middle East%'
                 OR mc.tags LIKE 'War%' OR mc.tags LIKE 'Iran%' OR mc.tags LIKE 'Ukraine%'
                 OR mc.tags LIKE 'Russia%' OR mc.tags LIKE 'China%' OR mc.tags LIKE 'Venezuela%'
                 OR mc.tags LIKE 'Syria%' OR mc.tags LIKE 'Gaza%' OR mc.tags LIKE 'world affairs%'
                 OR mc.tags LIKE 'strike%' OR mc.tags LIKE 'Brazil%' OR mc.tags LIKE 'UK%'
                 OR mc.tags LIKE 'Weather%'
                 OR mc.tags LIKE 'AI%' OR mc.tags LIKE 'Science%' OR mc.tags LIKE 'Tech%'))
)
SELECT COALESCE(SPLIT_PART(tags, ',', 1), '<<NULL_TAGS>>') AS primary_tag,
  ROUND(SUM(amount)/1e6, 2) AS vol_musd,
  COUNT(*) AS n_fills
FROM other_trades
GROUP BY 1
ORDER BY vol_musd DESC
LIMIT 30;
