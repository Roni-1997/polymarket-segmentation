# Findings — Polymarket participant segmentation

Status: **audit-adjusted methodology AND rerun completed**.
Data window: trailing 30 days (April 27 – May 27, 2026).
Quarterly comparison: Q4 2025 and Q1 2026.

The original exported CSVs had two audit issues that have now been fixed
in the SQL and the queries re-executed against Dune:

1. The cohort queries counted **touched volume** (each fill once on the
   maker side + once on the taker side). Correct for participant-share
   analysis, but 2× single-counted venue notional. Output now carries
   both columns explicitly.
2. Known router/system contracts were filtered as raw maker/taker
   addresses, but not after `users_address_lookup` mapped proxy wallets
   to owners. Now filtered at both stages.
3. LP rewards UNIONed merkle claims with direct USDC transfers, which
   double-counted: merkle claims trigger a USDC transfer in the same tx.
   Direct transfers are now deduped against merkle claims by `evt_tx_hash`.

---

## Headline numbers (the 60-second read)

Everything below is sliced six different ways. If you only have a minute,
read this:

- **Real volume:** ~$102M/day single-counted notional (half the headline
  $200M/day figure — Paradigm OrderFilled double-counting).
- **Who drives volume (T30d):** **MMs 38% / Bots+Algo 56% / Retail 5%.**
  Sums to **94.7% professional/systematic, 5.3% retail.**
- **Headcount asymmetry:** ~327,000 professional/systematic owners
  generate the 94.7%. ~926,000 true-retail owners generate the 5.3%.
  Polymarket is retail by *headcount*, professional by *dollars*.
- **Where the dollars are by category:** Other/null-tagged is 36%;
  among tagged categories, Sports 30% > Politics 16% > Crypto 9%.
  (The "Polymarket = politics" narrative is wrong.)
- **Who plays where:** Politics is the most retail-heavy major
  category at 13% retail. Crypto is the most bot-dominated (96%
  MMs+Bots+Algo). Sports is bot-dominated and mature.
- **The retail collapse:** Retail share dropped from **10.7% (Q4 2025)
  → 7.7% (Q1 2026) → 5.3% (T30d May 2026)**. Halved in 6 months.
  Far below the ~20% structural floor for healthy uninformed flow.
- **LP rewards concentration:** Top 10 owners = 30% of all rewards.
  Top 50 = 50%. Long tail of 111,000+ owners captures the remaining 40%.
- **Overlay tags (T30d, top-100 venue-wide):** 32/100 LP-confirmed
  (≥$1k all-time), 16/100 complete-set arbers, 48/100 large-ticket
  whales, 0/100 active on Hyperliquid HIP-4.
- **Cross-venue migration:** **0 of the 100 venue-wide top wallets**
  (by 30d touched volume) are active on HIP-4. The venue-wide top-100
  is 94% professional (50 Pro-MM + 23 Fast-taker + 21 Hybrid-bot) and
  only 6% non-professional (3 Systematic-taker + 3 Mid-MM, 0 Retail).
  Migration visible so far runs HL-perps → HIP-4, NOT Polymarket → HIP-4.

---

## Audited numbers (trailing 30 days, May 2026), 7-cohort framework

### Cohort distribution by single-counted notional ($M)

| Cohort | Touched $M | Single-counted $M | % of touched |
|---|---:|---:|---:|
| **Pro-MM** (highMkr_fast) | 1,904 | **952** | **31.0%** |
| **Fast-taker** (lowMkr_fast) | 1,261 | 631 | 20.5% |
| **Hybrid-bot** (midMkr_fast) | 1,096 | 548 | 17.9% |
| **Systematic-taker** (lowMkr_systematic) | 782 | 391 | 12.7% |
| **Mid-MM** (highMkr_systematic) | 454 | 227 | 7.4% |
| **Retail** (any maker, <10 fills/active_day) | 323 | 162 | **5.3%** |
| **Systematic-mixed** (midMkr_systematic) | 321 | 160 | 5.2% |
| **Total** | **6,141** | **3,071** | 100% |

