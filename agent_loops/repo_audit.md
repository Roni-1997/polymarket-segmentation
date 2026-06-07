# Repo audit loop

## Objective

Audit the repo for public-facing quality, methodology consistency, and
result/source alignment.

## Loop

1. **Git state**
   - Run `git status --short`.
   - Do not overwrite unrelated user changes.

2. **Manifest consistency**
   - Count query files under `queries/`.
   - Count committed CSVs under `results/`.
   - Check `README.md` and `results/README.md` for matching counts and
     run dates.

3. **Source mapping**
   - Every public result table should map to a source query.
   - Every public note should link to source query and source CSV.
   - If a query is query-only, label it that way.

4. **Methodology consistency**
   - Check that docs distinguish:
     - touched volume vs single-counted notional,
     - wallet behavior labels vs real-world identity,
     - category tags vs true market taxonomy,
     - `resolved_on_timestamp` vs `market_end_time`.

5. **Public wording scan**
   - Scan `README.md docs results queries` for private org/product
     names, agent/vendor references, coauthor markers, fundraising
     language, and private launch-strategy wording.
   - Any hit needs manual review. Do not blindly delete technical
     source names if they are legitimate, but this repo should usually
     have no hits.

6. **Diff hygiene**
   - `git diff --check`
   - `git diff --stat`
   - Review changed docs before commit.

## Output

Lead with findings. If no issues, say so and list residual caveats.
