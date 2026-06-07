# Agent loops

These are reusable runbooks for research agents working on this
repo. The goal is to make recurring work loop-driven: rerun data,
compare against prior snapshots, detect a publishable market-structure
finding, write it up, validate it, and commit it.

Use these as the first instruction to an agent rather than writing a
fresh one-off request.

## Available loops

| Loop | Use |
|---|---|
| [`research_yolo.md`](research_yolo.md) | Find and ship one data-backed, publishable market-structure insight. |
| [`monthly_dune_refresh.md`](monthly_dune_refresh.md) | Refresh core Dune outputs and flag metric changes. |
| [`publishable_note.md`](publishable_note.md) | Turn a validated result into a concise public research note. |
| [`repo_audit.md`](repo_audit.md) | Check methodology, public wording, result manifests, and repo hygiene. |

## Global rules

- Public-facing only. Do not add private company strategy, fundraising,
  product-roadmap, or agent/vendor references to repo docs.
- Every quantitative claim needs a source query and either a committed
  result CSV or a clearly marked "not yet run" caveat.
- Prefer compact, reproducible SQL over broad exploratory queries that
  time out on Dune's 2-minute tier.
- Keep single-counted venue notional separate from touched maker+taker
  participant volume.
- Preserve metadata caveats. Do not drop stale/unknown buckets just to
  make a result look cleaner.
- Before commit, run the checks listed in each loop.

## Minimal invocation

```text
Run agent_loops/research_yolo.md.

Repo: /Users/kamil/polymarket-segmentation
Goal: find and ship one publishable prediction-market microstructure
insight. Commit and push when complete.
```
