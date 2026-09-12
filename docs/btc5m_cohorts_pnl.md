# BTC 5m up/down in the seven-cohort grid, with PnL by cohort (September 2026)

Update to the May 2026 segmentation. Same grid (maker share of touched volume by fills per active day),
applied to every fill on Polymarket's BTC 5-minute up/down markets on 2026-09-09 UTC, both legs, with the
question the May work left open answered: who makes money and who pays.

## The claim

**Retail is not the flow.** People placing fewer than 10 trades a day were 1.2% of volume on the Bitcoin
5-minute markets over the 30 days to September 9, and 5.3% across the whole venue in May. Nothing about
these venues' volume, depth or growth is explained by casual bettors, and the story that prediction
markets run on them should be retired.

**Flow needs bots.** Market makers and fast trading bots were 82% of volume over the same 30 days. Market
makers posted 75% of all resting orders; bots took 92% of all aggressive trades. They show up within days
of a market launching (Polymarket's 5-minute market was 46% bots on its second day) and they are the
order book. A venue without them has nothing to trade against and no depth to show.

**Bots need someone to pay them.** Every dollar a bot wins at settlement is a dollar someone else lost.
Over the 30 days about $44,000 a day moved from the people who lose to the market makers and bots who
win. The losers are not casual bettors, who are too few to matter. They are active traders using tools,
placing 10 to 300 trades a day, who trade in sessions, size their orders in dollars and lose about 2 cents
per dollar traded. Bot volume follows that supply: when Polymarket's inflow of new wallets fell 80%
between spring and autumn, bot volume fell 43%. A venue therefore needs the bots plus a steady supply of
these active traders, arriving through front ends, brokers and partner apps, not a consumer funnel for
casual bettors.

## Data and method

- Source: Polymarket data-api `/trades` per market, `takerOnly=true` and `takerOnly=false`, for all 288
  markets of 2026-09-09 (gamma `/events?series_id=10684`). 1,383,413 records: 476,400 taker legs and 907,013
  maker legs, identified by matching (transaction hash, wallet, side, size, price, outcome) against the
  taker-only set. 8,328 proxy wallets. Touched $14.28M, single-counted $7.14M. Two markets hit the API
  pagination limit at 11,000 records and are truncated.
- Cohorts: maker share of touched volume 70%+ high, 30-70% mid, under 30% low; cadence 100+ fills fast,
  10-100 systematic, under 10 discretionary; Retail at any maker share under 10. Single day, so cadence is
  fills that day.
- Differences from the May pipeline: data-api rather than Dune, proxy-wallet level with no owner
  aggregation (merging a firm's proxies would lower machine wallet counts, not dollar shares), one product,
  one day at a time. Aug 30 and Sep 8 were processed the same way; the three-day tables are below.
- PnL to settlement per leg: a buy of an outcome pays 1 if it wins, a sell the reverse. No fees (none were
  charged on these markets), no rewards, no positions carried across the day, no external hedges. It
  measures transfer between cohorts on the venue, not firm profit.
- Scripts: `scripts/btc5m/pull_both_legs.py`, `scripts/btc5m/cohorts_v1_v2.py`. Results:
  `results/btc5m_cohorts_v1_2026-09-09.csv`, `results/btc5m_cohorts_v2_2026-09-09.csv`.

## The grid on 2026-09-09 (superseded by the 30-day window below)

| Cohort | Wallets | % touched | % maker side | % taker side | $ per fill | PnL per $ | PnL $ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pro-MM | 545 | 35.5% | 71.8% | 2.7% | 7 | +0.66% | +33,254 |
| Fast-taker | 711 | 34.6% | 6.6% | 59.9% | 14 | +0.32% | +15,806 |
| Hybrid-bot | 171 | 15.1% | 17.4% | 13.1% | 12 | -0.11% | -2,439 |
| Systematic-taker | 2,742 | 11.3% | 0.6% | 20.9% | 17 | -2.01% | -32,274 |
| Mid-MM | 435 | 1.2% | 2.4% | 0.2% | 10 | -0.56% | -983 |
| Systematic-mixed | 301 | 1.0% | 1.0% | 1.0% | 13 | -0.61% | -879 |
| Retail | 3,423 | 1.3% | 0.3% | 2.2% | 15 | -6.85% | -12,485 |

Three-persona rollup against the May figures:

| Persona | BTC 5m Sep 9, % touched | % maker side | % taker side | PnL $ | Venue-wide May | Crypto May |
|---|---:|---:|---:|---:|---:|---:|
| MMs (Pro-MM, Mid-MM) | 36.7% | 74.2% | 2.9% | +32,271 | 38.4% | 38% |
| Bots + Algo | 62.0% | 25.6% | 94.9% | -19,786 | 56.3% | 58% |
| Retail | 1.3% | 0.3% | 2.2% | -12,485 | 5.3% | 5% |

The product is the venue's fingerprint with retail squeezed further. The Bots + Algo persona nets
negative as a whole because it contains both the payers (Systematic-taker) and the earners (Fast-taker).

## Proposed refinement: split the cadence axis by operation mode and directionality

The v1 cells mix people with tools and part-day machines, and Fast-taker mixes market-neutral machines
that earn with directional machines that do not. A v2 with the same maker-share axis, an operation-mode
axis (unattended: no 6-hour gap between orders or 16+ active hours; part-day machine: buys both outcomes
in 40%+ of its markets, or trades 50%+ of available windows over a 4-hour span in share-denominated
sizes; session: neither) and a directionality flag (neutral: both outcomes bought in 40%+ of markets)
gives six cohorts. PnL is not an input; it is the validation, and it orders correctly on this day.

| v2 cohort | Wallets | % touched | % maker side | % taker side | PnL per $ | PnL $ | Exact-dollar buys | Sells | Active hours |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pro-MM | 687 | 34.3% | 69.7% | 2.3% | +0.77% | +37,830 | 3% | 8% | 20 |
| Part-time MM | 240 | 2.4% | 4.4% | 0.5% | -1.31% | -4,390 | 4% | 7% | 6 |
| Neutral bot | 376 | 25.0% | 14.3% | 34.7% | +1.38% | +49,480 | 10% | 6% | 9 |
| Directional bot | 1,107 | 21.5% | 8.1% | 33.6% | -0.23% | -7,158 | 6% | 7% | 18 |
| Session trader | 2,374 | 15.3% | 3.1% | 26.3% | -2.76% | -60,356 | 41% | 27% | 5 |
| Retail | 3,544 | 1.5% | 0.4% | 2.5% | -7.16% | -15,406 | 0% | 19% | 1 |

Rollup: MMs 36.7% (+$33k), Machines 46.5% (+$42k), People 16.8% (-$76k). Crosswalk of v1 touched dollars:
Fast-taker splits into Neutral bot 46%, Directional bot 39%, Session trader 15%; Hybrid-bot into Neutral
bot 57%, Directional bot 34%, Session trader 10%; Systematic-taker into Session trader 71%, Directional bot
24%. Exact-dollar sizing (the web app takes dollar amounts, the API takes share counts) and early exits
separate the people from the machines in every cell.

## Three days: Aug 30, Sep 8 and Sep 9, 2026 (superseded by the 30-day window below)

Same method on three days, 4,283,811 records and $42.0M touched ($14.0M a day). Shares are the
mean of the daily shares; PnL dollars are summed. Two markets a day hit the pagination limit and are truncated.

| Cohort | Wallets per day | % touched | % maker side | % taker side | PnL per $ | PnL $, three days | % touched by day (Aug 30, Sep 8, Sep 9) |
|---|---:|---:|---:|---:|---:|---:|---|
| Pro-MM | 518 | 35.4% | 69.1% | 3.2% | +0.53% | +80,943 | 35.8, 34.8, 35.5 |
| Fast-taker | 727 | 31.8% | 5.3% | 57.1% | +0.31% | +44,692 | 25.7, 35.2, 34.6 |
| Hybrid-bot | 192 | 18.0% | 19.7% | 16.4% | +0.10% | +8,427 | 22.7, 16.2, 15.1 |
| Systematic-taker | 2,673 | 10.3% | 0.5% | 19.8% | -2.09% | -94,766 | 9.6, 10.2, 11.3 |
| Mid-MM | 438 | 2.1% | 4.1% | 0.2% | -1.12% | -8,914 | 3.7, 1.4, 1.2 |
| Systematic-mixed | 311 | 1.1% | 1.0% | 1.1% | -0.33% | -1,400 | 1.1, 1.2, 1.0 |
| Retail | 3,533 | 1.3% | 0.3% | 2.2% | -5.53% | -29,025 | 1.4, 1.1, 1.3 |

| Persona | % touched | % maker side | % taker side | PnL $, three days | May 2026 venue-wide |
|---|---:|---:|---:|---:|---:|
| MMs (Pro-MM, Mid-MM) | 37.5% | 73.2% | 3.4% | +72,029 | 38.4% |
| Bots and algo | 61.3% | 26.5% | 94.4% | -43,046 | 56.3% |
| Retail | 1.3% | 0.3% | 2.2% | -29,025 | 5.3% |

Pro-MM, Fast-taker and Hybrid-bot together are 85% of touched volume. Market makers provide 73% of the
maker side; bots and algo consume 94% of the taker side. Retail is 1.3%. Settlement PnL moves about
$41k a day from Systematic-taker and Retail to Pro-MM and Fast-taker.

The proposed v2 split on the same three days:

| v2 cohort | Wallets per day | % touched | % maker side | % taker side | PnL per $ | PnL $, three days | PnL per $ by day |
|---|---:|---:|---:|---:|---:|---:|---|
| Pro-MM | 647 | 35.3% | 69.2% | 3.0% | +0.60% | +90,120 | +0.32%, +0.71%, +0.77% |
| Part-time MM | 253 | 2.1% | 3.9% | 0.4% | -1.98% | -16,845 | -2.53%, -2.12%, -1.31% |
| Neutral bot | 409 | 25.4% | 14.5% | 35.9% | +1.20% | +130,826 | +0.89%, +1.33%, +1.38% |
| Directional bot | 1,068 | 20.5% | 8.5% | 31.9% | +0.30% | +21,671 | +1.15%, +0.00%, -0.23% |
| Session trader | 2,361 | 15.1% | 3.4% | 26.3% | -2.88% | -182,139 | -3.02%, -2.84%, -2.76% |
| Retail | 3,653 | 1.5% | 0.5% | 2.6% | -6.93% | -43,676 | -2.62%, -11.00%, -7.16% |

| Rollup | % touched | % maker side | % taker side | PnL $, three days |
|---|---:|---:|---:|---:|
| MMs | 37.4% | 73.0% | 3.4% | +73,275 |
| Machines | 45.9% | 23.0% | 67.8% | +152,497 |
| People | 16.7% | 3.9% | 28.8% | -225,815 |

The v2 validation rule (Neutral bot and Pro-MM positive, Directional bot near zero, Session trader
negative, Retail most negative) holds on Sep 8 and Sep 9. On Aug 30 the directional machines earned
+1.15%, more than the neutral ones, so the rule holds in two days of three. Session traders lose 2.8 to
3.0% per dollar on every day and are the largest single source of the money that the machines and the
makers earn: $182k over three days against $44k from Retail.

## Trailing 30 days, taker side (2026-08-11 to 2026-09-09)

Every taker fill for 30 consecutive days: 54,746 wallets, $225.0M, $7.50M a day. Machines (300+ fills a day,
or 30+ with no 6-hour gap, or both outcomes bought in 40%+ of windows, or a dense share-typed run of 4h+) were
67.5% of taker dollars, between 58% and 73% on every day with no trend, and had positive settlement PnL on
all 30 days; people had negative PnL on all 30. Over the month 31.9% of wallets ended ahead and the median
wallet lost 5.7% of what it traded. Daily series in `results/btc5m_trailing30_daily.csv`.

| Cadence, fills per active day | Wallets | Share of taker $ | Profitable over the month | PnL per $ |
|---|---:|---:|---:|---:|
| Under 10 (Retail) | 31,734 | 3.3% | 31.9% | -4.27% |
| 10 to 100 (systematic) | 20,484 | 34.3% | 30.8% | -1.33% |
| 100 and up (fast) | 2,528 | 62.4% | 41.4% | +1.19% |

| Active days | Wallets | Profitable | Median PnL per $ | Share of $ |
|---|---:|---:|---:|---:|
| 1 | 23,351 | 28.7% | -22.2% | 1.5% |
| 2 to 4 | 17,063 | 30.6% | -6.2% | 6.5% |
| 5 to 9 | 7,046 | 35.1% | -2.0% | 11.0% |
| 10 to 19 | 4,733 | 39.3% | -0.9% | 21.5% |
| 20 or more | 2,553 | 47.9% | -0.1% | 59.5% |

Regulars on 20 or more days are 5% of wallets and 60% of dollars and break even as a group. The 26 wallets
that traded over $1M each are 27% of dollars and 21 of them ended ahead. The top 1% of wallets took 81% of
gross gains. The seven-cohort grid over the same window is being computed from the maker legs and will
replace the three-day tables above.

## Trailing 30 days, both legs: the grid over the full window (2026-08-11 to 2026-09-09)

Every fill, both legs, for 30 consecutive UTC days: 57,300 proxy wallets, $458.4M touched
($15.28M a day, $7.64M single-counted). One cohort per wallet for the whole window, as the
segmentation repo defines it: cadence is fills per active day across the window and maker share is the wallet's
maker touched volume over its total. Settlement PnL is gross of fees (none charged) and LP rewards. Over the
month 30.3% of wallets ended ahead, the median wallet lost 5.6% of what it traded, and the top 1%
of wallets took 82% of gross gains. This section supersedes the one-day and three-day tables above.

| Cohort | Wallets | % touched | % maker side | % taker side | PnL per $ | PnL $, 30 days | Wallets profitable | Median PnL per $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Pro-MM | 1,418 | 38.4% | 69.9% | 5.8% | +0.16% | +282,587 | 28.8% | -1.7% |
| Fast-taker | 2,379 | 21.9% | 3.1% | 41.5% | +0.38% | +377,546 | 37.2% | -0.7% |
| Hybrid-bot | 763 | 21.9% | 19.8% | 24.2% | +0.66% | +663,317 | 29.5% | -1.4% |
| Systematic-taker | 18,301 | 12.4% | 0.8% | 24.4% | -1.58% | -895,313 | 29.1% | -3.2% |
| Mid-MM | 1,478 | 2.6% | 4.7% | 0.3% | -0.04% | -5,208 | 32.5% | -3.1% |
| Systematic-mixed | 2,002 | 1.6% | 1.5% | 1.7% | -1.79% | -132,496 | 31.8% | -2.4% |
| Retail | 30,959 | 1.2% | 0.2% | 2.1% | -5.37% | -290,434 | 30.4% | -20.5% |

| Persona | Wallets | % touched | % maker side | % taker side | PnL $, 30 days | May 2026 venue-wide |
|---|---:|---:|---:|---:|---:|---:|
| MMs (Pro-MM, Mid-MM) | 2,896 | 41.0% | 74.6% | 6.2% | +277,379 | 38.4% |
| Bots and algo | 23,445 | 57.8% | 25.1% | 91.7% | +13,055 | 56.3% |
| Retail | 30,959 | 1.2% | 0.2% | 2.1% | -290,434 | 5.3% |

Pro-MM, Fast-taker and Hybrid-bot together are 82.3% of touched volume (daily range 82% to 88%). Market makers
provide 74.6% of the maker side; bots and algo consume 91.7% of the taker side. Retail is 1.2% of touched volume.
Over the month $1.32M, about $44k a day, moved from Systematic-taker, Systematic-mixed and Retail to Pro-MM,
Fast-taker and Hybrid-bot. Note that Pro-MM wallets are only 29% profitable before LP rewards, with a median
of -1.7% per dollar: a few large makers earn, the rest live on rewards.

The proposed v2 split over the same window (modal daily cohort per wallet):

| v2 cohort | Wallets | % touched | % maker side | % taker side | PnL per $ | PnL $, 30 days | Wallets profitable |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pro-MM | 1,693 | 37.5% | 68.2% | 5.6% | +0.18% | +305,421 | 28.4% |
| Part-time MM | 835 | 2.8% | 4.6% | 1.0% | -0.38% | -49,337 | 34.5% |
| Neutral bot | 2,035 | 22.7% | 12.8% | 33.0% | +1.50% | +1,557,025 | 29.4% |
| Directional bot | 2,327 | 15.6% | 8.1% | 23.3% | +0.12% | +88,002 | 39.8% |
| Session trader | 15,384 | 17.8% | 4.8% | 31.2% | -1.74% | -1,420,280 | 28.1% |
| Retail | 35,026 | 3.7% | 1.5% | 5.9% | -2.86% | -480,830 | 30.7% |

Rollup: MMs 40.3% of touched (+256,084), Machines 38.3% (+1,645,027), People 21.4% (-1,901,110). Neutral machines
earn +1.50% per dollar and took $1.56M; session traders lost $1.42M, three times what Retail lost.
The v2 ordering (Neutral bot and Pro-MM positive, Directional bot near zero, Session trader negative, Retail most
negative) holds over the full window. Result file: `results/btc5m_cohorts30_2026-08-11_09-09.json` (per-month and
per-day tables included).

## Six months, 2026-03-10 to 2026-09-09: the grid over the whole period and month by month

Every trade, both legs, for 184 days: 427,091 wallets, $4,651M traded (both sides counted; $2,325M
single-counted, $12.6M a day). One cohort per wallet for the whole period, following the segmentation
repo's definitions: cadence is fills per active day across the period and maker share is the wallet's maker volume
over its total. Profit and loss is at settlement, before liquidity rewards; no fees were charged on these markets.

Over the period 29% of wallets ended ahead, the typical wallet lost 6.3% of what it traded, the top 1% of
wallets took 86% of all gains and the top 0.1% took 52%. About $104k a day moved from the
cohorts that lose to the cohorts that win.

### Month by month

| Month | Days | Volume per day, $M single-counted | Wallets | Market makers | Bots and active traders | Casual bettors | Bots (v2) | People (v2) | $k per day from people to bots and makers | Wallets profitable in the month |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| March 2026 | 22 | 21.3 | 123,671 | 41% | 57% | 1.3% | 36% | 23% | 190 | 30% |
| April 2026 | 30 | 15.8 | 145,270 | 44% | 54% | 1.8% | 31% | 25% | 136 | 31% |
| May 2026 | 31 | 11.3 | 114,946 | 40% | 59% | 1.5% | 34% | 27% | 47 | 32% |
| June 2026 | 30 | 12.3 | 100,994 | 43% | 56% | 1.4% | 32% | 25% | 104 | 33% |
| July 2026 | 31 | 11.4 | 83,807 | 42% | 57% | 1.1% | 34% | 25% | 79 | 33% |
| August 2026 | 31 | 7.8 | 61,970 | 41% | 58% | 1.2% | 34% | 24% | 57 | 32% |
| September 2026 | 9 | 7.4 | 24,604 | 38% | 60% | 1.4% | 42% | 20% | 69 | 34% |

Bots and market makers (the three fast cohorts) held between 77% and 83% of volume. Casual bettors held between 1.1% and 1.8%.
Volume per day went from 21.3M in March 2026 to 7.4M in September 2026 (range 7.4M to 21.3M). The daily transfer from people to bots and market makers went from 190k in March 2026 to 69k in September 2026 (range 47k to 190k).

### The grid over the whole period

| Who | Wallets | Share of volume | Share of resting orders | Share of aggressive trades | PnL per $ | PnL $, 184 days | Wallets profitable | Median PnL per $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Market makers, full time (Pro-MM) | 6,166 | 38.8% | 68.8% | 7.3% | +0.39% | +7,027,551 | 33.2% | -1.2% |
| Fast bots taking liquidity (Fast-taker) | 16,518 | 20.5% | 3.5% | 38.3% | +0.46% | +4,406,113 | 34.0% | -1.1% |
| Fast bots on both sides (Hybrid-bot) | 6,155 | 19.5% | 19.0% | 20.0% | +0.79% | +7,132,119 | 35.1% | -1.0% |
| Active traders using tools (Systematic-taker) | 146,823 | 14.5% | 1.2% | 28.5% | -2.18% | -14,748,178 | 25.4% | -4.0% |
| Market makers, part time (Mid-MM) | 8,572 | 2.7% | 4.8% | 0.5% | +0.40% | +507,533 | 36.2% | -2.4% |
| Active traders, mixed (Systematic-mixed) | 16,070 | 2.7% | 2.4% | 3.0% | -0.75% | -942,943 | 31.3% | -2.4% |
| Casual bettors (Retail) | 226,787 | 1.2% | 0.2% | 2.3% | -5.84% | -3,364,951 | 29.6% | -19.9% |

| Persona | Wallets | Share of volume | Share of resting orders | Share of aggressive trades | PnL $ | Venue-wide share, May 2026 |
|---|---:|---:|---:|---:|---:|---:|
| Market makers | 14,738 | 41.5% | 73.6% | 7.9% | +7,535,084 | 38.4% |
| Bots and active traders | 185,566 | 57.2% | 26.1% | 89.8% | -4,152,890 | 56.3% |
| Casual bettors | 226,787 | 1.2% | 0.2% | 2.3% | -3,364,951 | 5.3% |

Market makers and fast bots together are 79% of volume. Market makers post 74% of resting orders; bots and
active traders take 90% of aggressive trades. Casual bettors are 1.2% of volume and 53% of wallets.

### The proposed v2 split over the whole period

| Who (v2) | Wallets | Share of volume | Share of resting orders | Share of aggressive trades | PnL per $ | PnL $ | Wallets profitable |
|---|---:|---:|---:|---:|---:|---:|---:|
| Market makers, full time | 6,909 | 37.4% | 65.5% | 8.0% | +0.41% | +7,086,794 | 30.8% |
| Market makers, part time | 4,871 | 4.1% | 6.8% | 1.3% | +0.49% | +944,817 | 37.1% |
| Bots trading both sides | 13,323 | 18.1% | 10.4% | 26.2% | +1.13% | +9,472,900 | 26.4% |
| Bots betting a direction | 14,514 | 13.9% | 7.1% | 21.1% | +0.02% | +153,583 | 35.4% |
| Active traders using tools | 120,886 | 19.7% | 6.3% | 33.8% | -1.20% | -10,978,920 | 25.2% |
| Casual bettors | 266,588 | 6.7% | 4.0% | 9.6% | -2.13% | -6,661,932 | 29.8% |

Rollup: market makers 41.6% of volume (+8,031,611), bots 32.0% (+9,626,484), people 26.4% (-17,640,853).

The v2 label over a long window is the wallet's most common daily class, so a wallet that ran as a bot on its busy
days but traded by hand on most days is counted as a person for the whole period, and its bot-day volume goes with
it. That is why bots read lower and people higher here than in any single month; the month-by-month table above is
the better read for the v2 split, and the v1 grid (cadence per active day, maker share over the window) does not
have this problem.

### Who is still standing after six months

| Active days in the period | Wallets | Share of volume | Wallets profitable | Median PnL per $ |
|---|---:|---:|---:|---:|
| 1 day | 167,025 | 1.0% | 28.5% | -23.0% |
| 2 to 4 days | 137,247 | 3.4% | 25.6% | -8.1% |
| 5 to 9 days | 56,673 | 5.3% | 29.7% | -3.2% |
| 10 to 19 days | 33,423 | 10.5% | 32.5% | -1.8% |
| 20 or more days | 32,723 | 79.7% | 36.9% | -0.8% |

Result file with per-month, per-day and persistence tables: `results/btc5m_cohorts_6m_2026-03-10_09-09.json`.

## What this changes in the May reading

- The "structural retail-flow floor" worry is answered for this product: the uninformed flow is the
  Systematic-taker cohort, 11% of touched and 21% of the taker side, losing 2% per dollar. Counting it,
  uninformed flow is about 17% of touched volume and 29% of the taker side.
- "Bots + Algo" is a volume persona, not an economic one. For economics, split it into machines that earn
  (neutral, high cadence) and people with tools who pay (session traders).
- Next: owner aggregation through Dune and a 30-day modal cohort assignment.
