# Results

These CSVs are legacy exports from the pre-audit query version.

Do not cite exact percentages or dollar volumes from these files without
rerunning the SQL in `queries/`. The current SQL changed:

- system/router exclusions now also apply after proxy-to-owner mapping;
- cohort outputs are explicitly labeled as touched volume;
- LP rewards are deduped across merkle claims and direct transfers;
- material LP confirmation uses a `$1,000` reward threshold.

