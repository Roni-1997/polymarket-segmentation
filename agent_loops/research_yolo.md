# Research YOLO loop

## Objective

Find, validate, write, and ship one publishable prediction-market
microstructure insight from the repo's data.

The output should be useful to analysts, market makers, exchange
operators, and researchers. It should not read like generic market-size
commentary.

## Inputs

- Existing SQL in `queries/`
- Existing CSVs in `results/`
- Existing notes in `docs/`
- Dune curated Polymarket tables when available
- Public Polymarket/Kalshi APIs only when directly relevant

## Loop

1. **Read current state**
   - Run `git status --short`.
   - Skim `README.md`, `results/README.md`, and recent docs.
   - Identify stale manifests, missing result files, or open caveats.

2. **Choose one research question**
   - Prefer market-structure questions:
     - volume by time-to-expiry,
     - market concentration,
     - maker/taker role split,
     - LP reward concentration,
     - category mix shifts,
     - top-wallet turnover,
     - complete-set arb signatures,
     - metadata/resolution quality.
   - Avoid broad market-size or "prediction markets are growing" topics.

3. **Refresh or create the data**
   - If a query exists, rerun it when Dune/API access is available.
   - If no query exists, add the smallest query that answers the question.
   - If the full query times out, reduce the window or simplify the
     aggregation before giving up.

4. **Validate the result**
   - Check that units are correct: single-counted notional vs touched
     maker+taker volume.
   - Check joins and metadata fields against `docs/methodology.md`.
   - Keep residual buckets visible when metadata is imperfect.
   - Compare against previous CSVs when possible.

5. **Write the note**
   - Add or update one doc under `docs/`.
   - Include:
     - headline result,
     - source query,
     - source CSV,
     - concise interpretation,
     - caveats,
     - publishable takeaway.
   - Keep it analytical and public-safe.

6. **Update repo manifests**
   - Update `README.md` if a new doc/query/result is added.
   - Update `results/README.md` if a CSV is added or rerun.
   - Update `docs/methodology.md` if a schema gotcha or query convention
     changes.

7. **Run checks**
   - `git diff --check`
   - Public red-flag scan over `README.md docs results queries`.
     Check for private org/product names, agent/vendor references,
     coauthor markers, fundraising language, and private launch-strategy
     wording.
   - Review `git diff --stat`.
   - Read the new/changed public note end to end.

8. **Commit and push**
   - Commit only if the work is coherent and checks pass.
   - Use a short factual commit message.
   - Push to `origin/master`.

## Success criteria

- One publishable finding is backed by a source query and result CSV.
- Public docs have no private/company/agent references.
- Methodology caveats are explicit.
- The repo is clean after commit and push.

## Final response format

Report:

- commit hash,
- what was added,
- headline finding,
- checks run,
- any caveat or unfinished follow-up.