Real volume: **~$102M/day single-counted notional** over the trailing
30 days. Matches Paradigm's December 2025 finding that Polymarket's
~$200M/day headline number is ~2× overstated via OrderFilled
double-counting.

### Collapsed three-persona view

| Persona | Cohorts | % of touched |
|---|---|---:|
| **MMs** | Pro-MM + Mid-MM | **38.4%** |
| **Bots + Algo** | Hybrid-bot + Fast-taker + Systematic-mixed + Systematic-taker | **56.3%** |
| **Retail** | Retail | **5.3%** |

### Cohort distribution by quarter (% of touched volume)

| Cohort | Q4 2025 | Q1 2026 | T30d (May 2026) |
|---|---:|---:|---:|
| Pro-MM | 23.2% | 29.1% | 31.0% |
| Fast-taker | 11.5% | 17.1% | 20.5% |
| Hybrid-bot | 22.8% | 22.0% | 17.9% |
| Systematic-taker | 12.7% | 12.0% | 12.7% |
| Mid-MM | 7.4% | 5.1% | 7.4% |
| Systematic-mixed | 11.6% | 7.0% | 5.2% |
| **Retail** | **10.7%** | **7.7%** | **5.3%** |

**Retail share halved in 6 months under the strict definition.** This
is the sharpest professionalization signal in the data.

### Volume in dollars (single-counted)

| Period | $B / qtr (single-counted) | $M / day |
|---|---:|---:|
| Q4 2025 | 5.2 | 57 |
| Q1 2026 | 11.1 | **123** |
| T30d (May 2026) | 3.1 | **102** |

Q1 2026 was a 2× volume spike vs Q4 2025; T30d sits ~83% of the Q1
peak. Likely drivers: NCAA + crypto rally + post-inauguration markets.

### Wallet counts (Q1 2026 — 90d stable reference)

| Cohort | Distinct owners |
|---|---:|
| Pro-MM | 8,095 |
| Mid-MM | 21,541 |
| Hybrid-bot | 11,603 |
| Systematic-mixed | 45,833 |
| Fast-taker | 40,910 |
| Systematic-taker | 199,448 |
| **Retail** | **926,087** |
| **Total** | ~1.25M |

**Professional + systematic owners: ~327,000.** They generate ~92.3%
of dollars. Retail owners: ~926,087. They generate ~7.7%.

---

## Category breakdown — where the dollars actually go

The "Polymarket is a politics venue" narrative is outdated. Politics is
only 16% of platform volume. Among tagged categories, sports is nearly
2× larger. The largest bucket overall is still "other" / null-tagged.

### Categories ranked by size (single-counted notional, 30d)

| Category | $M / 30d | % of platform | $M / day | Texture |
|---|---:|---:|---:|---|
| Other (null-tagged) | 1,100 | **35.8%** | 37 | Mostly recurring crypto/sports markets that lost their tags somewhere |
| Sports | 906 | **29.5%** | 30 | NBA + NFL + esports (Dota, CS2, LoL, Valorant) + soccer |
| Politics | 492 | 16.0% | 16 | Trump, elections, geopolitical politics |
| Crypto | 290 | 9.4% | 10 | 5m / 15m / 1h Up-or-Down recurring binaries |
| Geopolitics | 163 | 5.3% | 5.4 | Iran, Ukraine, Russia, world affairs, Gaza |
| Finance | 41 | 1.3% | 1.4 | Fed, inflation, interest rates, oil |
| Weather | 40 | 1.3% | 1.3 | (newer category) |
| Culture | 33 | 1.1% | 1.1 | Awards, MrBeast, movies, music, celebrities |
| Tech | 5 | 0.2% | 0.2 | AI, science, tech outcomes |
| **Total** | **3,071** | 100% | **~$102M/day** | |

### Crypto tagging shifted between Q1 and May 2026 — caveat

Comparing T30d (May) to Q1 2026 (Jan–Mar) reveals a data-quality flag:

