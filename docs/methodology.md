# Methodology

How wallets are classified, what's excluded, and why.

## The pipeline

```
polymarket_polygon.market_trades (raw fills)
    │
    ├─► exclude routing contracts (NegRisk adapter + 3 others)
    │
    ├─► JOIN users_address_lookup (proxy → owner)
    │
    ├─► UNION ALL maker + taker rows → wallet_sides
    │
    ├─► aggregate per (wallet, window) → wallet_features
    │       │ COUNT(*), SUM(notional), maker_vol, n_active_days,
    │       │ n_unique_markets
    │       │ exclude system wallets again after owner mapping
    │       │ HAVING n_fills ≤ 5,000,000 (safety net for missed contracts)
    │
    ├─► classify into 9-cell grid (maker_band × cadence_band) → cohorts
    │
    ├─► JOIN market_details for category → wallet_cat_vol
    │
    └─► output: cohort × category × touched volume
```

## Volume convention

The cohort queries intentionally fan every fill into two rows: one maker
row and one taker row. The resulting `total_vol` / `total_touched_musd`
is **touched volume**, not single-counted venue notional.

Use touched volume for participant shares:

```
segment touched volume / total touched volume
```

Use single-counted notional for venue volume:

```
equivalent single-counted notional = touched volume / 2
```

This distinction is load-bearing. MMs that take liquidity still count as
MM flow once their wallet is classified as an MM, but absolute dollar
volume must not be compared to public venue volume until divided by 2.

## Wallet aggregation: owner level, not proxy level

Each Polymarket user has a proxy wallet (Safe or Magic) controlled by an
owner EOA. Trades happen at the proxy level. We aggregate to **owner
level** via `users_address_lookup` so one MM running many proxies counts
as one entity.

EOAs that trade directly (no proxy) keep their own address — correct.

This DOES NOT cluster across multiple owner EOAs run by the same firm
(e.g., one MM with 5 independent EOAs for risk separation). That would
require manual address clustering, which is out of scope.

## Cohort classification (9-cell grid)

The current main classifier is a maker-share × cadence grid. It does not
yet create a separate complete-set-arber cohort. Add split/merge features
from Conditional Tokens events before making arber-share claims.

```
                    cadence_band (n_fills / n_active_days)
                    ──────────────────────────────────────
                    fast (≥100)   med (1-100)   slow (<1)
                    ─────────────────────────────────────
maker_band   high   Pro-MM        Mid-MM        Passive-quoter
(70-100%)
             mid    Hybrid-bot    Active-mixed  Casual-mixed
(30-70%)
             low    HFT-taker     Active-retail Casual-retail
(<30%)
```

**Three of nine cells are empty by construction**: "slow" cadence (<1
fill per active day) is mathematically impossible because we define an
"active day" as one where a fill occurred. So `n_fills / n_active_days
≥ 1` always.

In practice, only six cohorts have meaningful volume.

## Why these thresholds

- **maker_share ≥ 0.70**: a wallet whose primary role is providing
  liquidity. 60-70% is the soft boundary; pure passive quoters are 85%+;
  hybrid strategies are 30-70%; pure-take is <30%.
- **fills/day ≥ 100**: bot-cadence threshold. Real HFT bots fire
  thousands of times per day; 100 fills/day is the lower bound for
  "this is automated" with high confidence.
- **fills/day ∈ [1, 100)**: active human or slow bot. Human discretionary
  traders typically fall in 5-50 fills/day on active days.

**These are reasonable defaults, not gospel.** The 70% maker-share line
is the most sensitive — sliding it to 60% moves ~5pp from HFT-taker
into Pro-MM.

## Contract exclusion

NegRisk multi-outcome markets route through adapter contracts. System
addresses can appear either as raw maker/taker addresses or, after
`users_address_lookup`, as owner addresses. We therefore exclude them in
both places.

| Address | What it is |
|---|---|
| `0xe111180000d2663c0091e4f400237545b87b996b` | NegRisk Adapter |
| `0xe2222d279d744050d28e00520010520000310f59` | NegRisk router (sibling) |
| `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` | CTF Exchange contract |
| `0xc5d563a36ae78145c45a50134d48a1215220f80a` | Suspected router (106k fills/day, 0% maker) |

**Safety net**: `HAVING COUNT(*) <= 5,000,000` per analysis window at
the `wallet_features` step. Catches any missed system actor with extreme
fill count.

Do not infer the venue's true notional reduction directly from this
filter. The cohort outputs are touched volume; compare to headline venue
volume only after converting to single-counted notional.

## Category mapping (regex on `market_details.tags`)

Tags are stored as a comma-separated VARCHAR. First element is the
high-level category. Match patterns:

