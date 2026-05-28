# Polymarket participant segmentation

Reproducible SQL pack + analysis classifying every Polymarket wallet
that traded in the trailing 30 days (and prior quarters) into 6
behavioral cohorts, then measuring **who drives volume**, **who
provides depth**, **who consumes flow**, by category, over time.

Built to answer one question for the Verdict (HIP-4 outcome markets on
Hyperliquid) diligence: *who actually drives volume on Polymarket — and
which of them should a new venue target?*

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
- [Strategic implications for Verdict](#strategic-implications-for-verdict)
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
one of 6 cohorts. Then we aggregate volume, fill count, wallet count,
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

### 3. The cohort classifier — 2D grid

Every wallet lands in exactly one cell:

| | **fast** (≥100 fills/day) | **med** (1–100 fills/day) |
|---|---|---|
| **highMkr** (≥70% maker share) | Pro-MM | Mid-MM |
| **midMkr** (30–70% maker share) | Hybrid-bot | Active-mixed |
| **lowMkr** (<30% maker share) | HFT-taker | Active-retail |

A "slow" (<1 fill/day) row exists in theory but is mathematically
empty — an "active day" by definition requires a fill, so
`fills/active_days ≥ 1` always.

Maker-share threshold rationale: 70% reliably separates wallets whose
ECONOMIC ROLE is providing liquidity from wallets whose role is mixed
or pure-taking. 30% catches purely directional takers. The boundary
zone (60–70%) is fuzzy and contributes ~5pp of measurement
uncertainty.

Cadence threshold rationale: 100 fills/day is the floor for "this is
automated with high confidence" — no human places 100+ orders per day
sustainably. Below that is human-active.

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

Without these exclusions, "HFT-taker" volume is inflated by ~$3B/month
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

- **Real volume**: ~$103M/day single-counted notional. Headline numbers
  are ~2× overstated (Paradigm Dec 2025 OrderFilled double-counting).
- **Who drives volume**: **MMs 40% / Bots 38% / Retail 22%** (by touched
  volume). 78% professional, 22% retail.
- **Headcount asymmetry**: ~221k MM/bot-classified owners generate the
  78%; ~1.03M retail-tier owners generate the 22%. **The three fast
  professional cohorts alone are ~60,600 owners generating ~69% of
  volume.** Polymarket is retail by headcount, professional by dollars.
- **Categories by size**: Sports 30% > Politics 16% > Crypto 10%. The
  "Polymarket = politics" narrative is outdated. (~35% is null-tagged
  "Other" — mostly recurring crypto/sports markets without tags.)
- **The trend**: Retail share dropped 33% → 22% in 6 months. Polymarket
  is professionalizing rapidly.
- **LP rewards**: Top 10 owners = 30% of all rewards. Top 50 = 50%.
  Long tail of 111,000+ owners captures the remaining 40%. **32/100
  of venue-wide top wallets are LP-confirmed at the ≥$1k threshold.**
- **Cross-venue**: 0 of 100 venue-wide top Polymarket wallets are
  active on Hyperliquid HIP-4. The migration path that works is
  HL-perps → HIP-4, not Polymarket → HIP-4.

---

## Insights by cohort

Distinct owner counts and trade sizes from the audited rerun. Volume
share is % of touched. Owner counts from Q1 2026 (90d) for stability;
trailing 30d counts are smaller in the same ratio.

| Cohort | Plain English | Owners (Q1 90d) | % vol | Avg $/fill |
|---|---|---:|---:|---:|
| **Pro-MM** (highMkr_fast) | Fast bot that mostly posts orders. The dedicated 24/7 quoter. | 8,095 | 31% | $23 (range $7 crypto → $415 geopolitics) |
| **HFT-taker** (lowMkr_fast) | Fast bot that mostly hits orders. News/latency/cross-venue arb. | 40,910 | 21% | $19 |
| **Hybrid-bot** (midMkr_fast) | Fast bot that does both. NegRisk basket arbers, inventory-rebalancers. | 11,603 | 17% | $27 |
| **Active-retail** (lowMkr_med) | Human placing market-order bets. Headcount giant. | **849,631** | 16% | $40 ($110 politics, $25 crypto) |
| **Mid-MM** (highMkr_med) | Part-time / slower MM. Smaller scale, often passive. | 160,046 | 9% | $89 (range $33 crypto → $552 geopolitics) |
| **Active-mixed** (midMkr_med) | Sophisticated human using both limit + market orders. The fastest-shrinking cohort. | 183,232 | 6% | $52 |

**Three personas if six is too many:**

| Persona | Cohorts | % volume | % depth provided | % flow consumed |
|---|---|---:|---:|---:|
| **The Quoter** (MMs) | Pro-MM + Mid-MM | 40% | **62%** | 10% |
| **The Sniper** (Bots) | Hybrid-bot + HFT-taker | 38% | 27% | **51%** |
| **The Human** (Retail) | Active-retail + Active-mixed | 22% | 12% | 39% |

The Quoter provides 62% of standing depth. The Sniper consumes 51% of
flow. The Human provides 39% of taker flow — structurally critical
uninformed counterparty even though they're only 22% of dollars.

---

## Insights by category

Categories ranked by single-counted notional (30d):

| Category | $M / 30d | % platform | $M / day | What's in it |
|---|---:|---:|---:|---|
| Other (null-tagged) | 1,100 | **35.4%** | 37 | Mostly recurring crypto/sports markets that lost their tags |
| Sports | 921 | **29.7%** | 31 | NBA + NFL + esports (Dota, CS2, LoL) + soccer |
| Politics | 500 | 16.1% | 17 | Trump, elections, geopolitical politics |
| Crypto | 297 | 9.6% | 10 | 5m / 15m / 1h Up-or-Down recurring binaries |
| Geopolitics | 165 | 5.3% | 5.5 | Iran, Ukraine, Russia, Gaza, world affairs |
| Finance | 42 | 1.3% | 1.4 | Fed, inflation, interest rates, oil |
| Weather | 41 | 1.3% | 1.4 | (newer category) |
| Culture | 33 | 1.1% | 1.1 | Awards, MrBeast, movies, music |
| Tech | 5 | 0.2% | 0.2 | AI, science, tech outcomes |

### Per-category cohort mix (% of category touched volume)

Simplified to the 3-persona view; full 6-cohort matrix in
[docs/findings.md](docs/findings.md).

| Category | MMs | Bots | Retail | Dominant pattern |
|---|---:|---:|---:|---|
| **Sports** | 40% | **41%** | 19% | Bots edge MMs; retail tiny |
| **Politics** | 42% | 22% | **37%** | Most retail-heavy major category |
| **Crypto** | 39% | **43%** | 17% | Most bot-dominated. Retail effectively absent. |
| **Geopolitics** | **47%** | 22% | 31% | MM-heavy with meaningful retail |
| **Finance** | 37% | 25% | **38%** | Most balanced cohort mix |
| **Weather** | **43%** | 28% | 29% | MM-heavy, balanced rest |
| **Culture** | 38% | 22% | **39%** | Retail-leaning, tiny |
| **Tech** | 38% | 24% | **37%** | Balanced, tiny |
| **Other** | 38% | **44%** | 17% | Bots dominate the recurring residual |

**Strategic read per category (for Verdict):**

| Category | Focus | Why |
|---|---|---|
| **Crypto** | ✓ **Lead** | 76% automated. Polymarket here is only $10M/day. Most contestable. Design for machines. |
| **Finance** | ✓ Add | Most diverse cohort mix. Sophisticated retail + Mid-MM both present. |
| **Geopolitics** | ✓ Selective | Chunky $400-550 bets, niche but lucrative. Avoid subjective settlement. |
| **Sports** | ✗ Skip | Polymarket sports MM ecosystem is mature; you can't out-MM them on day 1 |
| **Politics** | ✗ Skip | Polymarket owns the brand. Declining. Not Verdict's edge. |
| **Culture / Tech / Weather** | ✗ Skip | Too small, retail-heavy distractions. |

---

## Insights by role (depth providers vs flow consumers)

The aggregate "% volume" number is misleading because it conflates two
different activities. Splitting maker side from taker side shows the
roles cleanly. Columns sum to 100% in each row.

### Who PROVIDES depth in each category (% of maker side)

| Category | Pro-MM | Mid-MM | Hybrid-bot | Active-mixed | HFT-taker | Active-retail |
|---|---:|---:|---:|---:|---:|---:|
| Sports | **58%** | 10% | 22% | 5% | 4% | 2% |
| Politics | **46%** | **31%** | 10% | 10% | 2% | 2% |
| Crypto | **59%** | 14% | 19% | 4% | 4% | 1% |
| Geopolitics | **59%** | **28%** | 5% | 6% | 1% | 1% |
| Finance | 38% | **29%** | 13% | 14% | 3% | 4% |
| Other | **59%** | 10% | 21% | 5% | 4% | 2% |

**Pro-MM provides 38–59% of depth in every category.** MMs combined =
**62–80% of all standing depth.** Retail provides 1–4% — they almost
never post limit orders.

### Who CONSUMES depth in each category (% of taker side)

| Category | Pro-MM | Mid-MM | Hybrid-bot | Active-mixed | HFT-taker | Active-retail |
|---|---:|---:|---:|---:|---:|---:|
| Sports | 8% | 2% | 21% | 5% | **39%** | 26% |
| Politics | 4% | 3% | 10% | 10% | 22% | **51%** |
| Crypto | 5% | 2% | 16% | 4% | **49%** | 25% |
| Geopolitics | 5% | 3% | 6% | 7% | 34% | **46%** |
| Finance | 4% | 4% | 14% | 13% | 21% | **44%** |
| Other | 6% | 1% | 21% | 5% | **44%** | 24% |

**Roles flip on the taker side.** Active-retail dominates in
slow-resolving categories (politics 51%, finance 44%, geopol 46%).
HFT-taker dominates in fast categories (crypto 49%, sports 39%, other
44%). MMs barely consume (4–8%).

**Bottom line on roles:**

| | Provides depth | Consumes flow |
|---|---|---|
| MMs | 62–80% across categories | 6–11% |
| Bots (Hybrid + HFT) | 17–30% | 35–60% |
| Retail | 3–14% | 30–55% |

MMs make. Bots and retail take. Hybrid bots are the only cohort that
straddles meaningfully (15–22% on both sides).

---

## Insights by time (the professionalization trend)

| Cohort share | Q4 2025 | Q1 2026 | T30d (May 2026) | 6mo Δ |
|---|---:|---:|---:|---:|
| Pro-MM | 23% | 29% | 31% | **+8pp** |
| HFT-taker | 12% | 17% | 21% | **+9pp** |
| Hybrid-bot | 23% | 22% | 17% | −6pp |
| Mid-MM | 10% | 7% | 9% | flat |
| Active-retail | 18% | 15% | 16% | flat |
| Active-mixed | 15% | 10% | 6% | **−9pp** |

Collapsed:

| Bucket | Q4 2025 | Q1 2026 | T30d | 6mo Δ |
|---|---:|---:|---:|---:|
| **MMs** | 33% | 36% | **40%** | +7pp |
| **Bots** | 34% | 39% | 38% | +4pp |
| **Retail** | **33%** | 25% | **22%** | **−11pp** |

Volume (single-counted, $/day): Q4 $57M → Q1 **$123M** (spike) →
T30d $103M (mild reversion).

**Three takeaways:**
1. **Professionalization is accelerating** — retail share fell 11pp in
   6 months. Polymarket is becoming a machine venue.
2. **Active-mixed (sophisticated retail) is the biggest loser** —
   14.7% → 6.0%. They may have migrated to Kalshi (which Paradigm noted
   overtook Polymarket by Q1 2026).
3. **The ratio is approaching the structural floor**. ~20% retail is
   the minimum for healthy market microstructure (uninformed flow lets
   MMs earn the spread). Polymarket is one bad quarter from the floor.

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
HIP-4. Verdict's MM-recruitment plan should target the Hyperliquid
trader base, NOT Polymarket veterans.

---

## Strategic implications for Verdict

1. **Design for professional flow early.** 78% of Polymarket volume is
   machines. Crypto outcome markets are 76% bots. Build API quality,
   maker rebates, fast cancel, NegRisk-style basket support before
   retail UX.

2. **Internal vault is the launch mechanism, not the marketing
   budget.** $5–10M HLP-style vault sized to provide 30–40% of intended
   depth in launch markets. Substitutes for missing retail in months
   0–6. Without it, MMs will not quote tight.

3. **Recruit Hyperliquid-native MMs, NOT Polymarket veterans.** The
   cross-venue data kills the "Polymarket migration" thesis. Target
   HL-perps active MMs, HLP vault delegators, ex-DeFi MM operators
   who already understand HL signing.

4. **Hybrid bots are the highest-leverage early-onboard target.** 14/20
   top hybrid bots earn LP rewards. They self-arrive with a
   competitive rebate program + NegRisk basket support. Phase 1.

5. **Open retail UX in months 3–9, not at launch.** Retail acquired
   before depth exists = adverse selection = bad reviews = death.
   Copy Polymarket's limit-order-first UX once depth exists. Hyperliquid
   wallet integration → low-friction onboarding.

6. **Tier-1 MMs (Wintermute, GSR, B2C2) come LAST**, not first. They
   require $10M+/day notional for their seat-fee math to work. Phase
   3, month 9+.

7. **Skip politics, skip sports, skip Polymarket migration plays.**
   Politics is 16% of Polymarket and shrinking. Sports MM ecosystem
   on Polymarket is mature. Polymarket → HIP-4 migration is 0/100.

**Phased launch playbook in one table:**

| Phase | Months | Acquire | Volume target | Critical metric |
|---|---|---|---|---|
| **0** Build | T-3 → T-0 | Vault + 3–5 HL-native MM term sheets | $0 | Vault depth quoting ≤5bps |
| **1** Ignition | 0–3 | Hybrid bots self-arrive; HL-perps power users | $1–5M/day | Maker side ≥40% from vault, ≥30% from MMs |
| **2** Retail | 3–9 | Retail via HL wallet integration + airdrop tie-in | $10–20M/day | **Retail % of taker ≥20%** |
| **3** Maturity | 9–18 | Tier-1 MMs become viable | $30–50M/day | Top-10 MM concentration <60% |

Full implications: [docs/findings.md](docs/findings.md).

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
   8.6pp drop in Active-mixed cohort likely reflects migration to
   Kalshi. Confirming requires Kalshi API data ($200/mo via FinFeedAPI
   or scraping) + matching wallet timestamps across venues. **~3–5 days.**

3. **Wallet-level firm attribution.** We can identify the LP-reward
   top 10 by address. Mapping them to firms (Wintermute, GSR, B2C2,
   Amber, Susquehanna, etc.) requires manual labeling against public
   registries + on-chain clustering for sibling-EOA grouping. **~1–2
   days.** Important for BD targeting.

4. **Wash-trade exclusion.** Solidus flagged ~15% of some markets as
   wash trading consistent with POLY airdrop farming. Filtering paired
   YES+NO same-owner positions in the same condition_id within a
   short window would reduce Active-mixed and Active-retail cohort
   sizes. Likely shifts the headline cohort numbers by 2–5pp.
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

### Operational / for Verdict specifically

8. **Internal vault sizing model.** Given target depth (X% of
   intended book), market correlation matrix, and expected adverse
   selection cost from this analysis, what's the minimum vault TVL
   for Phase 0–1? Build a parameter sweep that outputs (vault size,
   maker rebate budget, expected APY, kill-switch trigger
   thresholds). **~3–5 days, requires market-specific assumptions.**

9. **MM acquisition pipeline.** Build a wallet-level scoring system
   that ranks HL-perps wallets by likelihood-to-onboard for HIP-4.
   Inputs: their HL trading sophistication, maker share on HL,
   capital deployed, any prediction-market activity. Use this to
   prioritize BD outreach. **~1 week.**

10. **Monthly automated rerun.** Pin the `params` CTE to explicit
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
  sports).** Verdict's edge is in objective-resolution markets;
  subjective markets aren't the target audience.

---

## Repo structure

| Path | What |
|---|---|
| [docs/findings.md](docs/findings.md) | Strategic memo — full findings + Verdict implications |
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