| Category | Q1 2026 ($M/day single) | T30d May 2026 ($M/day single) | Δ |
|---|---:|---:|---|
| Crypto | $37.8 | $9.7 | **−74%** |
| Other (null-tagged) | $0.5 | $36.7 | **+73×** |
| Crypto + Other combined | $38.3 | $46.4 | +21% |

The 74% crypto crash is implausible against a stable platform total
(Q1 $123M/day → T30d $102M/day, −17%). The real cause is **Polymarket
re-tagging or untagging the recurring 5m/15m/1h crypto binaries**
between Q1 and May. They moved from being tagged `Crypto` to being
null-tagged `Other`.

**Implication for citing the T30d category breakdown:** the May 2026
"Other = 35.8%" bucket is *mostly de-tagged crypto*, not a true
miscellaneous residual. Treat "Crypto + Other" as the upper bound on
crypto's real share (~45% of platform in May). The Q1 2026 numbers
better reflect the underlying market types (Crypto 30.7%, Other 0.4%).

### Q1 2026 crypto cohort breakdown (90d window, $M)

| Cohort | Touched $M | Single $M | % of crypto | T30d for ref |
|---|---:|---:|---:|---:|
| Pro-MM | 2,074 | 1,037 | **30.5%** | 31.7% |
| Hybrid-bot | 1,634 | 817 | 24.0% | 17.4% |
| Fast-taker | 1,611 | 806 | 23.7% | 26.0% |
| Systematic-taker | 549 | 275 | 8.1% | 10.5% |
| Retail | 461 | 231 | **6.8%** | 5.0% |
| Mid-MM | 248 | 124 | 3.7% | 5.8% |
| Systematic-mixed | 227 | 113 | 3.3% | 3.6% |
| **Total** | **6,805** | **3,402** | 100% | $290M T30d |

3-persona collapse (Q1 2026 crypto):
**MMs 34% / Bots+Algo 59% / Retail 7%.** Stable vs T30d (38/58/5).
Crypto has been consistently bot-dominated across both windows.

### Who plays in each category — three views

The "Polymarket cohort share by category" is actually three different
questions, each with a different answer. Maker side and taker side
behave very differently for the same cohort.

#### View 1 — Who PROVIDES depth in each category (% of maker side)

This is who's posting limit orders that other people fill. Every fill
has one maker, so columns sum to 100%.

| Category | Pro-MM | Mid-MM | Hybrid-bot | Systematic-mixed | Fast-taker | Systematic-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Sports** | **58%** | 9% | 22% | 5% | 4% | 1% | 1% |
| **Politics** | **46%** | **26%** | 10% | 8% | 2% | 2% | 7% |
| **Crypto** | **59%** | 10% | 19% | 4% | 4% | 1% | 4% |
| **Finance** | **38%** | **23%** | 13% | 12% | 3% | 3% | 8% |
| **Geopolitics** | **59%** | **23%** | 5% | 5% | 1% | 1% | 6% |
| **Culture** | **43%** | 19% | 15% | 13% | 2% | 2% | 6% |
| **Weather** | **59%** | 17% | 12% | 7% | 3% | 2% | 1% |
| **Tech** | **44%** | 19% | 12% | 9% | 3% | 3% | 10% |
| **Other** | **59%** | 9% | 21% | 4% | 4% | 1% | 1% |

**Pro-MM provides 38–59% of depth in every single category.** Mid-MM
is the consistent #2 (9–26%). Together MMs are **65–82% of all
maker-side flow across categories.** Hybrid-bot adds another 5–22%.
Retail provides 1–10% of depth — mostly via Politics/Finance/Tech
where humans use limit orders to express directional views.

#### View 2 — Who CONSUMES depth in each category (% of taker side)

This is who's hitting other people's orders. Columns sum to 100%.

