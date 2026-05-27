-- LP rewards distribution — fork of dune.com/queries/5989757.
-- UNIONs the two reward sources Polymarket uses:
--   1. MerkleDistributor airdrop (canonical post-2024 mechanism)
--   2. Direct USDC transfers from the rewards distributor wallet
--      0xc288480574783BD7615170660d71753378159c47
--
-- Top 100 wallets capture 100% of rewards; top 10 capture 51%; top 3
-- capture 33.7%. This is the ground-truth MM-confirmed wallet list.
-- Aggregated to owner level via users_address_lookup.

WITH lp_rewards_raw AS (
  SELECT tokenReceiver AS recipient, amount/1e6 AS amt
  FROM polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed
  UNION ALL
  SELECT "to" AS recipient, value/1e6 AS amt
  FROM erc20_polygon.evt_Transfer
  WHERE "from" = from_hex('c288480574783BD7615170660d71753378159c47')
    AND contract_address = from_hex('2791bca1f2de4661ed88a30c99a7a9449aa84174')
)
SELECT
  CONCAT('0x', LOWER(to_hex(COALESCE(u.owner, r.recipient)))) AS wallet,
  ROUND(SUM(r.amt), 0) AS lp_rewards_usd
FROM lp_rewards_raw r
LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = r.recipient
GROUP BY 1
ORDER BY lp_rewards_usd DESC
LIMIT 100;
