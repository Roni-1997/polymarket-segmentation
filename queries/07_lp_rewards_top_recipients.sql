-- LP rewards distribution — fork of dune.com/queries/5989757.
-- UNIONs the two reward sources Polymarket uses:
--   1. MerkleDistributor airdrop (canonical post-2024 mechanism)
--   2. Direct USDC transfers from the rewards distributor wallet
--      0xc288480574783BD7615170660d71753378159c47
--      excluding transfers in the same tx as a merkle claim to avoid
--      double-counting the claim payout.
--
-- Material LP rewards are ground truth that a wallet participated in the
-- maker program. Dust rewards alone should be treated as weak evidence.
-- Aggregated to owner level via users_address_lookup.

WITH merkle_rewards AS (
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
)
SELECT
  CONCAT('0x', LOWER(to_hex(COALESCE(u.owner, r.recipient)))) AS wallet,
  ROUND(SUM(r.amt), 0) AS lp_rewards_usd,
  SUM(r.amt) >= 1000 AS lp_rewards_confirmed_1k
FROM lp_rewards_raw r
LEFT JOIN polymarket_polygon.users_address_lookup u ON u.polymarket_wallet = r.recipient
GROUP BY 1
ORDER BY lp_rewards_usd DESC
LIMIT 100;