| Category | Pro-MM | Mid-MM | Hybrid-bot | Systematic-mixed | Fast-taker | Systematic-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Sports** | 8% | 2% | 21% | 5% | **38%** | 22% | 4% |
| **Politics** | 4% | 3% | 10% | 8% | 22% | **35%** | **19%** |
| **Crypto** | 5% | 1% | 16% | 4% | **49%** | 20% | 6% |
| **Finance** | 4% | 4% | 14% | 12% | 21% | **35%** | 11% |
| **Geopolitics** | 5% | 3% | 6% | 6% | 34% | **29%** | **19%** |
| **Culture** | 6% | 3% | 14% | 9% | 16% | **37%** | **16%** |
| **Weather** | 7% | 2% | 9% | 6% | 33% | **35%** | 8% |
| **Tech** | 4% | 3% | 15% | 10% | 20% | **33%** | **16%** |
| **Other** | 6% | 1% | 21% | 4% | **44%** | 20% | 4% |

**The taker side is dominated by Fast-taker and Systematic-taker.**
Combined they consume 57–69% of taker flow in every category. Retail
takers are 4–19% — meaningfully present in slow-resolving categories
(politics, geopol, culture, tech) but small everywhere else.

#### View 3 — Combined participation (3-persona, % of touched)

| Category | MMs (Pro+Mid) | Bots+Algo (Hybrid+Fast+Sys-mixed+Sys-taker) | Retail |
|---|---:|---:|---:|
| **Sports** | 38% | **59%** | 2.7% |
| **Politics** | 39% | 48% | **13.0%** |
| **Crypto** | 38% | **58%** | 5.0% |
| **Finance** | 34% | **56%** | 9.7% |
| **Geopolitics** | **45%** | 43% | 12.7% |
| **Weather** | 42% | **53%** | 4.6% |
| **Culture** | 36% | **54%** | 10.8% |
| **Tech** | 35% | **53%** | 12.7% |
| **Other** | 38% | **60%** | 2.5% |
| **Platform avg** | **38%** | **56%** | **5%** |

#### Key insight from separating maker / taker / combined

**The roles are crystal clear when you split sides (T30d totals):**

- **MMs (Pro + Mid) provide 69% of maker side, consume 8% of taker side.** They're the liquidity-provider pillar.
- **Bots + Algo (Hybrid + Fast-taker + Systematic-mixed + Systematic-taker) provide 28% of maker side, consume 85% of taker side.** They're the dominant consumers of liquidity.
- **Retail provides 3% of maker side, consumes 8% of taker side.**
  Structurally small on both ends.

The aggregate "touched" view conflates these roles. MMs make. Bots and
Algo take. Retail provides a thin slice of both.

**The uninformed-flow problem:** With Retail at only 5–13% of taker
flow across categories, MMs are increasingly trading against other
machines. The Systematic-taker cohort may function as a quasi-retail
substitute (slow algos behave somewhat uninformed at intra-day scale),
but if that cohort thins further, MMs will start losing to Fast-taker
in an adverse-selection contest.

### Wallet counts and trade-size signals per cell

Full per-cell data in
[`results/cohort_x_category_drilldown_30d.csv`](../results/cohort_x_category_drilldown_30d.csv).
Standout cells:

| Cohort | Category | Wallets (T30d) | Avg trade size | Reads as |
|---|---|---:|---:|---|
| Pro-MM | Crypto | ~2,800 | **$7** | Tiny recurring binaries fired millions of times |
| Pro-MM | Geopolitics | ~500 | **$415** | Chunky positions on Iran/Ukraine; few firms, big bets |
| Systematic-taker | Politics | ~85k | **$70** | Slow algos / tool-assisted humans taking politics |
| Retail | Politics | ~120k | **~$80** | True retail bettors on politics (now in collapsed cohort) |
| Fast-taker | Crypto | ~10k | $7 | Pure-take bots picking off stale 5m binary quotes |
| Hybrid-bot | Sports | ~5k | $80 | Basket arbers on NBA/NFL/esports multi-outcome markets |
| Mid-MM | Geopolitics | ~7k | **$550** | Mid-tier MMs sitting on chunky geopolitical bets |

## LP rewards — major correction