| Category | Patterns |
|---|---|
| crypto | `Crypto%` |
| sports | `Sports%`, `Soccer%`, `Football%`, `football%` |
| politics | `Politic%`, `Trump%`, `Elections%` |
| culture | `Pop Culture%`, `Culture%`, `Entertain%`, `Awards%`, `MrBeast%`, `YouTube%`, `Movies%`, `Music%`, `box office%`, `Celebrities%`, `SpaceX%`, `Breaking News%`, `Prediction Markets%` |
| finance | `Business%`, `Econ%`, `Fed%`, `Trade Wars%`, `Macro%`, `Finance%`, `Stocks%`, `Markets%`, `Oil%`, `Inflation%`, `interest rates%` |
| geopolitics | `Geopolit%`, `World%`, `Middle East%`, `War%`, `Iran%`, `Ukraine%`, `Russia%`, `China%`, `Venezuela%`, `Syria%`, `Gaza%`, `world affairs%`, `strike%`, `Brazil%`, `UK%` |
| weather | `Weather%` |
| tech | `AI%`, `Science%`, `Tech%` |
| other | everything else (including null tags) |

The "other" bucket can still be large, mostly because some recurring
high-frequency crypto/sports markets have NULL tags. Resolving this would
require an external market-to-tag registry.

## LP rewards ground truth

Two sources, UNION'd after deduplication:

1. `polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed`
   — merkle airdrop claims (the canonical rewards mechanism).
2. `erc20_polygon.evt_Transfer` where `"from" = 0xc28848...` (the rewards
   distributor wallet) and `contract_address = USDC` — older direct-transfer
   path. Transfers in the same transaction as a merkle claim are excluded
   to avoid double-counting claim payouts.

Aggregated per owner via `users_address_lookup` (rewards go to proxy
wallets; the owner is the firm).

Use two reward flags:

| Flag | Meaning |
|---|---|
| `lp_rewards_observed` | Any reward history, including dust |
| `lp_rewards_confirmed_1k` | At least $1,000 in rewards; stronger MM-program evidence |

Dust rewards are not enough to call a wallet an MM. Use
`lp_rewards_confirmed_1k` for validation claims.

## Schema gotchas encountered

1. **`market_trades.action` only has value `"CLOB trade"`** — despite
   docs claiming three types incl. MINT/MERGE. Use
   `ctf_evt_positionsplit` / `ctf_evt_positionsmerge` for arber
   detection.
2. **`condition_id` type mismatch**: `market_trades` stores it as
   `varbinary`; `market_details` as VARCHAR `'0x...'`. JOIN must cast:
   `md.condition_id = '0x' || LOWER(to_hex(t.condition_id))`.
3. **`market_details` has multiple rows per `condition_id`** (one per
   outcome). Always pre-aggregate to one row per condition_id before
   joining trades.
4. **`market_start_time`, `market_end_time`** stored as VARCHAR — use
   `try_cast(... AS timestamp)` if you need them.
5. **Dune free-tier SQL timeout is 2 minutes.** 90-day windows fit;
   180-day usually doesn't unless query is simplified.

## Running it

### Reproducible windows

Most query files use a rolling `CURRENT_TIMESTAMP - INTERVAL '30' DAY`
window for convenience. The committed CSVs are snapshots from
2026-05-27. If you need exact reproduction of the committed numbers,
replace the `params` CTE with explicit timestamps for the intended
window before running.

### Via Dune web UI
Paste queries from [queries/](../queries/) into the editor at
[dune.com/queries](https://dune.com/queries). Costs ~10–45 credits each.

For wallet-level exports, watch Dune result pagination. Query 05 can
return 120 rows (20 per cohort); Dune API defaults can clip that to 100
unless you request a larger result limit. Use query 11 for true
venue-wide top-wallet samples.

### Via Dune MCP (programmatic)
We drove the analysis via the Dune MCP server exposed at
`https://api.dune.com/mcp/v1`. Requires a Dune API key (Plus tier).
Key tools used: `createAndExecuteQuery`, `updateDuneQuery`,
`executeQueryById`, `getExecutionResults`, `searchTables`, `searchDocs`.

```bash
# Register MCP for Claude Code:
claude mcp add --scope user --transport http dune \
  https://api.dune.com/mcp/v1 \
  --header "x-dune-api-key: <YOUR_KEY>"
```

Tool arg-naming inconsistency: `executeQueryById` wants `query_id`
(snake_case); `getExecutionResults` wants `executionId` (camelCase);
`updateDuneQuery` wants `queryId` (camelCase) and `query` (NOT
`query_sql`). Worth noting if you write a wrapper.
