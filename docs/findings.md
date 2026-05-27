# Findings — Polymarket participant segmentation

Period studied: Q4 2025 + Q1 2026 + trailing 30d (April 27 – May 27, 2026).
All numbers are post-correction (routing contracts excluded, owner-aggregated
via `users_address_lookup`).

---

## 1. The cohort distribution

### Trailing 30 days (May 2026)

| Cohort | Wallets | $M / 30d | % of platform | Maker share |
|---|---:|---:|---:|---:|
| Pro-MM | — | 1,964 | **31.0%** | ≥70% |
| HFT-taker | — | 1,332 | 21.0% | <30% |
| Hybrid-bot | — | 1,108 | 17.5% | 30-70% |
| Active-retail | — | 1,004 | 15.8% | <30% |
| Mid-MM | — | 540 | 8.5% | ≥70% |
| Active-mixed | — | 389 | 6.1% | 30-70% |
| **Total** | — | **6,337** | 100% | |

### Collapsed to three buckets

| Bucket | % of platform |
|---|---:|
| **MMs** (Pro + Mid) | **39.5%** |
| **Bots** (Hybrid + HFT) | **38.5%** |
| **Retail** (Active-retail + Active-mixed) | **21.9%** |

---

## 2. Category breakdown (30d, clean)

| Category | $M | % of platform | Dominant cohort |
|---|---:|---:|---|
| Sports | 1,901 | **30.0%** | Pro-MM (33%) + HFT (22%) + Hybrid (20%) — bot-dominated |
| Politics | 1,023 | **16.1%** | Active-retail (26%) — retail-heaviest category |
| Crypto | 629 | 9.9% | Pro-MM (31%) + HFT (27%) + Hybrid (18%) — 76% automated |
| Geopolitics | 334 | 5.3% | Pro-MM (31%) + Active-retail (23%) |
| Finance | 86 | 1.4% | Pro-MM (21%) + Active-retail (23%) |
| Weather | 85 | 1.3% | (new category) |
| Culture | 69 | 1.1% | Active-retail (26%) + Mid-MM (14%) |
| Tech | 11 | 0.2% | Pro-MM (22%) + Active-retail (23%) |
| Other (null-tagged) | 2,200 | **34.7%** | Mostly recurring crypto/sports w/o tags |

**Key insight**: Sports, not politics or crypto, is Polymarket's largest
category. The "Polymarket is a politics venue" narrative is outdated.

---

## 3. Trend over 6 months

| Cohort share | Q4 2025 | Q1 2026 | T30d May 2026 | Δ 6mo |
|---|---:|---:|---:|---:|
| Pro-MM | 23.2% | 29.1% | 31.0% | **+7.8pp** |
| HFT-taker | 11.5% | 17.1% | 20.3% | **+8.8pp** |
| Hybrid-bot | 22.8% | 22.0% | 17.5% | −5.3pp |
| Mid-MM | 9.7% | 6.6% | 8.5% | −1.2pp |
| Active-retail | 18.0% | 15.2% | 15.8% | −2.2pp |
| Active-mixed | 14.7% | 10.0% | 6.1% | **−8.6pp** |

### Collapsed trend

| Bucket | Q4 2025 | Q1 2026 | T30d | Δ |
|---|---:|---:|---:|---:|
| **MMs** | 33% | 36% | **40%** | +7pp |
| **Bots** | 34% | 39% | 38% | +4pp |
| **Retail** | **33%** | 25% | **22%** | **−11pp** |

### Volume in dollars

| Period | $B / qtr | $M / day | Notes |
|---|---:|---:|---|
| Q4 2025 | 10.3 | 115 | post-election lull |
| Q1 2026 | 22.2 | **247** | Super Bowl + crypto rally + sports peak |
| T30d | 6.3 | 210 | mild reversion from Q1 peak |

**Key insight**: retail share dropped 11pp in 6 months. Polymarket is
professionalizing rapidly — bots and MMs are scaling capital faster than
retail. The retail-driven narrative is increasingly false.

---

## 4. MM oligopoly — LP rewards concentration

All-time LP rewards distribution:

