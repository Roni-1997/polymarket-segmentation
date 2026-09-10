# BTC 5m up/down in the seven-cohort grid, with PnL by cohort (September 2026)

Update to the May 2026 segmentation. Same grid (maker share of touched volume by fills per active day),
applied to every fill on Polymarket's BTC 5-minute up/down markets on 2026-09-09 UTC, both legs, with the
question the May work left open answered: who makes money and who pays.

## The claim

**Retail is not the flow, and the retail narrative should be retired.** Strict retail, under 10 fills per
active day, is 1.3% of BTC 5m touched volume here and was 5.3% venue-wide in May. Nothing about these
venues' volume, depth or growth is explained by casual clickers.

**Flow needs machines.** Market makers and fast machines (Pro-MM, Fast-taker, Hybrid-bot) are 85% of BTC
5m touched volume. Market makers provide 73% of the maker side and bots and algo consume 94% of the taker side. They arrive within days of a product launching (the 5m product
carried 46% machine share on its second day) and they are the book. A venue without them has nothing to
trade against and no depth to show.

**Machines need someone to pay them.** Settlement PnL is zero-sum across both legs. Over three measured
days about $41k a day moved from Systematic-taker and Retail to Pro-MM and Fast-taker ($49k on Sep 9). The payers are not the retail cohort, which is
too small to matter; they are the Systematic-taker cohort, tool-assisted people trading 10 to 300 fills a
day who sleep, size in dollars and lose about 2% per dollar. Machine volume tracks that supply: in an
internal taker-only series from February to September 2026, bot dollars fell 43% when new wallets fell
80%. The design target for a venue is therefore machines plus a steady supply of session traders, arriving
through frontends, brokers and partner apps, not a consumer funnel of casual clickers.

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

## The grid on 2026-09-09

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

## Three days: Aug 30, Sep 8 and Sep 9, 2026

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

## What this changes in the May reading

- The "structural retail-flow floor" worry is answered for this product: the uninformed flow is the
  Systematic-taker cohort, 11% of touched and 21% of the taker side, losing 2% per dollar. Counting it,
  uninformed flow is about 17% of touched volume and 29% of the taker side.
- "Bots + Algo" is a volume persona, not an economic one. For economics, split it into machines that earn
  (neutral, high cadence) and people with tools who pay (session traders).
- Next: owner aggregation through Dune and a 30-day modal cohort assignment.
