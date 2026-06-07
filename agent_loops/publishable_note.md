# Publishable note loop

## Objective

Turn a validated result into a concise public research note.

## Structure

Use this shape unless the result clearly needs something else:

1. Title
2. One-paragraph setup
3. Result table
4. Headline takeaway
5. Interpretation
6. Method
7. Caveats
8. Publishable takeaway

## Writing constraints

- Be analytical, not promotional.
- Prefer market-structure language:
  - liquidity,
  - maker/taker,
  - event timing,
  - concentration,
  - resolution quality,
  - metadata quality,
  - subsidy efficiency.
- Avoid:
  - private company names,
  - fundraising framing,
  - product strategy,
  - "AI" unless the note is specifically about an AI-measured metric,
  - broad market-size hype.

## Required evidence

Every note must link to:

- source SQL in `queries/`,
- source CSV in `results/`,
- methodology doc if a schema caveat matters.

If a query was added but not run, the note must say so and must not
present the result as measured.

## Pre-commit checks

- Read the note end to end.
- Confirm no unsupported exact claims.
- Confirm all numbers appear in the source CSV.
- Run `git diff --check`.
- Run the public red-flag scan from `research_yolo.md`.
