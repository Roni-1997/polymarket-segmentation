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

- **Real volume:** ~$103M/day single-counted notional (half the headline
  $200M/day figure — Paradigm OrderFilled double-counting).
- **Who drives volume:** **MMs 40% / Bots 38% / Retail 22%.** Sums to
  78% professional, 22% retail.
- **Headcount asymmetry:** ~221,000 MM/bot-classified owners generate
  the 78%. ~1,030,000 retail-tier owners generate the 22%. The three
  fast professional cohorts alone are ~60,600 owners and generate ~69%.
  Polymarket is retail by *headcount*, professional by *dollars*.
- **Where the dollars are by category:** Other/null-tagged is 35%;
  among tagged categories, Sports 30% > Politics 16% > Crypto 10%.
  (The "Polymarket = politics" narrative is wrong.)
- **Who plays where:** Politics is most retail-heavy (37% human).
  Crypto is most bot-dominated (77% MM+Bot, only 17% human). Sports is
  bot-dominated and mature.
- **The trend:** Retail share dropped 33% → 22% in 6 months. Polymarket
  is professionalizing rapidly.
- **LP rewards concentration:** Top 10 owners = 30% of all rewards.
  Top 50 = 50%. Long tail of 111,000+ owners captures the remaining 40%.
- **Cross-venue migration:** **0 of the 100 venue-wide top wallets**
  (by 30d touched volume — query 11) are active on Hyperliquid HIP-4.
  Confirmed against the HIP-4 top-127 sample in
  [hip4_cross_venue/](../hip4_cross_venue/). Migration visible so far
  runs HL-perps → HIP-4, NOT Polymarket → HIP-4. The venue-wide
  top-100 is 94% professional cohorts (51 Pro-MM + 23 HFT-taker +
  20 Hybrid-bot) and 6% human (3 Active-retail + 3 Mid-MM).

Verdict-relevant one-liner: **Build for machines first (crypto + finance
markets). Recruit Hyperliquid-native MMs, not Polymarket veterans. Open
retail UX in month 3-9 once depth exists. Skip sports, skip politics,
skip Polymarket migration plays.**

---

## Audited numbers (trailing 30 days, May 2026)

### Cohort distribution by single-counted notional ($M)

| Cohort | Touched $M | Single-counted $M | % of touched |
|---|---:|---:|---:|
| Pro-MM (highMkr_fast) | 1,950 | **975** | **31.4%** |
| HFT-taker (lowMkr_fast) | 1,269 | 635 | 20.5% |
| Hybrid-bot (midMkr_fast) | 1,079 | 539 | 17.4% |
| Active-retail (lowMkr_med) | 1,008 | 504 | 16.2% |
| Mid-MM (highMkr_med) | 527 | 263 | 8.5% |
| Active-mixed (midMkr_med) | 374 | 187 | 6.0% |
| **Total** | **6,206** | **3,103** | 100% |

Real volume: **~$103M/day single-counted notional** over the trailing
30 days. This matches Paradigm's December 2025 finding that Polymarket's
~$200M/day headline number is ~2× overstated via OrderFilled
double-counting.

Note: the pre-audit version of this doc stated $210M/day, which was
touched volume mislabeled as notional. The corrected number is half
that.

### Collapsed three-bucket view

| Bucket | % of touched |
|---|---:|
| **MMs** (Pro + Mid) | **39.9%** |
| **Bots** (HFT + Hybrid) | **37.9%** |
| **Retail** (Active-retail + Active-mixed) | **22.2%** |

### Cohort distribution by quarter (% of touched volume)

| Cohort | Q4 2025 | Q1 2026 | T30d |
|---|---:|---:|---:|
| Pro-MM | 23.2% | 29.1% | 31.4% |
| HFT-taker | 11.5% | 17.1% | 20.5% |
| Hybrid-bot | 22.8% | 22.0% | 17.4% |
| Mid-MM | 9.7% | 6.6% | 8.5% |
| Active-retail | 18.0% | 15.2% | 16.2% |
| Active-mixed | 14.7% | 10.0% | 6.0% |

Collapsed retail share: 33% → 25% → 22%. Direction holds; magnitudes
unchanged from pre-audit because the cohort-level fixes were tiny.

### Volume in dollars (single-counted)

| Period | $B / qtr (single-counted) | $M / day |
|---|---:|---:|
| Q4 2025 | 5.2 | 57 |
| Q1 2026 | 11.1 | 123 |
| T30d (May 2026) | 3.1 | **103** |

