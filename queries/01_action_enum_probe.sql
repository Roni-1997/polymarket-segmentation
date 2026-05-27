-- Pre-flight: what values does market_trades.action contain?
-- (Schema docs say "CLOB or AMM" but overview claims 3 match types incl
-- MINT/MERGE — turns out the real value is only "CLOB trade".)
-- Cost: ~0.4 credits on Dune free tier.

SELECT action, COUNT(*) AS n
FROM polymarket_polygon.market_trades
WHERE block_time >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY 1
ORDER BY n DESC;
