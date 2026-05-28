# Polymarket participant segmentation

Reproducible SQL pack + analysis classifying every Polymarket wallet
that traded in the trailing 30 days (and prior quarters) into 7
behavioral cohorts, then measuring **who drives volume**, **who
provides depth**, **who consumes flow**, by category, over time.

Built to answer one question: *who actually drives volume and liquidity
on Polymarket?*

Repo state: audited rerun, 11 SQL queries, 9 result CSVs, cross-venue
overlap check. Current as of **2026-05-27**.

---

## Contents

- [Methodology](#methodology) — how the classifier works, what we count, what we exclude
- [Headline numbers (60-second read)](#headline-numbers-60-second-read)
- [Insights by cohort](#insights-by-cohort) — who plays, sized by dollars and headcount
- [Insights by category](#insights-by-category) — sports / politics / crypto / finance / etc.
- [Insights by role (maker vs taker)](#insights-by-role-depth-providers-vs-flow-consumers)
- [Insights by time](#insights-by-time-the-professionalization-trend)
- [Cross-venue (Polymarket × HIP-4)](#cross-venue-the-migration-that-isnt-happening)
- [Next steps / open questions](#next-steps--open-questions)
- [Repo structure](#repo-structure)
- [How to reproduce](#how-to-reproduce)
- [Caveats](#caveats)

---

## Methodology

### 1. What we measure

For each wallet that traded on Polymarket (CTF Exchange + NegRisk
Exchange on Polygon) in the analysis window, we compute behavioral
features from raw `OrderFilled` events and classify the wallet into
one of 7 cohorts. Then we aggregate volume, fill count, wallet count,
and average trade size per (cohort × category × maker/taker side).

### 2. Data sources

All on-chain, all free, via [Dune curated tables](https://docs.dune.com/data-catalog/curated/prediction-markets/polymarket/overview):

| Table | What we pull |
|---|---|
| `polymarket_polygon.market_trades` | Every fill — block_time, maker, taker, amount, condition_id |
| `polymarket_polygon.market_details` | Market metadata + comma-separated `tags` for category mapping |
| `polymarket_polygon.users_address_lookup` | Proxy wallet → owner EOA mapping (so one MM with many proxies = one entity) |
| `polymarket_polygon.ctf_evt_positionsplit` / `ctf_evt_positionsmerge` | Complete-set arber signals (not currently in the main classifier) |
| `polymarket_usdc_merkle_distributor_polygon.MerkleDistributor_evt_Claimed` | LP rewards ground truth — material MM signal |
| `erc20_polygon.evt_Transfer` (from `0xc28848...`) | Older direct LP-reward transfers, deduped against merkle claims |

### 3. The cohort classifier — 7-cohort grid

Two axes (**maker share** × **fills per active day**) produce a 3×3 grid.
The 3 cells in the `discretionary` cadence band collapse into a single
`Retail` bucket — once you're at <10 fills/day, maker/taker behavior is a
stylistic order-type choice rather than a strategic role.

| | **fast** (≥100/day) | **systematic** (10–100/day) | **discretionary** (<10/day) |
|---|---|---|---|
| **highMkr** (≥70% maker share) | Pro-MM | Mid-MM | ↓ |
| **midMkr** (30–70%) | Hybrid-bot | Systematic-mixed | ↓ |
| **lowMkr** (<30%) | Fast-taker | Systematic-taker | ↓ |
| **(any maker share)** | — | — | **Retail** |

**7 cohorts total.** Labels are intentionally behavioral, not identity:
"Fast-taker" describes observed cadence + low maker share, not formally
latency-classified HFT. "Retail" is the only cohort where headcount
dominates — by volume it's the smallest.

**Threshold rationale:**

- **Maker ≥70%** = wallet acts primarily as liquidity provider
- **Maker 30–70%** = hybrid (basket arb / inventory rebalancing / news-reaction MM)
- **Maker <30%** = wallet acts primarily as liquidity consumer
- **Cadence ≥100/day** = clearly automated (no human sustains 100+ orders/day)
- **Cadence 10–100/day** = systematic / tool-assisted (slow algo, copy-trading wrapper, sophisticated discretionary human)
- **Cadence <10/day** = retail-cadence discretionary trading

**Cadence is fills per ACTIVE day, not per calendar day.** A wallet
trading 30 fills concentrated in 3 hot days has cadence 10
(systematic), even if dormant the other 27 days. Same wallet trading
30 fills spread evenly across 30 days has cadence 1.0 (Retail). This
catches behavior, not just total activity.

**Important framing:** these are *observed trading behaviors over the
measurement window*, not user identities. A wallet labeled `Retail` may
be a casual bettor, OR a wealth-tier directional trader who places few
chunky bets, OR a hedger — the data only proves low cadence + low
maker share. We don't claim identity.

### 4. Owner aggregation

Wallets are aggregated to **owner level** via
`users_address_lookup`. Polymarket creates a proxy wallet (Safe or
Magic) controlled by an owner EOA for each user; trades happen at the
proxy level. Aggregating to owner means one firm running 30 proxies
counts as one entity. EOAs that trade directly (no proxy) keep their
own address — correct.

This does NOT cluster across multiple owner EOAs run by the same firm
(an MM that uses 5 independent EOAs for risk separation). For that
you'd need manual address clustering — out of scope.

### 5. Contract exclusion

Known routing/system contracts are excluded both as raw maker/taker
addresses AND after proxy-to-owner mapping (some system addresses can
re-enter via owner mapping). Hardcoded list:

| Address | Role |
|---|---|
| `0xe111180000d2663c0091e4f400237545b87b996b` | NegRisk Adapter |
| `0xe2222d279d744050d28e00520010520000310f59` | NegRisk router (sibling) |
| `0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e` | CTF Exchange contract |
| `0xc5d563a36ae78145c45a50134d48a1215220f80a` | Suspected router (106k fills/day, 0% maker) |

Behavioral safety net: `HAVING COUNT(*) ≤ 5,000,000` per window
catches any router we haven't enumerated (no real wallet trades >55k
fills/day sustained).

Without these exclusions, fast-taker volume is inflated by ~$3B/month
from NegRisk basket pass-through. With them, headline numbers match
Paradigm's December 2025 finding that Polymarket headline volume is
~2× overstated.

### 6. Volume accounting — touched vs single-counted

**Touched volume** = maker_side amount + taker_side amount, summed.
Used for participant share (because each side of every fill counts as
an instance of participation).

**Single-counted notional** = touched / 2. Used for venue volume
comparisons ($/day). Matches what Paradigm and the corrected
Polymarket dashboards report.

Both columns appear in the output of `04_cohort_x_category_30d.sql`.

### 7. LP rewards ground truth

To validate "is this wallet really a market maker?" we UNION two
on-chain reward sources:

- `MerkleDistributor_evt_Claimed` events (canonical post-2024 rewards
  mechanism)
- USDC transfers from the rewards distributor wallet
  `0xc288480574783BD7615170660d71753378159c47`

The UNION deduplicates by `evt_tx_hash` (merkle claims trigger a USDC
transfer in the same tx, so naive UNION double-counts).

**Material LP confirmation** requires ≥$1,000 all-time rewards. Dust
rewards (<$1k) are weak evidence — they accumulate from any
incidental maker activity.

### 8. Time windows

- Main analysis: **trailing 30 days** (April 27 – May 27, 2026)
- Historical comparison: **Q4 2025** (Oct 1 – Jan 1) and **Q1 2026**
  (Jan 1 – Apr 1)
- Dune free-tier 2-min SQL timeout blocks 180-day windows in one
  shot. Use 30-day or 90-day chunks.

Full spec: [docs/methodology.md](docs/methodology.md).

---

## Headline numbers (60-second read)

- **Real volume**: ~$102M/day single-counted notional. Headline numbers
  are ~2× overstated (Paradigm Dec 2025 OrderFilled double-counting).
- **Who drives volume** (touched volume, T30d):
  **MMs 38% / Bots+Systematic 56% / Retail 5%.**
  **94.7% professional or systematic, 5.3% retail.**
- **Headcount asymmetry**: ~327k professional/systematic owners
  generate the 94.7%; ~926k true-retail owners generate the 5.3%.
  Polymarket is retail by headcount, professional by dollars.
- **Categories by size**: Sports 30% > Politics 16% > Crypto 10%. The
  "Polymarket = politics" narrative is outdated. (~35% is null-tagged
  "Other" — mostly recurring crypto/sports markets without tags.)
- **The retail collapse**: Retail share fell from **10.7% (Q4 2025) →
  7.7% (Q1 2026) → 5.3% (T30d May 2026)**. Halved in 6 months. Far
  below the ~20% structural floor for healthy uninformed flow.
- **LP rewards**: Top 10 owners = 30% of all rewards. Top 50 = 50%.
  Long tail of 111,000+ owners captures the remaining 40%. **32/100
  of venue-wide top wallets are LP-confirmed at the ≥$1k threshold.**
- **Overlay tags (T30d, top-100 venue-wide)**: 16/100 are
  complete-set arbers; 48/100 are large-ticket whales; 0/100 active
  on Hyperliquid HIP-4.
- **Cross-venue**: 0 of 100 venue-wide top Polymarket wallets are
  active on Hyperliquid HIP-4. The migration path that works is
  HL-perps → HIP-4, not Polymarket → HIP-4.

---

## Insights by cohort

Distinct owner counts from Q1 2026 (90d) for stability; trailing-30d
counts are smaller in the same ratio. Volume share is % of touched
volume.

| Cohort | Plain English | Owners (Q1 90d) | % vol (T30d) | Avg $/fill (T30d) |
|---|---|---:|---:|---:|
| **Pro-MM** (highMkr_fast) | Fast bot, ≥70% maker. The dedicated 24/7 quoter. | 8,095 | **31.0%** | $22 |
| **Fast-taker** (lowMkr_fast) | Fast bot, <30% maker. News/latency/cross-venue arb. | 40,910 | 20.5% | $19 |
| **Hybrid-bot** (midMkr_fast) | Fast bot, mixed maker/taker. NegRisk basket arber, inventory-rebalancer. | 11,603 | 17.9% | $27 |
| **Systematic-taker** (lowMkr_systematic) | 10–100 fills/day, <30% maker. Slow algo, copy-trader, tool-assisted discretionary. | 199,448 | 12.7% | $38 |
| **Mid-MM** (highMkr_systematic) | 10–100 fills/day, ≥70% maker. Part-time / slower MM. | 21,541 | 7.4% | $91 |
| **Systematic-mixed** (midMkr_systematic) | 10–100 fills/day, mixed. Slow hybrid bot, advanced discretionary. | 45,833 | 5.2% | $56 |
| **Retail** (any maker, <10 fills/day) | Discretionary cadence — true retail or low-frequency directional bettor. | **926,087** | **5.3%** | $48 |

**Three-persona rollup:**

| Persona | Cohorts | % volume (T30d) |
|---|---|---:|
| **Depth providers** | Pro-MM + Mid-MM | **38.4%** |
| **Efficiency / sniper flow** | Hybrid-bot + Fast-taker + Systematic-mixed + Systematic-taker | **56.3%** |
| **Retail** | Retail | **5.3%** |

**This is materially sharper than the prior framing.** Under the
previous (looser) classifier, retail was ~22% of volume. Under the
strict definition (<10 fills/active_day), retail is **5.3%**. The
difference is the **Systematic-taker** cohort (12.7% of volume): wallets
doing 10–100 fills/day with low maker share — they're not retail
behaviorally, even if they're individually small.

---

## Insights by category

Categories ranked by single-counted notional (30d):

| Category | $M / 30d | % platform | $M / day | What's in it |
|---|---:|---:|---:|---|
| Other (null-tagged) | 1,100 | **35.8%** | 37 | Mostly recurring crypto/sports markets that lost their tags |
| Sports | 906 | **29.5%** | 30 | NBA + NFL + esports (Dota, CS2, LoL) + soccer |
| Politics | 492 | 16.0% | 16 | Trump, elections, geopolitical politics |
| Crypto | 290 | 9.4% | 10 | 5m / 15m / 1h Up-or-Down recurring binaries |
| Geopolitics | 163 | 5.3% | 5.4 | Iran, Ukraine, Russia, Gaza, world affairs |
| Finance | 41 | 1.3% | 1.4 | Fed, inflation, interest rates, oil |
| Weather | 40 | 1.3% | 1.3 | (newer category) |
| Culture | 33 | 1.1% | 1.1 | Awards, MrBeast, movies, music |
| Tech | 5 | 0.2% | 0.2 | AI, science, tech outcomes |

### Per-category cohort mix — full 7-cohort breakdown

% of category touched volume by cohort (T30d). Bold = top cohort in
that category.

| Category | Pro-MM | Mid-MM | Hybrid-bot | Sys-mixed | Fast-taker | Sys-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Crypto** | **31.7%** | 5.8% | 17.4% | 3.6% | **26.0%** | 10.5% | 5.0% |
| **Politics** | 24.7% | 14.4% | 9.8% | 7.9% | 11.9% | **18.4%** | **13.0%** |
| **Sports** | **32.9%** | 5.3% | 21.6% | 5.0% | 21.1% | 11.5% | 2.7% |
| **Finance** | 21.1% | 13.3% | 13.4% | 11.8% | 11.6% | **19.1%** | 9.7% |
| **Geopolitics** | **31.8%** | 13.0% | 5.2% | 5.2% | 17.3% | 14.8% | **12.7%** |
| **Culture** | 24.2% | 11.3% | 14.6% | 10.8% | 8.6% | **19.7%** | 10.8% |
| **Weather** | **32.9%** | 9.5% | 10.5% | 6.5% | 17.8% | **18.2%** | 4.6% |
| **Tech** | 23.8% | 11.0% | 13.7% | 9.6% | 11.3% | **18.0%** | 12.7% |
| **Other** | **32.5%** | 5.2% | 20.9% | 4.2% | 23.8% | 10.8% | 2.5% |

### Per-category cohort mix — 3-persona collapse

Same data, collapsed into 3 personas for quick reading:

| Category | MMs (Pro+Mid) | Bots+Algo (Hybrid+Sys-mixed+Fast+Sys-taker) | Retail | Dominant pattern |
|---|---:|---:|---:|---|
| **Sports** | 38% | **59%** | 2.7% | Pro-MM + fast bots dominate; almost no retail |
| **Politics** | 39% | 48% | **13.0%** | Most retail-heavy; Sys-taker is largest single cohort |
| **Crypto** | 38% | **58%** | 5.0% | Pro-MM + Fast-taker dominant. Almost no retail. |
| **Finance** | 34% | **56%** | 9.7% | Most balanced mix; Mid-MM tail present |
| **Geopolitics** | **45%** | 43% | 12.7% | MM-heavy + meaningful retail. Chunky bet sizes. |
| **Weather** | 42% | **53%** | 4.6% | Bot-leaning |
| **Culture** | 36% | **54%** | 10.8% | Sys-taker dominant, tiny category |
| **Tech** | 35% | **53%** | 12.7% | Sys-taker dominant, tiny category |
| **Other** | 38% | **60%** | 2.5% | Bots dominate the recurring residual |

### Single-counted notional per (cohort, category), $M

For sizing comparisons. Total per category = sum across cohorts.

| Category | Pro-MM | Mid-MM | Hybrid-bot | Sys-mixed | Fast-taker | Sys-taker | Retail | **Total** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sports | 298 | 48 | 196 | 45 | 191 | 105 | 24 | **906** |
| Other | 358 | 57 | 230 | 46 | 262 | 119 | 28 | **1,100** |
| Politics | 122 | 71 | 48 | 39 | 58 | 90 | 64 | **492** |
| Crypto | 92 | 17 | 50 | 10 | 75 | 30 | 14 | **290** |
| Geopolitics | 52 | 21 | 9 | 9 | 28 | 24 | 21 | **163** |
| Finance | 9 | 6 | 6 | 5 | 5 | 8 | 4 | **41** |
| Weather | 13 | 4 | 4 | 3 | 7 | 7 | 2 | **40** |
| Culture | 8 | 4 | 5 | 4 | 3 | 7 | 4 | **33** |
| Tech | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **5** |

### Per-category headline reads

- **Crypto** — bot-extreme: 75% from fast bots (Pro-MM 32% + Fast-taker 26% + Hybrid-bot 17%). Retail effectively absent (5%). Most automated category.
- **Politics** — most retail-heavy AND most balanced cohort spread. Retail 13% (highest), but Sys-taker is biggest single cohort (18%). Real money: ~$110 avg retail trade.
- **Sports** — bot-dominated (Pro-MM 33% + Hybrid-bot 22% + Fast-taker 21% = 77%). Hybrid-bot share highest of any category — NegRisk basket arb works here.
- **Finance** — most balanced mix. Mid-MM at 13% is second-highest across categories — small MMs like slow-resolving markets.
- **Geopolitics** — MM-heavy with chunky human bets. Avg $400–550/fill. Retail 13% is real money.
- **Culture / Tech** — long-tail patterns: Sys-taker dominant (~18-20%), retail 11-13%. Slow-algo + human discretionary, not fast bots.

Note vs prior framing: under the previous (looser) classifier, retail
shares per category were 19–39%. Under the strict definition (<10
fills/active_day = retail), retail per category is **2.5–13%**. The
difference is the Systematic-taker cohort (now properly classified as
algo/bot), which was previously lumped into retail.

## Insights by role (depth providers vs flow consumers)

The aggregate "% volume" number is misleading because it conflates two
different activities. Splitting maker side from taker side shows the
roles cleanly. Columns sum to 100% in each row.

### Who PROVIDES depth in each category (% of maker side)

| Category | Pro-MM | Mid-MM | Hybrid-bot | Systematic-mixed | Fast-taker | Systematic-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sports | **58%** | 9% | 22% | 5% | 4% | 1% | 1% |
| Politics | **46%** | **26%** | 10% | 8% | 2% | 2% | 7% |
| Crypto | **59%** | 10% | 19% | 4% | 4% | 1% | 4% |
| Geopolitics | **59%** | **23%** | 5% | 5% | 1% | 1% | 6% |
| Finance | 38% | **23%** | 13% | 12% | 3% | 3% | 8% |
| Other | **59%** | 9% | 21% | 4% | 4% | 1% | 1% |

**Pro-MM provides 38–59% of depth in every category.** MMs combined
(Pro+Mid) = **65–82% of all standing depth.** Retail provides 1–8%.

### Who CONSUMES depth in each category (% of taker side)

| Category | Pro-MM | Mid-MM | Hybrid-bot | Systematic-mixed | Fast-taker | Systematic-taker | Retail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sports | 8% | 2% | 21% | 5% | **38%** | 22% | 4% |
| Politics | 4% | 3% | 10% | 8% | 22% | **35%** | **19%** |
| Crypto | 5% | 1% | 16% | 4% | **49%** | 20% | 6% |
| Geopolitics | 5% | 3% | 6% | 6% | 34% | **29%** | **19%** |
| Finance | 4% | 4% | 14% | 12% | 21% | **35%** | 11% |
| Other | 6% | 1% | 21% | 4% | **44%** | 20% | 4% |

**Taker side is dominated by automated/systematic cohorts.** Combined
Fast-taker + Systematic-taker = **57–69% of taker flow per category**.
Retail consumes only 4–19% as takers. MMs barely consume (4–11%).

**Bottom line on roles (3-persona, T30d, %s of total maker side / total taker side):**

| Persona | Provides depth (% maker side) | Consumes flow (% taker side) |
|---|---:|---:|
| **MMs** (Pro + Mid) | **69%** | 8% |
| **Bots + Algo** (Hybrid + Fast + Systematic-mixed + Systematic-taker) | 28% | **85%** |
| **Retail** | 3% | 8% |

**MMs provide 69% of all standing depth. Bots and algo consume 85% of all flow.**
Retail provides 3% and consumes 8% — they're a much smaller structural
piece than the prior framing suggested. The uninformed-flow floor problem
is real: there's only 8% retail flow against 85% bot/algo flow.

---

## Insights by time (the professionalization trend)

| Cohort share | Q4 2025 | Q1 2026 | T30d (May 2026) | 6mo Δ |
|---|---:|---:|---:|---:|
| Pro-MM | 23% | 29% | 31% | **+8pp** |
| Fast-taker | 12% | 17% | 21% | **+9pp** |
| Hybrid-bot | 23% | 22% | 18% | −5pp |
| Systematic-taker | 13% | 12% | 13% | flat |
| Systematic-mixed | 12% | 7% | 5% | **−7pp** |
| Mid-MM | 7% | 5% | 7% | flat |
| **Retail** | **11%** | **8%** | **5%** | **−6pp (halved)** |

Collapsed (3-persona):

| Bucket | Q4 2025 | Q1 2026 | T30d | 6mo Δ |
|---|---:|---:|---:|---:|
| **MMs** (Pro + Mid) | 31% | 34% | **38%** | **+7pp** |
| **Bots + Algo** (Hybrid + Fast + Systematic-mixed + Systematic-taker) | 58% | 58% | 56% | flat |
| **Retail** | **11%** | **8%** | **5%** | **−6pp (halved)** |

Volume (single-counted, $/day): Q4 $58M → Q1 **$123M** (spike) →
T30d $102M (mild reversion).

**Three takeaways:**

1. **The retail collapse is dramatic.** Under the strict definition
   (<10 fills/active_day), retail share **halved in 6 months**: 10.7%
   → 7.7% → 5.3%. The prior, looser classifier reported retail as
   33% → 22% (also declining, but the magnitude understates the
   actual collapse).

2. **MMs continue to gain share** — Pro-MM is +8pp, Mid-MM stable.
   The professionalization isn't just "bots replacing retail" — MM
   capital is also scaling up faster than the rest of the venue.

3. **Polymarket is operating WAY below the structural retail floor.**
   Healthy markets typically need ~20% uninformed flow for MMs to
   earn the spread profitably. Polymarket is at 5.3% retail flow.
   Either the Systematic-taker / Systematic-mixed cohorts are
   uninformed-ENOUGH to function as retail-substitute, OR MMs are
   quietly losing money. Worth investigating: PnL-by-cohort analysis
   (see next steps).

---

## Cross-venue (the migration that isn't happening)

Sister analysis: [hip4_cross_venue/](hip4_cross_venue/). HIP-4 outcome
markets launched on Hyperliquid 2026-05-02.

| Check | Result |
|---|---|
| 100 venue-wide top Polymarket wallets ∩ HIP-4 top-127 | **0/100** |
| 25 LP-reward top recipients ∩ HIP-4 top-127 | **0/25** |
| Top 30 Polymarket wallets with any HL perp activity | 2/30 |
| Top 30 Polymarket wallets with HIP-4 activity | 0/30 |
| HIP-4 top-30 with any Polygon activity | 10/30 (casual, not Polymarket-specific) |

**The Polymarket MM oligopoly is not migrating to HIP-4.** Friction
points: Polygon vs HL signing, USDC.e vs USDC, Gnosis-Safe + meta-tx
vs EOA-direct, UMA vs validator-vote settlement. The friction is
structural and won't collapse on its own.

**The migration that IS happening:** HL-perps traders →
HIP-4. The observed overlap is HL-native rather than Polymarket-derived.

---

## Next steps / open questions

Things this repo does NOT yet measure but that would tighten the
analysis. Roughly ordered by leverage.

### High-value additions

1. **PnL by cohort.** Solidus measured profit concentration in politics
   markets only (0.55% of wallets capture 50% of profit, Dec 2025–Feb
   2026). Reproducing across all categories + longer windows would let
   us check whether the claim generalizes and quantify adverse
   selection per cohort. Source: defioasis PnL dashboard +
   position-state reconstruction. **~1–2 weeks of analyst time.**

2. **Cross-venue arber detection (Polymarket ↔ Kalshi).** The
   drop in Systematic-mixed cohort (11.6% → 5.2%) and Retail (10.7%
   → 5.3%) likely reflects migration to Kalshi. Confirming requires
   Kalshi API data ($200/mo via FinFeedAPI or scraping) + matching
   wallet timestamps across venues. **~3–5 days.**

3. **Wallet-level firm attribution.** We can identify the LP-reward
   top 10 by address. Mapping them to firms (Wintermute, GSR, B2C2,
   Amber, Susquehanna, etc.) requires manual labeling against public
   registries + on-chain clustering for sibling-EOA grouping. **~1–2
   days.**

4. **Wash-trade exclusion.** Solidus flagged ~15% of some markets as
   wash trading consistent with POLY airdrop farming. Filtering paired
   YES+NO same-owner positions in the same condition_id within a
   short window would reduce Systematic-mixed and Retail cohort sizes.
   Likely shifts the headline cohort numbers by 2–5pp.
   **~2–3 days.**

### Medium-value additions

5. **Builder Program flow attribution.** Some bot volume routes
   through the Polymarket Builder Program (231+ registered apps as
   of late 2025: Telegram bots, copy-trading wrappers, Discord apps).
   Joining trades against the Builder registry would distinguish
   "direct API bots" from "Telegram bot / copy-trader wrapper" flow.
   Source: gateresearch Builders dashboard. **~1 day.**

6. **Resolve the "Other" tag bucket.** 35% of platform volume is
   null-tagged markets. Most are recurring crypto/sports markets that
   lost their tags. Direct access to Polymarket's internal taxonomy
   would close this gap. Currently blocked on Polymarket data API.

7. **Complete-set arber cohorting.** Dune exposes
   `ctf_evt_positionsplit` and `ctf_evt_positionsmerge`. Adding
   split/merge features to the classifier would carve out a real
   complete-set arber cohort (currently mixed into Hybrid-bot).
   **~1 day.**

8. **Monthly automated rerun.** Pin the `params` CTE to explicit
   timestamps and schedule monthly Dune executions. Build a
   Streamlit/Observable dashboard that visualizes the cohort
   distribution over time. **~2–3 days.**

### What we explicitly chose NOT to do

- **Generate prediction-market market size forecasts.** This is a
  microstructure analysis, not a TAM estimate. Forecasts are easy to
  fabricate; structural insights are not.
- **Compare Polymarket against every venue.** Sister analysis covers
  HIP-4. Kalshi/Manifold/Limitless/Myriad cross-checks are open
  follow-ups.
- **Make recommendations on subjective markets (politics, culture,
  sports).** This repo measures observed Polymarket structure; it does
  not prescribe which categories another venue should list.

---

## Repo structure

| Path | What |
|---|---|
| [docs/findings.md](docs/findings.md) | Detailed findings and result-source mapping |
| [docs/methodology.md](docs/methodology.md) | Classifier spec, contract exclusions, schema gotchas |
| [docs/external_research.md](docs/external_research.md) | Cross-validation vs Paradigm, Solidus, Chainalysis, Dune dashboards |
| [queries/](queries/) | 11 SQL files — paste any into Dune to reproduce |
| [results/](results/) | 9 CSV result tables from the audited rerun (2026-05-27) |
| [hip4_cross_venue/](hip4_cross_venue/) | Sister analysis: bidirectional HIP-4 ↔ Polymarket overlap |

---

## How to reproduce

1. Open [dune.com](https://dune.com), create a new query, paste any
   file from [queries/](queries/), save, run.
2. Total cost ~350 credits across the core queries — well within the
   Dune free tier's 2,500/month allowance.
3. Recommended order: `01` (action enum probe) → `02` (tags probe) →
   `03` (Other-category probe) → `04` (main cohort × category) →
   `05` (per-cohort top-20 validation) → `06` (run twice with
   different quarter windows for the time trend) → `07` (LP
   recipients) → `08` (LP concentration) → `09` (drilldown with
   wallets/fills/avg-trade) → `10` (maker/taker split) → `11`
   (venue-wide top-100 with LP flags, for cross-venue checks).

For programmatic execution via Dune MCP, see
[docs/methodology.md](docs/methodology.md).

---

## Caveats

1. **Window is 30 days for the main analysis.** Quarterly comparisons
   are 90-day windows. Dune's free-tier 2-min SQL timeout blocks
   180-day windows in one shot.

2. **Snapshot CSVs are dated 2026-05-27.** Most SQL uses rolling
   `CURRENT_TIMESTAMP` windows, so reruns will drift unless you pin
   the `params` CTE timestamps.

3. **MM/HFT/Retail labels are imperfect.** The classifier forces
   discrete buckets via first-match rule order; real wallets near
   threshold boundaries (60–70% maker share) are arbitrary. Numbers
   shift ±5pp with threshold changes. Treat as directional.

4. **Owner aggregation does not cluster across firm-owned EOAs.** An
   MM running 5 independent EOAs counts as 5 entities.

5. **"Other" category is ~35% of platform volume** even after
   expanded tag matching. Most is null-tagged residual.

6. **Paradigm and Solidus are non-neutral sources.** Paradigm is a
   Kalshi investor; Solidus sells compliance software. The on-chain
   methodology of both is verifiable but framing isn't neutral.
   Citation guidance in
   [docs/external_research.md](docs/external_research.md).

7. **PnL by cohort is not measured.** "Volume share" ≠ "profit
   share." Solidus claims 0.55% of wallets capture 50% of profit in
   politics; our top-10 LP-reward owners capture 30% of rewards.
   Different metrics, both directionally valid.