Q1 2026 was a 2× volume spike vs Q4 2025; T30d sits ~85% of the Q1
peak. Likely drivers: NCAA + crypto rally + post-inauguration markets.

---

## Category breakdown — where the dollars actually go

The "Polymarket is a politics venue" narrative is outdated. Politics is
only 16% of platform volume. Among tagged categories, sports is nearly
2× larger. The largest bucket overall is still "other" / null-tagged.

### Categories ranked by size (single-counted notional, 30d)

| Category | $M / 30d | % of platform | $M / day | Texture |
|---|---:|---:|---:|---|
| Other (null-tagged) | 1,100 | **35.4%** | 37 | Mostly recurring crypto/sports markets that lost their tags somewhere |
| Sports | 921 | **29.7%** | 31 | NBA + NFL + esports (Dota, CS2, LoL, Valorant) + soccer |
| Politics | 500 | 16.1% | 17 | Trump, elections, geopolitical politics |
| Crypto | 297 | 9.6% | 10 | 5m / 15m / 1h Up-or-Down recurring binaries |
| Geopolitics | 165 | 5.3% | 5.5 | Iran, Ukraine, Russia, world affairs, Gaza |
| Finance | 42 | 1.3% | 1.4 | Fed, inflation, interest rates, oil |
| Weather | 41 | 1.3% | 1.4 | (newer category) |
| Culture | 33 | 1.1% | 1.1 | Awards, MrBeast, movies, music, celebrities |
| Tech | 5 | 0.2% | 0.2 | AI, science, tech outcomes |
| **Total** | **3,103** | 100% | $103M/day | |

### Who plays in each category — three views

The "Polymarket cohort share by category" is actually three different
questions, each with a different answer. Maker side and taker side
behave very differently for the same cohort.

#### View 1 — Who PROVIDES depth in each category (% of maker side)

This is who's posting limit orders that other people fill. Every fill
has one maker, so columns sum to 100%.

| Category | Pro-MM | Mid-MM | Hybrid-bot | Active-mixed | HFT-taker | Active-retail |
|---|---:|---:|---:|---:|---:|---:|
| **Sports** | **58%** | 10% | 22% | 5% | 4% | 2% |
| **Politics** | **46%** | **31%** | 10% | 10% | 2% | 2% |
| **Crypto** | **59%** | 14% | 19% | 4% | 4% | 1% |
| **Finance** | **38%** | **29%** | 13% | 14% | 3% | 4% |
| **Geopolitics** | **59%** | **28%** | 5% | 6% | 1% | 1% |
| **Culture** | **43%** | 24% | 15% | 14% | 2% | 3% |
| **Weather** | **59%** | 18% | 12% | 7% | 2% | 2% |
| **Tech** | 43% | 25% | 13% | 12% | 3% | 4% |
| **Other** | **59%** | 10% | 21% | 5% | 4% | 2% |

**Pro-MM provides 38–59% of depth in every single category.** Mid-MM is
the consistent #2 (10–31%). Together MMs are **66–87% of all maker-side
flow across categories.** Hybrid-bot adds another 5–22%. Active-retail
alone provides only 1–4% of depth; Active-mixed wallets post more, but
they are still secondary to the MM cohorts.

#### View 2 — Who CONSUMES depth in each category (% of taker side)

This is who's hitting other people's orders. Columns sum to 100%.

| Category | Pro-MM | Mid-MM | Hybrid-bot | Active-mixed | HFT-taker | Active-retail |
|---|---:|---:|---:|---:|---:|---:|
| **Sports** | 8% | 2% | 21% | 5% | **39%** | 26% |
| **Politics** | 4% | 3% | 10% | 10% | 22% | **51%** |
| **Crypto** | 5% | 2% | 16% | 4% | **49%** | 25% |
| **Finance** | 4% | 4% | 14% | 13% | 21% | **44%** |
| **Geopolitics** | 5% | 3% | 6% | 7% | 34% | **46%** |
| **Culture** | 6% | 4% | 14% | 10% | 16% | **51%** |
| **Weather** | 7% | 2% | 9% | 6% | 33% | **42%** |
| **Tech** | 4% | 4% | 15% | 12% | 20% | **46%** |
| **Other** | 6% | 1% | 21% | 5% | **44%** | 24% |

**The taker side flips entirely.** Active-retail consumes 24–51% of
liquidity across categories — they're the dominant takers in politics,
culture, geopolitics, finance, tech, weather. HFT-taker dominates the
fast markets (crypto 49%, sports 39%, "other" 44%). Pro-MM consumes
only 4–8% — they almost never take.

