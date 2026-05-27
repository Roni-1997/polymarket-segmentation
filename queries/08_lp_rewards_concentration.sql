-- LP rewards concentration by owner.
--
-- Use this for concentration statements (top 3 / top 10 / top 20 share).
-- It dedupes direct USDC transfers that occur in the same tx as merkle
-- claims, then maps proxy wallets to owners.

WITH merkle_rewards AS (
  SELECT evt_tx_hash, tokenReceiver AS recipient, amount/1e6 AS amt
  FROM polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed
),
direct_rewards AS (
  SELECT tr.evt_tx_hash, tr."to" AS recipient, tr.value/1e6 AS amt
  FROM erc20_polygon.evt_Transfer tr
  WHERE "from" = from_hex('c288480574783bd7615170660d71753378159c47')
    AND contract_address = from_hex('2791bca1f2de4661ed88a30c99a7a9449aa84174')
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
owner_rewards AS (
  SELECT
    COALESCE(u.owner, r.recipient) AS wallet,
    SUM(r.amt) AS rewards_usd
  FROM lp_rewards_raw r
  LEFT JOIN polymarket_polygon.users_address_lookup u
    ON u.polymarket_wallet = r.recipient
  GROUP BY 1
),
ranked AS (
  SELECT
    wallet,
    rewards_usd,
    ROW_NUMBER() OVER (ORDER BY rewards_usd DESC) AS rn,
    SUM(rewards_usd) OVER () AS total_rewards_usd
  FROM owner_rewards
  WHERE rewards_usd > 0
)
SELECT
  cutoff AS top_n,
  COUNT_IF(rn <= cutoff) AS wallets_in_cutoff,
  ROUND(SUM(CASE WHEN rn <= cutoff THEN rewards_usd ELSE 0 END), 0) AS rewards_usd,
  ROUND(
    SUM(CASE WHEN rn <= cutoff THEN rewards_usd ELSE 0 END)
      / MAX(total_rewards_usd) * 100,
    1
  ) AS pct_of_all_rewards,
  COUNT(*) AS total_rewarded_owners,
  ROUND(MAX(total_rewards_usd), 0) AS all_rewards_usd
FROM ranked
CROSS JOIN UNNEST(ARRAY[3, 10, 20, 50, 100]) AS t(cutoff)
GROUP BY cutoff
ORDER BY cutoff;
