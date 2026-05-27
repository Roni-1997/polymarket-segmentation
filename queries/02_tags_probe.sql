-- Discover what values market_details.tags contains (comma-separated;
-- first element is the high-level category).
-- Cost: ~0.05 credits.

SELECT tags, COUNT(DISTINCT condition_id) AS n_markets
FROM polymarket_polygon.market_details
WHERE tags IS NOT NULL AND tags <> ''
GROUP BY 1
ORDER BY n_markets DESC
LIMIT 30;