#### View 3 — Combined participation (% of touched volume)

This is the aggregate of maker + taker, useful for "how often is each
cohort involved in trades in this category." This is what the original
cohort × category headline matrix shows.

| Category | MMs (Pro+Mid) | Bots (Hybrid+HFT) | Retail (Active+Mixed) |
|---|---:|---:|---:|
| **Sports** | 40% | **41%** | 19% |
| **Politics** | 42% | 22% | **37%** |
| **Crypto** | 39% | **43%** | 17% |
| **Finance** | 37% | 25% | **38%** |
| **Geopolitics** | **47%** | 22% | 31% |
| **Weather** | **43%** | 28% | 29% |
| **Culture** | 38% | 22% | **39%** |
| **Tech** | 38% | 24% | **37%** |
| **Other** | 38% | **44%** | 17% |
| **Platform avg** | **40%** | **38%** | **22%** |

#### Key insight from separating maker / taker / combined

**The roles are crystal clear when you split sides:**
- **MMs = liquidity providers.** 66–87% of maker-side flow across categories, only 6–11% of taker flow.
- **HFT + Active-retail = flow consumers.** Together they take 65–80% of liquidity per category, but provide only 2–7% of depth.
- **Hybrid bots are the only cohort with roughly balanced maker/taker
  behavior.** They are not consistently maker-dominated like MMs or
  taker-dominated like HFT/retail.

The aggregate "touched" view conflates these roles, which is why the
platform-average (40% MM / 38% Bot / 22% Retail) is misleading on its
own — it makes it sound like MMs, bots, and retail all "do similar
things at different volumes." They don't. MMs make. HFT and retail
take. Hybrid bots straddle.

**The strategic read for Verdict:**

When you recruit MMs, you're recruiting the source of 66–87% of
maker-side flow in every category. There's no substitute on the maker
side except your internal vault. When you acquire retail, you're
acquiring the largest single source of taker flow (24–51%) — they
provide the uninformed counterparty MMs need to earn the spread. The
bots will self-arrive once spread exists. Hybrid bots provide meaningful
depth in some categories (5–22% of maker-side flow); HFT-taker wallets
mostly consume liquidity.

### Who plays in each category — full detail (6 cohorts, combined)

| Category | Pro-MM (Quoter) | Mid-MM (Quoter) | Hybrid-bot (Sniper) | HFT-taker (Sniper) | Active-retail (Human) | Active-mixed (Human) |
|---|---:|---:|---:|---:|---:|---:|
| **Sports** | **34%** | 6% | 20% | 21% | 14% | 5% |
| **Politics** | 25% | 17% | 10% | 12% | **27%** | 10% |
| **Crypto** | 32% | 8% | 17% | **26%** | 13% | 4% |
| **Finance** | 21% | 16% | 13% | 11% | **24%** | 14% |
| **Geopolitics** | 32% | 15% | 5% | 17% | **24%** | 7% |
| **Culture** | 25% | 14% | 14% | 9% | **27%** | 13% |
| **Other** | 33% | 6% | 21% | 24% | 13% | 5% |

### Headline read on each category

| Category | Headline | Implication for Verdict |
|---|---|---|
| **Sports** | Bot-dominated: 75% machines (Pro-MM 34% + Snipers 41%) | Polymarket sports MM is mature. Hard to break in. Skip. |
| **Politics** | Most retail-heavy: 37% human cohorts; Active-retail alone is the largest single cohort here | Polymarket owns the brand. Politics is declining (16% → falling). Don't lead. |
| **Crypto** | Most automated: 76% bots (Pro-MM + HFT + Hybrid). Only ~17% human | **Verdict's natural target.** Build for machines first. |
| **Finance** | Balanced: ~45% bot, ~38% human, ~16% Mid-MM | Has sophisticated retail + Mid-MM both present. Verdict can compete here. |
| **Geopolitics** | Pro-MM heavy + chunky human bets | Average trade $400-$550. Niche but lucrative. Subjective settlement risk. |
| **Culture / Tech / Weather** | Tiny categories, retail-heavy | Distraction. Skip in launch. |

### Wallet counts and trade-size signals per cell

Full per-cell data in
[`results/cohort_x_category_drilldown_30d.csv`](../results/cohort_x_category_drilldown_30d.csv).
Standout cells:

