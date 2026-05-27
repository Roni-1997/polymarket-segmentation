-- HIP-4 wallets -> Polymarket-specific activity check.
--
-- Use this to replace the weaker Polygon nonce check. A nonzero Polygon nonce
-- only proves generic Polygon activity; this query checks whether the HIP-4
-- address itself, or a Polymarket proxy wallet owned by that address, appears
-- in Polymarket curated trades.

WITH hip4_addresses(address) AS (
  VALUES
    (from_hex('e5dfc1970021fa328ab00319e20ebd175588c799')),
    (from_hex('c57c395e36d14ae6012e027b297407f7ab1167c7')),
    (from_hex('b565c0883d58cfc6009f1802dddef9f792332501')),
    (from_hex('95c16466ea54608c4d1ffb931441a08476cfb3f2')),
    (from_hex('3550dd33e3e6af5cd76822526af8cac37ba1d865')),
    (from_hex('caef5b46df8077a07ddb2e1be56e768d8c81f6e0')),
    (from_hex('017e019d6344b47854635ee87f728831260c87b5')),
    (from_hex('f39334f850d98243d8c617dbf904bbf2a1133924')),
    (from_hex('639520cfffa19179b32b839aef8c7e2b751816c5')),
    (from_hex('5ac1b6f6eec98dd9469266eefeaca04798945f15')),
    (from_hex('f6afb4d9573126e1de617ea6e9f60751b642bbcd')),
    (from_hex('a17f5c11aa82798658754a5a563141c535441a79')),
    (from_hex('f7ead3beb35f90df555f8cb1b10cfec286cc8af5')),
    (from_hex('db77d93a976081cd2c97914b72d27f9b053c843f')),
    (from_hex('78eb1125787b82c89bd8afb46f4330c70b7dc471')),
    (from_hex('fe3a32434dc67aeabf01ebbbca205fc79d893c9b')),
    (from_hex('a67fdce246f7d442bdbb3d9e286d4d5a59bdc8b7')),
    (from_hex('72d0b1f98fd9cdd4e46976edd86857b0266a62ea')),
    (from_hex('1c1511b650f24fd7a7c3c7ad05b835f5363f8695')),
    (from_hex('9ff2650389420617f6ddef53a4c038a65e3775b7')),
    (from_hex('0606f126f03ee5f51f168fbe9be39ea5370a9bee')),
    (from_hex('d32c02b6e897b0a75c0fd9dd0d529c739a0430a5')),
    (from_hex('38c2b9325e8b080058c31f44a13a56464a6a0fc2')),
    (from_hex('5f0ef9ca677a3df3b89060b13593ec528ae91f9e')),
    (from_hex('9d8ca8a9ff83e706b15ba20bc8722a7bf3742160')),
    (from_hex('57174ba8ac5cfcf8339d0cadf1b16a51122e0572')),
    (from_hex('58907a1b3a45b6b228a5f8127eb1277c0e533c44')),
    (from_hex('d501ccbdb70ce518b2da68c685045fa54458ec35')),
    (from_hex('69cdee059a750b584473e3370be6a4555ac837ec')),
    (from_hex('f47d3b1f4773ebd91c0c6544d47a77c0d334d0e0'))
),
proxy_wallets AS (
  SELECT
    h.address AS hip4_address,
    u.polymarket_wallet
  FROM hip4_addresses h
  JOIN polymarket_polygon.users_address_lookup u
    ON u.owner = h.address
),
trades AS (
  SELECT
    block_time,
    tx_hash,
    maker,
    taker,
    amount,
    event_market_name,
    question
  FROM polymarket_polygon.market_trades
  WHERE block_time >= NOW() - INTERVAL '365' DAY
),
matches AS (
  SELECT h.address AS hip4_address, 'direct_maker' AS match_type, t.*
  FROM trades t
  JOIN hip4_addresses h ON t.maker = h.address

  UNION ALL

  SELECT h.address AS hip4_address, 'direct_taker' AS match_type, t.*
  FROM trades t
  JOIN hip4_addresses h ON t.taker = h.address

  UNION ALL

  SELECT p.hip4_address, 'proxy_maker' AS match_type, t.*
  FROM trades t
  JOIN proxy_wallets p ON t.maker = p.polymarket_wallet

  UNION ALL

  SELECT p.hip4_address, 'proxy_taker' AS match_type, t.*
  FROM trades t
  JOIN proxy_wallets p ON t.taker = p.polymarket_wallet
),
proxy_counts AS (
  SELECT
    hip4_address,
    COUNT(DISTINCT polymarket_wallet) AS owned_polymarket_proxy_wallets
  FROM proxy_wallets
  GROUP BY 1
),
match_rollup AS (
  SELECT
    hip4_address,
    COUNT(*) AS polymarket_side_matches,
    ROUND(SUM(COALESCE(amount, 0)), 2) AS polymarket_matched_side_volume_usd,
    COUNT_IF(match_type IN ('direct_maker', 'proxy_maker')) AS maker_side_matches,
    COUNT_IF(match_type IN ('direct_taker', 'proxy_taker')) AS taker_side_matches,
    MIN(block_time) AS first_polymarket_match,
    MAX(block_time) AS last_polymarket_match
  FROM matches
  GROUP BY 1
)
SELECT
  CONCAT('0x', LOWER(to_hex(h.address))) AS hip4_address,
  COALESCE(p.owned_polymarket_proxy_wallets, 0) AS owned_polymarket_proxy_wallets,
  COALESCE(m.polymarket_side_matches, 0) AS polymarket_side_matches,
  COALESCE(m.polymarket_matched_side_volume_usd, 0) AS polymarket_matched_side_volume_usd,
  COALESCE(m.maker_side_matches, 0) AS maker_side_matches,
  COALESCE(m.taker_side_matches, 0) AS taker_side_matches,
  m.first_polymarket_match,
  m.last_polymarket_match
FROM hip4_addresses h
LEFT JOIN proxy_counts p
  ON h.address = p.hip4_address
LEFT JOIN match_rollup m
  ON h.address = m.hip4_address
ORDER BY polymarket_matched_side_volume_usd DESC, polymarket_side_matches DESC;
