# Polymarket participant segmentation

Who trades on Polymarket, measured from the chain. Every wallet that traded in a window is sorted
into one of seven cohorts by two things: how much of its volume it makes rather than takes, and how
often it trades. The cohorts are then measured by volume, by depth provided, by flow consumed, by
market category and over time. The SQL runs on Dune's curated Polymarket tables and the result CSVs
are committed, so every number here can be rerun.

The main cohort tables are from 2026-05-27 (trailing 30 days, with Q4 2025 and Q1 2026 for the
trend). The expiry-volume table is from 2026-06-07. In September 2026 the same grid was applied to
Polymarket's BTC 5-minute markets with both legs of every fill and settlement PnL per cohort; that
note is at [docs/btc5m_cohorts_pnl.md](docs/btc5m_cohorts_pnl.md).

## Contents

- [Highlights](#highlights)
- [What this means for Verdict](#what-this-means-for-verdict)
- [September 2026: BTC 5-minute markets, PnL by cohort](#september-2026-btc-5-minute-markets-pnl-by-cohort)
- [Method](#method)
- [Cohorts](#cohorts)
- [Categories](#categories)
- [Roles: who provides depth and who consumes it](#roles-who-provides-depth-and-who-consumes-it)
- [Over time](#over-time)
- [Cross-venue: Polymarket and Hyperliquid HIP-4](#cross-venue-polymarket-and-hyperliquid-hip-4)
- [Open questions](#open-questions)
- [Repository layout](#repository-layout)
- [Reproducing the numbers](#reproducing-the-numbers)
- [Limitations](#limitations)
- [Expiry-volume note](docs/expiry_volume.md)

## Highlights

- Polymarket's real volume is about $102M a day. The headline figure counts both sides of every fill
  and is about twice that.
- Machines make the market. Market makers are 38% of touched volume and provide 69% of all depth.
  Bots and systematic traders are 56% of volume and consume 85% of taker flow. Strict retail, under
  10 fills a day, is 5% of volume venue-wide and 1.3% on BTC 5-minute markets.
- Retail's share halved in six months, 10.7% to 5.3%, while volume doubled from Q4 2025 to Q1 2026.
  The growth came from machines and maker capital, not from new retail.
- The paying flow is not casual retail either. On BTC 5-minute markets, settlement PnL moves about
  $49k a day from the Systematic-taker cohort (people using tools, 10 to 300 fills a day) and Retail
  to Pro-MM and Fast-taker. About 17% of touched volume, 29% of the taker side, loses by result and
  funds everyone else.
- Crypto binaries are the most automated category, with 75% of volume from the three fast cohorts,
  and their cohort mix is nearly identical to sports.
- Polymarket's machines do not migrate. None of its top 100 wallets is active on Hyperliquid HIP-4.
  The HIP-4 flow that exists comes from Hyperliquid perps traders.
- Liquidity rewards concentrate: the top 10 owners take 30% of all LP rewards, the top 50 take 50%.

## What this means for Verdict

Verdict builds short-dated outcome markets on Hyperliquid HIP-4. Read as go-to-market, the data says:

1. Liquidity is not the scarce input. Machines arrive within days of a launch, the 5-minute product
   opened at 46% machine share on its second day, and they are the book. Recruit market makers and
   neutral machines with a reliable settlement feed, fast cancels and clear rules. Do not spend to
   acquire casual retail; it is 1% to 5% of flow everywhere and shrinking.
2. Paying flow is the scarce input, and it is the tooled-up session trader, not the clicker. On
   Hyperliquid that profile is the perps trader who already sits one click from an HIP-4 book.
   Distribution runs through frontends and builder codes, Polymarket routes about 15% of its volume
   through 50 third-party frontends, not through a consumer funnel.
3. A consumer app is not the gate to product-market fit. It is where fees are collected and where the
   customer relationship is owned. Build it as a trader terminal with a builder program for other
   frontends and bots, and do not gate the launch on it.
4. Fee design decides which machines the venue hosts. Zero taker fees invite stale-quote machines
   that earn off makers and people; a taker fee removes that edge. Until fees exist, settlement design
   is what protects the makers.
5. Do not pitch what the venue cannot host. Complete-set arbitrage does not exist on HIP-4's mirror
   books, and Polymarket's machines are not migrating.
6. Measure after incentives, not during: repeat fee-paying strategies, depth at size, maker
   profitability after rewards, venue revenue net of incentives.

## September 2026: BTC 5-minute markets, PnL by cohort

Full note: [docs/btc5m_cohorts_pnl.md](docs/btc5m_cohorts_pnl.md). The seven-cohort grid was
applied to every fill on Polymarket's BTC 5-minute up/down markets on 2026-09-09, both legs,
1.38M records and $14.3M touched, with settlement PnL computed per cohort.

Retail is not the flow. Strict retail, under 10 fills per active day, is 1.3% of touched volume on
this product and was 5.3% venue-wide in May. Casual clickers do not explain the volume, the depth or
the growth of these venues.

Flow needs machines. Market makers and fast machines are 63% of touched volume, 74% of the maker
side and 95% of the taker side, and they show up within days of a product launching. They are the
book.

Machines need someone to pay them. On this day $49k moved from Systematic-taker (-$32k) and Retail
(-$12k) to Pro-MM (+$33k) and Fast-taker (+$16k). The payers are people using tools at 10 to 300
fills a day, not casual clickers. A venue therefore needs machines plus a steady supply of those
session traders, arriving through frontends, brokers and partner apps.

| Persona | % touched | % maker side | % taker side | PnL $ | May 2026 venue-wide |
|---|---:|---:|---:|---:|---:|
| MMs | 36.7% | 74.2% | 2.9% | +32,271 | 38.4% |
| Bots and algo | 62.0% | 25.6% | 94.9% | -19,786 | 56.3% |
| Retail | 1.3% | 0.3% | 2.2% | -12,485 | 5.3% |

The bots-and-algo persona nets negative as a whole because it contains both the payers
(Systematic-taker) and the earners (Fast-taker). The note proposes a second version of the grid that
separates operation mode and directionality so that this does not happen.

## Method

### What is measured

For each wallet that traded on Polymarket (CTF Exchange and NegRisk Exchange on Polygon) in the
window, behavioural features are computed from raw `OrderFilled` events and the wallet is placed in
one of seven cohorts. Volume, fill count, wallet count and average trade size are then aggregated per
cohort, category and side.

### Data

All on-chain, all free, from [Dune's curated tables](https://docs.dune.com/data-catalog/curated/prediction-markets/polymarket/overview).

| Table | Used for |
|---|---|
| `polymarket_polygon.market_trades` | Every fill: block time, maker, taker, amount, condition id |
| `polymarket_polygon.market_details` | Market metadata and the comma-separated `tags` used for categories |
| `polymarket_polygon.users_address_lookup` | Proxy wallet to owner EOA, so one firm with many proxies counts once |
| `polymarket_polygon.ctf_evt_positionsplit`, `ctf_evt_positionsmerge` | Complete-set arbitrage signals (not yet in the main classifier) |
| `polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed` | LP rewards, the strongest evidence that a wallet is a market maker |
| `erc20_polygon.evt_Transfer` from `0xc28848...` | Older direct LP-reward transfers, deduplicated against merkle claims |

### The seven cohorts

Two axes: maker share of a wallet's touched volume, and cadence, measured as fills per active day.
Below 10 fills a day the maker-taker distinction is an order-type preference rather than a role, so
the three low-cadence cells collapse into one Retail cohort.

| Maker share | Fast, 100+ fills a day | Systematic, 10 to 100 | Discretionary, under 10 |
|---|---|---|---|
| 70% or more | Pro-MM | Mid-MM | Retail |
| 30% to 70% | Hybrid-bot | Systematic-mixed | Retail |
| Under 30% | Fast-taker | Systematic-taker | Retail |

The labels describe behaviour, not identity. Fast-taker means high cadence and low maker share, not
a latency measurement. A Retail wallet may be a casual bettor, a large directional trader who places a
few big bets, or a hedger; the data only shows low cadence.

Why these thresholds: 70% maker share or more means the wallet mainly provides liquidity; 30% to 70%
means a mix (basket arbitrage, inventory rebalancing, news-reaction quoting); under 30% means it
mainly consumes liquidity. 100 or more fills a day is treated as automated. 10 to 100 is systematic
or tool-assisted: slow algorithms, copy-trading wrappers, heavy discretionary traders. Under 10 is
retail cadence.

Cadence is per active day, not per calendar day. A wallet with 30 fills on three days has cadence 10
and is systematic even if it was dormant for the other 27. The same 30 fills spread over 30 days give
cadence 1 and Retail.

### Owner aggregation

Wallets are aggregated to the owner level through `users_address_lookup`. Polymarket gives each user a
proxy wallet (Safe or Magic) controlled by an owner EOA, and trades happen at the proxy. Aggregating
to the owner means a firm running 30 proxies counts as one entity. EOAs that trade directly keep their
own address. Firms that split activity across several owner EOAs are not clustered; that would need
manual address work and is out of scope.

### Contract exclusion

Routing and system contracts are excluded both as raw maker or taker addresses and again after the
proxy-to-owner mapping, because some of them re-enter through the mapping.

| Address | Role |
|---|---|
| `0xe111180000d2663c0091e4f400237545b87b996b` | NegRisk adapter |
| `0xe2222d279d744050d28e00520010520000310f59` | NegRisk router |
| `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` | CTF Exchange |
| `0xc5d563a36ae78145c45a50134d48a1215220f80a` | Suspected router (106k fills a day, 0% maker) |

A `HAVING COUNT(*) <= 5,000,000` per window catches any router not on the list; no real wallet sustains
more than about 55,000 fills a day. Without these exclusions, Fast-taker volume is inflated by roughly
$3B a month of NegRisk basket pass-through. With them, the totals match Paradigm's finding that the
headline volume is about twice the real figure.

### Touched and single-counted volume

Touched volume is the maker-side amount plus the taker-side amount, so each fill counts twice, once
per participant. It is used for participant shares. Single-counted notional is half of that and is used
for venue volume, matching Paradigm and the corrected Polymarket dashboards. Both columns are in the
output of `04_cohort_x_category_30d.sql`.

### LP rewards as ground truth

To check whether a wallet really makes markets, two on-chain reward sources are combined: merkle
distributor claims, the standard mechanism since 2024, and USDC transfers from the rewards wallet
`0xc288480574783BD7615170660d71753378159c47`. Transfers in the same transaction as a claim are dropped
so that claims are not counted twice. A wallet counts as a confirmed LP at $1,000 or more of lifetime
rewards. Smaller amounts accumulate from incidental maker activity and prove little.

### Windows

The main window is the trailing 30 days to 2026-05-27. The trend uses Q4 2025 (Oct 1 to Jan 1) and
Q1 2026 (Jan 1 to Apr 1). Dune's free tier times out at two minutes, which rules out 180-day windows
in one query; use 30 or 90 days. Full specification in [docs/methodology.md](docs/methodology.md).

## Cohorts

Owner counts are from Q1 2026 (90 days) for stability; trailing-30-day counts are smaller in the same
ratio. Volume share is percent of touched volume.

| Cohort | In plain terms | Owners (Q1, 90d) | % volume (30d) | Avg $ per fill (30d) |
|---|---|---:|---:|---:|
| Pro-MM | Fast, 70%+ maker. The dedicated quoter, on around the clock. | 8,095 | 31.0% | $22 |
| Fast-taker | Fast, under 30% maker. News, latency and cross-venue trading. | 40,910 | 20.5% | $19 |
| Hybrid-bot | Fast, mixed maker and taker. NegRisk basket arbitrage, inventory rebalancing. | 11,603 | 17.9% | $27 |
| Systematic-taker | 10 to 100 fills a day, under 30% maker. Slow algorithms, copy traders, heavy discretionary traders with tools. | 199,448 | 12.7% | $38 |
| Mid-MM | 10 to 100 fills a day, 70%+ maker. Part-time or slower market making. | 21,541 | 7.4% | $91 |
| Systematic-mixed | 10 to 100 fills a day, mixed. Slow hybrid strategies, advanced discretionary. | 45,833 | 5.2% | $56 |
| Retail | Under 10 fills a day, any maker share. Casual bettors and low-frequency directional traders. | 926,087 | 5.3% | $48 |

Three-persona rollup:

| Persona | Cohorts | % volume (30d) |
|---|---|---:|
| Market makers | Pro-MM, Mid-MM | 38.4% |
| Bots and algo | Hybrid-bot, Fast-taker, Systematic-mixed, Systematic-taker | 56.3% |
| Retail | Retail | 5.3% |

An earlier, looser version of this classifier put retail at about 22% of volume. The difference is
the Systematic-taker cohort, 12.7% of volume: wallets doing 10 to 100 fills a day with low maker share.
They are small individually but they are not retail in behaviour.

## Categories

Ranked by single-counted notional over 30 days.

| Category | $M per 30d | % of platform | $M per day | Contents |
|---|---:|---:|---:|---|
| Other (untagged) | 1,100 | 35.8% | 37 | Mostly crypto binaries that lost their tags, see below |
| Sports | 906 | 29.5% | 30 | NBA, NFL, esports (Dota, CS2, LoL), soccer |
| Politics | 492 | 16.0% | 16 | Trump, elections, geopolitical politics |
| Crypto | 290 | 9.4% | 10 | 5m, 15m and 1h up/down binaries; undercounted in May, see below |
| Geopolitics | 163 | 5.3% | 5.4 | Iran, Ukraine, Russia, Gaza, world affairs |
| Finance | 41 | 1.3% | 1.4 | Fed, inflation, rates, oil |
| Weather | 40 | 1.3% | 1.3 | New category |
| Culture | 33 | 1.1% | 1.1 | Awards, MrBeast, film, music |
| Tech | 5 | 0.2% | 0.2 | AI, science, technology outcomes |

### Crypto and sports side by side

The two largest fast-resolving categories have nearly the same cohort mix. Both are machine-heavy and
neither has much retail.

| Cohort | Q1 crypto | Q1 sports | 30d crypto | 30d sports |
|---|---:|---:|---:|---:|
| Pro-MM | 30.5% | 29.8% | 31.7% | 32.9% |
| Mid-MM | 3.7% | 3.1% | 5.8% | 5.3% |
| Hybrid-bot | 24.0% | 26.6% | 17.4% | 21.6% |
| Systematic-mixed | 3.3% | 6.6% | 3.6% | 5.0% |
| Fast-taker | 23.7% | 17.9% | 26.0% | 21.1% |
| Systematic-taker | 8.1% | 10.7% | 10.5% | 11.5% |
| Retail | 6.8% | 5.4% | 5.0% | 2.7% |

| Persona | Q1 crypto | Q1 sports | 30d crypto | 30d sports |
|---|---:|---:|---:|---:|
| Market makers | 34% | 33% | 38% | 38% |
| Bots and algo | 59% | 62% | 58% | 59% |
| Retail | 7% | 5% | 5% | 3% |

Single-counted notional:

| Period | Crypto $M per day | Sports $M per day |
|---|---:|---:|
| Q1 2026 | 37.8 | 52.8 |
| 30d to May 27 | 9.7 | 30.2 |
| Change | -74% | -43% |

The crypto drop is a tagging artefact, not a volume loss. Between Q1 and May, Polymarket's recurring
5m, 15m and 1h crypto binaries moved from the Crypto tag to no tag at all:

| Category | Q1 2026, $M per day | 30d May 2026, $M per day | Change |
|---|---:|---:|---|
| Crypto | 37.8 | 9.7 | -74% |
| Other (untagged) | 0.5 | 36.7 | 73x |
| Crypto plus Other | 38.3 | 46.4 | +21% |

A 74% collapse in crypto against a 17% fall in platform volume is not plausible. Treat Crypto plus
Other as the real crypto share, about 45% of the platform in May. The Q1 numbers (Crypto 30.7%, Other
0.4%) describe the underlying market types better; the full Q1 table is in
[results/cohort_x_category_q1_2026.csv](results/cohort_x_category_q1_2026.csv). The sports decline is
mostly real, a seasonal fall from the NBA playoffs peak.

### Cohort mix within each category

Percent of the category's touched volume, 30 days.

| Category | Pro-MM | Mid-MM | Hybrid-bot | Sys-mixed | Fast-taker | Sys-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Crypto | 31.7% | 5.8% | 17.4% | 3.6% | 26.0% | 10.5% | 5.0% |
| Politics | 24.7% | 14.4% | 9.8% | 7.9% | 11.9% | 18.4% | 13.0% |
| Sports | 32.9% | 5.3% | 21.6% | 5.0% | 21.1% | 11.5% | 2.7% |
| Finance | 21.1% | 13.3% | 13.4% | 11.8% | 11.6% | 19.1% | 9.7% |
| Geopolitics | 31.8% | 13.0% | 5.2% | 5.2% | 17.3% | 14.8% | 12.7% |
| Culture | 24.2% | 11.3% | 14.6% | 10.8% | 8.6% | 19.7% | 10.8% |
| Weather | 32.9% | 9.5% | 10.5% | 6.5% | 17.8% | 18.2% | 4.6% |
| Tech | 23.8% | 11.0% | 13.7% | 9.6% | 11.3% | 18.0% | 12.7% |
| Other | 32.5% | 5.2% | 20.9% | 4.2% | 23.8% | 10.8% | 2.5% |

The same table as three personas:

| Category | Market makers | Bots and algo | Retail | Pattern |
|---|---:|---:|---:|---|
| Sports | 38% | 59% | 2.7% | Pro-MM and fast machines; almost no retail |
| Politics | 39% | 48% | 13.0% | The most retail of the large categories; Systematic-taker is the largest single cohort |
| Crypto | 38% | 58% | 5.0% | Pro-MM and Fast-taker; almost no retail |
| Finance | 34% | 56% | 9.7% | The most balanced mix; a Mid-MM tail |
| Geopolitics | 45% | 43% | 12.7% | Maker-heavy with large human bets |
| Weather | 42% | 53% | 4.6% | Machine-leaning |
| Culture | 36% | 54% | 10.8% | Systematic-taker leads; small category |
| Tech | 35% | 53% | 12.7% | Systematic-taker leads; small category |
| Other | 38% | 60% | 2.5% | Machines dominate the recurring residual |

Single-counted notional by cohort and category, $M over 30 days:

| Category | Pro-MM | Mid-MM | Hybrid-bot | Sys-mixed | Fast-taker | Sys-taker | Retail | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sports | 298 | 48 | 196 | 45 | 191 | 105 | 24 | 906 |
| Other | 358 | 57 | 230 | 46 | 262 | 119 | 28 | 1,100 |
| Politics | 122 | 71 | 48 | 39 | 58 | 90 | 64 | 492 |
| Crypto | 92 | 17 | 50 | 10 | 75 | 30 | 14 | 290 |
| Geopolitics | 52 | 21 | 9 | 9 | 28 | 24 | 21 | 163 |
| Finance | 9 | 6 | 6 | 5 | 5 | 8 | 4 | 41 |
| Weather | 13 | 4 | 4 | 3 | 7 | 7 | 2 | 40 |
| Culture | 8 | 4 | 5 | 4 | 3 | 7 | 4 | 33 |
| Tech | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 5 |

Reading across categories: crypto is the most automated, with 75% of volume from the three fast
cohorts and 5% retail. Politics has the most retail at 13% and the widest spread across cohorts, and
its retail trades are real money at about $110 each. Sports is 77% fast cohorts, and Hybrid-bot's
share is the highest of any category because NegRisk basket arbitrage works there. Finance is the most
balanced; Mid-MM at 13% is its second-highest share, since smaller makers like slow-resolving markets.
Geopolitics is maker-heavy with large human tickets, $400 to $550 per fill on average. Culture and
tech are long-tail categories led by Systematic-taker with 11% to 13% retail. Under the earlier looser
classifier, retail per category read 19% to 39%; under the strict definition it is 2.5% to 13%, the
difference again being Systematic-taker.

## Roles: who provides depth and who consumes it

A single volume share mixes two activities. Splitting the maker side from the taker side shows the
roles. Rows sum to 100%.

Share of the maker side, by category:

| Category | Pro-MM | Mid-MM | Hybrid-bot | Systematic-mixed | Fast-taker | Systematic-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sports | 58% | 9% | 22% | 5% | 4% | 1% | 1% |
| Politics | 46% | 26% | 10% | 8% | 2% | 2% | 7% |
| Crypto | 59% | 10% | 19% | 4% | 4% | 1% | 4% |
| Geopolitics | 59% | 23% | 5% | 5% | 1% | 1% | 6% |
| Finance | 38% | 23% | 13% | 12% | 3% | 3% | 8% |
| Other | 59% | 9% | 21% | 4% | 4% | 1% | 1% |

Pro-MM provides 38% to 59% of depth in every category. Market makers combined provide 65% to 82%.
Retail provides 1% to 8%.

Share of the taker side, by category:

| Category | Pro-MM | Mid-MM | Hybrid-bot | Systematic-mixed | Fast-taker | Systematic-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sports | 8% | 2% | 21% | 5% | 38% | 22% | 4% |
| Politics | 4% | 3% | 10% | 8% | 22% | 35% | 19% |
| Crypto | 5% | 1% | 16% | 4% | 49% | 20% | 6% |
| Geopolitics | 5% | 3% | 6% | 6% | 34% | 29% | 19% |
| Finance | 4% | 4% | 14% | 12% | 21% | 35% | 11% |
| Other | 6% | 1% | 21% | 4% | 44% | 20% | 4% |

Fast-taker and Systematic-taker together are 57% to 69% of taker flow in every category. Retail
consumes 4% to 19%. Market makers barely take at all, 4% to 11%.

Venue-wide, 30 days:

| Persona | Share of maker side | Share of taker side |
|---|---:|---:|
| Market makers | 69% | 8% |
| Bots and algo | 28% | 85% |
| Retail | 3% | 8% |

Market makers provide 69% of depth. Bots and algo consume 85% of flow. Retail provides 3% and
consumes 8%.

## Over time

| Cohort share of touched volume | Q4 2025 | Q1 2026 | 30d to May 27 | Change over six months |
|---|---:|---:|---:|---:|
| Pro-MM | 23% | 29% | 31% | +8 points |
| Fast-taker | 12% | 17% | 21% | +9 points |
| Hybrid-bot | 23% | 22% | 18% | -5 points |
| Systematic-taker | 13% | 12% | 13% | flat |
| Systematic-mixed | 12% | 7% | 5% | -7 points |
| Mid-MM | 7% | 5% | 7% | flat |
| Retail | 11% | 8% | 5% | -6 points, halved |

| Persona | Q4 2025 | Q1 2026 | 30d to May 27 | Change |
|---|---:|---:|---:|---:|
| Market makers | 31% | 34% | 38% | +7 points |
| Bots and algo | 58% | 58% | 56% | flat |
| Retail | 11% | 8% | 5% | -6 points, halved |

Single-counted volume went from $58M a day in Q4 2025 to $123M in Q1 2026 and $102M in the 30 days to
May 27.

Three things follow. Retail's share halved in six months under the strict definition, 10.7% to 7.7%
to 5.3%; the looser classifier showed 33% to 22%, a decline that understated the size of the move.
Market makers kept gaining share, Pro-MM by 8 points with Mid-MM flat, so the professionalisation is
maker capital scaling as well as machines replacing retail. And the question this raised in May, whether
the systematic cohorts are uninformed enough to serve as the counterparty that market makers need, was
answered for BTC 5m in September: Systematic-taker loses 2.0% per dollar and supplies two thirds of the
losses. Counting it, uninformed flow is about 17% of touched volume and 29% of the taker side on that
product.

## Cross-venue: Polymarket and Hyperliquid HIP-4

Sister analysis in [hip4_cross_venue/](hip4_cross_venue/). HIP-4 outcome markets went live on
Hyperliquid on 2026-05-02.

| Check | Result |
|---|---|
| Top 100 Polymarket wallets by volume that appear in the HIP-4 top 127 | 0 of 100 |
| Top 25 LP-reward recipients that appear in the HIP-4 top 127 | 0 of 25 |
| Top 30 Polymarket wallets with any Hyperliquid perp activity | 2 of 30 |
| Top 30 Polymarket wallets with HIP-4 activity | 0 of 30 |
| HIP-4 top 30 with any Polygon activity | 10 of 30, casual and not Polymarket-specific |

Polymarket's market-making group is not moving to HIP-4. The obstacles are structural: Polygon
against Hyperliquid signing, USDC.e against USDC, Gnosis Safe with meta-transactions against direct
EOAs, UMA resolution against validator votes. The traders who do appear on HIP-4 come from Hyperliquid
perps, not from Polymarket.

## Open questions

Things the repository does not yet measure, in rough order of value.

1. PnL by cohort beyond BTC 5m. Done for one product on one day in
   [docs/btc5m_cohorts_pnl.md](docs/btc5m_cohorts_pnl.md). Still open: other categories, longer
   windows, owner level. Solidus measured profit concentration in politics only (0.55% of wallets take
   50% of profit, December 2025 to February 2026); reproducing that across categories would show
   whether it generalises and would quantify adverse selection per cohort. Sources: the defioasis PnL
   dashboard and position-state reconstruction. One to two weeks.
2. Cross-venue arbitrage between Polymarket and Kalshi. The fall in Systematic-mixed (11.6% to 5.2%)
   and Retail (10.7% to 5.3%) may reflect migration to Kalshi. Confirming it needs Kalshi trade data
   and timestamp matching across venues. Three to five days.
3. Firm attribution. The top 10 LP-reward owners are identifiable by address. Mapping them to firms
   needs manual labelling against public registries and clustering of sibling EOAs. One to two days.
4. Wash-trade exclusion. Solidus flagged about 15% of some markets as wash trading consistent with
   airdrop farming. Filtering paired YES and NO positions by the same owner in the same market within a
   short window would shrink Systematic-mixed and Retail, probably by 2 to 5 points. Two to three days.
5. Builder program attribution. Some machine volume routes through Polymarket's builder program, 231
   registered apps as of late 2025 including Telegram bots and copy-trading wrappers. Joining trades to
   the builder registry would separate direct API flow from wrapper flow. One day.
6. The untagged bucket. 35% of platform volume has no tag. Most of it is recurring crypto and sports
   markets; closing the gap needs Polymarket's internal taxonomy.
7. A complete-set arbitrage cohort. Dune exposes position split and merge events; adding them to the
   classifier would carve that cohort out of Hybrid-bot. One day.
8. A monthly rerun. Pin the `params` CTE to explicit timestamps, schedule the queries, and chart the
   cohort distribution over time. Two to three days.

Not attempted, by choice: market-size forecasts (this is a microstructure study, not a TAM estimate),
comparisons against every other venue (HIP-4 is covered; Kalshi, Manifold, Limitless and Myriad are
open), and recommendations about which categories another venue should list.

## Repository layout

| Path | Contents |
|---|---|
| [docs/findings.md](docs/findings.md) | Detailed findings and the mapping from each result to its query |
| [docs/methodology.md](docs/methodology.md) | Classifier specification, contract exclusions, schema notes |
| [docs/external_research.md](docs/external_research.md) | Cross-checks against Paradigm, Solidus, Chainalysis and Dune dashboards |
| [docs/expiry_volume.md](docs/expiry_volume.md) | Trailing-30-day volume by time to resolution |
| [docs/btc5m_cohorts_pnl.md](docs/btc5m_cohorts_pnl.md) | BTC 5m in the cohort grid with PnL per cohort, September 2026 |
| [queries/](queries/) | 12 SQL files; paste any into Dune |
| [results/](results/) | Result CSVs from the audited reruns and the BTC 5m cohort tables |
| [scripts/btc5m/](scripts/btc5m/) | Data-api pull and cohort classifier used for the BTC 5m note |
| [hip4_cross_venue/](hip4_cross_venue/) | Polymarket and HIP-4 overlap, both directions |

## Reproducing the numbers

Open [dune.com](https://dune.com), create a query, paste any file from [queries/](queries/), and run
it. The core queries cost about 350 credits in total, within the free tier's 2,500 a month. Run them
in order: 01 (action enum probe), 02 (tags probe), 03 (untagged-category probe), 04 (cohort by
category, the main table), 05 (top 20 per cohort, for validation), 06 (twice, with different quarter
windows, for the trend), 07 (LP recipients), 08 (LP concentration), 09 (drilldown with wallets, fills
and average trade), 10 (maker and taker split), 11 (venue-wide top 100 with LP flags, for the
cross-venue checks), 12 (trailing-30-day volume by time to expiry). Programmatic execution through the
Dune MCP server is described in [docs/methodology.md](docs/methodology.md).

The BTC 5m note is reproduced from Polymarket's public data-api with the two scripts in
[scripts/btc5m/](scripts/btc5m/).

## Limitations

1. The main window is 30 days; the quarterly comparisons are 90 days. Dune's free tier cannot run
   180 days in one query.
2. The CSVs are snapshots from 2026-05-27. Most queries use rolling windows, so reruns drift unless
   the `params` CTE is pinned.
3. The cohort labels are approximate. The classifier forces discrete buckets by first-match rule order,
   wallets near a boundary (60% to 70% maker share) could go either way, and the numbers move about
   5 points when thresholds move. Treat them as directional.
4. Owner aggregation does not cluster across firm-owned EOAs. A firm running five EOAs counts as five.
5. The untagged category is about 35% of platform volume even after expanded tag matching.
6. Paradigm and Solidus are not neutral sources. Paradigm has invested in Kalshi and Solidus sells
   compliance software. Their on-chain methods are verifiable; their framing is theirs. See
   [docs/external_research.md](docs/external_research.md).
7. PnL by cohort is measured for BTC 5m on one day, not venue-wide. Volume share is not profit share.
   Solidus finds that 0.55% of wallets take 50% of profit in politics; here the top 10 LP-reward owners
   take 30% of rewards. Different metrics, both pointing the same way.
