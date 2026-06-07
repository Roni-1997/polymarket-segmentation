# Monthly Dune refresh loop

## Objective

Refresh the repo's core Dune-derived metrics and identify material
changes since the previous snapshot.

## Core queries

Run these first:

1. `04_cohort_x_category_30d.sql`
2. `09_cohort_x_category_drilldown.sql`
3. `10_cohort_x_category_maker_taker.sql`
4. `11_top_wallets_30d_with_lp.sql`
5. `12_volume_by_time_to_expiry.sql`

Run these when time/credits allow:

6. `07_lp_rewards_top_recipients.sql`
7. `08_lp_rewards_concentration.sql`
8. `03_other_category_probe.sql`

## Loop

1. Pin the `params` CTE if the refresh should be reproducible for a
   calendar window. Otherwise keep the rolling trailing-30d window.
2. Execute queries through Dune web UI, API, or MCP.
3. Export CSVs and replace the matching files in `results/`.
4. Compare old vs new tables.
5. Flag changes worth writing up:
   - any cohort share changes by more than 5 percentage points,
   - any category share changes by more than 10 percentage points,
   - top-100 wallet turnover,
   - LP reward concentration changes by more than 5 percentage points,
   - final-24h expiry share changes by more than 5 percentage points,
   - new large `other` or stale-metadata buckets.
6. Update `results/README.md` with the new run date.
7. If there is a strong finding, hand off to `publishable_note.md`.

## Checks

- `git diff --check`
- Validate that each CSV filename still matches its source query.
- Validate that single-counted and touched volume are not mixed.
- Run the public red-flag scan from `research_yolo.md`.

## Output

- Updated CSVs.
- Updated result manifest.
- Short note listing material deltas, even if no publishable doc is
  added.