| Cohort | Category | Wallets | Avg trade size | Reads as |
|---|---|---:|---:|---|
| Pro-MM | Crypto | 2,871 | **$7** | Tiny recurring binaries fired 27M times in 30d |
| Pro-MM | Geopolitics | 498 | **$415** | Chunky positions on Iran/Ukraine; few firms, big bets |
| Active-retail | Politics | 167,082 | **$110** | Retail puts real money behind political bets |
| Active-retail | Sports | 163,305 | $57 | Similar wallet count, smaller per-bet stakes |
| Active-retail | Other (recurring crypto) | 200,847 | $25 | Most retail wallets dabble in recurring crypto at small stakes |
| HFT-taker | Crypto | 9,924 | $7 | Pure-take bots picking off stale 5m binary quotes |
| Hybrid-bot | Sports | 4,915 | $80 | Basket arbers on NBA/NFL/esports multi-outcome markets |
| Mid-MM | Geopolitics | 7,355 | **$552** | Mid-tier MMs sitting on chunky geopolitical bets |

### Strategic category focus for Verdict (HIP-4 crypto + financial outcome markets)

| Focus | Category | Why |
|---|---|---|
| ✓ Lead | **Crypto outcome markets** (5m / 15m / 1h binaries hedgeable on HL perps) | Polymarket here is only $10M/day, 76% bot. Easy to design FOR machines on day 1. Contestable. |
| ✓ Add | **Finance** (Fed, CPI, inflation, oil) | Most diverse cohort mix. Sophisticated retail + Mid-MM both present. |
| ✓ Selective | **Geopolitics** (objective-settlement subset) | Chunky bets ($400-550 avg). Niche but lucrative. Avoid subjective markets. |
| ✗ Skip | **Sports** | Polymarket's bot ecosystem is mature; you can't out-MM them on day 1. |
| ✗ Skip | **Politics** | Polymarket owns the brand. Retail-heavy and declining. Not Verdict's edge. |
| ✗ Skip | **Culture / Tech / Weather** | Too small to matter; retail-heavy. |

---

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
   the full 120-row query output. Use `lp_rewards_confirmed_1k` as the
   strong signal, not `lp_rewards_observed`.
4. LP rewards concentration — `results/lp_rewards_concentration.csv`
   from `queries/08_lp_rewards_concentration.sql`.
5. Cohort × category drill-down (wallet counts, fills, avg trade size
   per cell) — `results/cohort_x_category_drilldown_30d.csv` from
   `queries/09_cohort_x_category_drilldown.sql`.
6. Cohort × category maker / taker split (who provides depth vs who
   consumes it, per cell) — `results/cohort_x_category_maker_taker_30d.csv`
   from `queries/10_cohort_x_category_maker_taker.sql`.
7. True venue-wide top-wallet sample — use
   `queries/11_top_wallets_30d_with_lp.sql`. No CSV is committed yet.

---

## Verdict implications (rerun-confirmed)

1. **Design for professional flow early.** Crypto and financial outcome
   markets are naturally quoteable, hedgeable, and automation-friendly.
   Verdict should prioritize API quality, deterministic settlement, and
   maker tooling before broad retail discovery work.

2. **Internal liquidity still matters, but measure it correctly.**
   Baseline liquidity should be evaluated by quote uptime, spread, depth,
   markouts, and inventory bounds, not headline volume.

3. **Hybrid maker/taker bots are strategically important.** These actors
   bridge pure MM and pure taker flow: they quote when rewarded, take when
   inventory or cross-market pricing demands it, and are easier to
   onboard than a small set of top-tier institutional MMs.

4. **Retail is still useful even if not dominant.** Less informed flow is
   what lets market makers earn the spread. A venue with only professional
   flow becomes an adverse-selection contest.

5. **Avoid overfitting to politics.** Verdict's HIP-4 edge is strongest
   in objective, fast-resolving, hedgeable crypto/financial markets.

6. **Do not assume Polymarket MMs will migrate to HIP-4 organically.**
   The sister analysis in [hip4_cross_venue/](../hip4_cross_venue/)
   shows 0/100 venue-wide top Polymarket wallets (rerun with query 11
   for true venue-wide methodology) and 0/25 LP-reward recipients
   are active on Hyperliquid HIP-4 25 days after
   launch. Only 2 of the top 30 wallets in that exported Polymarket
   sample have any HL perp activity. The
   cross-venue migration path that exists runs **HL-perps → HIP-4**,
   not Polymarket → HIP-4. Verdict's MM recruitment plan must target
   the HL-perps audience directly and recruit Polymarket-style
   expertise as a separate effort. The structural friction explaining
   this gap (Polygon vs HL, USDC.e vs USDC, Gnosis-Safe + meta tx vs
   EOA-direct, UMA vs validator-vote settlement) is unlikely to
   collapse on its own.