| Top N | $ rewards | % of all rewards |
|---|---:|---:|
| 3 wallets | $4.24M | **33.7%** |
| 10 wallets | $6.42M | **51.0%** |
| 20 wallets | $8.12M | 64.6% |
| 50 wallets | $10.60M | 84.3% |
| 100 wallets | $12.57M | 100.0% |

Total recipients (incl. spillover): 111,690 addresses
Top 3 wallets:
- `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb` — $2.43M
- `0x9d84ce0306f8551e02efef1680475fc0f1dc1344` — $1.27M
- `0xc8ab97a9089a9ff7e6ef0688e6e591a066946418` — $545k

**Classifier validation**: Pro-MM cohort top 20 — **17/20 are LP-rewards
confirmed**. The behavioral classifier independently identifies the same
wallets the rewards-program data confirms as professional MMs.

---

## 5. Cross-validation against external research

| Metric | Our number | External | Match |
|---|---|---|---|
| Total notional ~$210M/day | ✓ | Polymarket ~$200M/day post-Paradigm | ✓ |
| Automated share 78% | ✓ | "65-70%" napkin estimate (memo) | △ ours higher |
| Crypto bot-dominated | 76% | conventional wisdom | ✓ |
| Politics retail-heavy | 49% of cat | long-standing narrative | ✓ |
| Sports > Politics | 30% > 16% | post-election shift | ✓ |
| MM share of maker side | 47% | memo had said 92% | ✗ memo was wrong |
| Whales are tiny | 1.6% | "Théo moves the market" folklore | ✗ |

---

## 6. Implications for Verdict (HIP-4 outcome markets on Hyperliquid)

### What changes from the original memo

1. **Internal vault target shrinks materially.** Polymarket runs on ~40%
   MM coverage, not 80%. A Verdict vault providing **~30–40% of depth**
   is sufficient bootstrapping; retail-with-limit-orders + a few
   external MMs cover the rest. Original memo over-sized the vault by
   ~2×.

2. **Hybrid bots are the highest-leverage early-onboard target.** They
   earn LP rewards (14/20 top hybrid bots are reward-confirmed), they're
   easier to win than Tier-1 MMs (no term sheet needed), and there's a
   pool of 50–500 such wallets running rebate-farming + arb strategies
   that would migrate to a credible HIP-4 venue.

3. **For crypto outcome markets, plan for ~80%+ machine flow.** Build
   for machines first. Don't waste cycles on retail discovery features
   for crypto markets in year 1.

4. **Copy Polymarket's limit-order UX.** Active-retail provides 16% of
   platform volume and they use limit orders, not market orders. The
   default-to-limit-order UX is the unsung hero of Polymarket's depth.

5. **The professionalization trend means the launch window matters.** If
   you launch in Q3/Q4 2026, the addressable competitor mix will be
   ~80% machine-driven (vs ~67% in Q4 2025). Earlier launch = more
   retail tailwind; later launch = more pro flow to migrate.

### What does NOT change

- MMs/HFTs need professional infrastructure (API quality, settlement
  trust, rebates) — that part of the strategy is right.
- Politics-first launch is wrong — politics is only 16% of platform
  volume and shrinking.
- Whale-centric narrative is overstated; whales are 1.6% of volume.

---

## Caveats — what would tighten the analysis

1. **PnL by cohort** — would require position-state reconstruction
   across resolutions. Approximately 1-2 weeks of analyst work. Would
   let us validate Solidus's "0.55% of wallets capture 50% of profit"
   claim independently.

2. **Wallet identity attribution** — manual labeling of top 50–100
   wallets against known firms (Wintermute, GSR, B2C2, Amber, Polymarket
   own bots, public Théo cluster). 1-2 days of work.

3. **Kalshi cross-venue arb** — would require Kalshi API data
   (~$200/mo via FinFeedAPI or AhaSignals, or scraping).

4. **More routing contracts** — only excluded the most obvious 4.
   A behavioral filter (`n_fills <= 5M/quarter`) catches the most
   egregious; finer filtering might find another 3–5%.

5. **Threshold sensitivity** — the maker_share cutoff at 70% is a hard
   line through a continuous distribution. Sliding it to 60% would
   move ~5pp from HFT-taker into Pro-MM.