The pre-audit doc said "top 100 wallets capture 100% of rewards" — that
was an artifact of fetching only the top 50 from a paginated result.
After deduping merkle claims against direct USDC transfers and
aggregating to owner level, the actual picture is:

| Top N (owners) | $ rewards | % of all rewards |
|---|---:|---:|
| 3 | $4.24M | **20.1%** |
| 10 | $6.42M | **30.3%** |
| 20 | $8.12M | 38.4% |
| 50 | $10.60M | 50.1% |
| 100 | $12.57M | 59.4% |
| **All (111,217 owners)** | **$21.16M** | 100% |

**Pre-audit said top 10 = 51%; audited says 30.3%.** Pre-audit said
top 100 = 100%; audited says 59.4%, with a 40% long tail across
~111,000 reward-earning wallets.

The Tier-1 oligopoly is real — top 3 captured $4.24M (20%) — but
much more diluted by a long tail than the original analysis suggested.

Top 3 owners by all-time LP rewards (deduped):
- `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb` — $2.43M
- `0x9d84ce0306f8551e02efef1680475fc0f1dc1344` — $1.27M
- `0x96bde0dd1d5ba5cc8e1c74cdec14041564a1363a` — $545k

---

## What remains robust

The directional market-structure conclusion is still supported:

- Polymarket is not primarily a one-off retail venue. A large share of
  activity comes from maker-heavy wallets, high-cadence takers, and
  hybrid maker/taker strategies.
- Participant segmentation should be measured at the **owner** level, not
  proxy-wallet level.
- MMs can and do take liquidity. The right metric is therefore segment
  share of maker+taker touched volume, not maker-side volume alone.
- LP rewards are useful ground truth for MM participation, but only after
  deduping merkle claims vs direct transfers and ignoring dust rewards as
  weak identity evidence.
- Crypto/short-duration markets should be expected to skew more automated
  than politics or slower event markets.

---

## Counting convention

Use two separate denominators:

| Metric | Definition | Use |
|---|---|---|
| Single-counted notional | One row per fill from `market_trades.amount` | Venue volume, dollars/day, comparison to public volume numbers |
| Touched volume | Maker-side amount + taker-side amount | Participant share, because both counterparties participated |

If `04_cohort_x_category_30d.sql` reports `total_touched_musd = 6,000`,
the equivalent single-counted venue notional is `3,000` million. Cohort
shares from touched volume are still meaningful because all fills have two
sides; absolute dollar-volume claims must use the single-counted column.

---

## Where to find each result

Each cited number above maps to a specific CSV under `results/`:

1. Trailing-30d cohort × category — `results/cohort_x_category_30d_clean.csv`
   from `queries/04_cohort_x_category_30d.sql`.
2. Quarterly trend — `results/cohort_q1_2026.csv` and
   `results/cohort_q4_2025.csv` from `queries/06_cohort_per_quarter.sql`
   (run twice with different date windows).
3. Wallet-level validation — `results/top20_per_cohort_30d.csv` from
   `queries/05_top20_per_cohort_with_lp.sql`. This exported CSV is
   clipped at 100 rows, so it is a top-per-cohort validation sample, not
   the full 140-row query output. Use `lp_rewards_confirmed_1k` as the
   strong signal, not `lp_rewards_observed`.
4. LP rewards concentration — `results/lp_rewards_concentration.csv`
   from `queries/08_lp_rewards_concentration.sql`.
5. Cohort × category drill-down (wallet counts, fills, avg trade size
   per cell) — `results/cohort_x_category_drilldown_30d.csv` from
   `queries/09_cohort_x_category_drilldown.sql`.
6. Cohort × category maker / taker split (who provides depth vs who
   consumes it, per cell) — `results/cohort_x_category_maker_taker_30d.csv`
   from `queries/10_cohort_x_category_maker_taker.sql`.
7. True venue-wide top-wallet sample —
   `results/top100_wallets_venue_wide_30d.csv` from
   `queries/11_top_wallets_30d_with_lp.sql`.
