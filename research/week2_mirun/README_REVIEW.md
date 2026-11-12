# Archived exploratory implementation

These original scripts and summaries are preserved for traceability. They use a
fixed-alpha GARCH with burn 200 and one-way CR1 by the first overlapping regime;
they are not the active full-membership comparison in `week2_completion`.

Known limitations: first-membership labels can omit shared regimes; shared
calendar factors can cross regime-grouped folds; `baseline_no_dependence` still
has a calendar factor; scripts run at import and some depend on local working
directories/optional `arch`; `gate2_checks.json` contains non-standard NaN values
for undefined diagnostics. Do not treat those values as zero or as a Gate pass.
The saved summaries lack the original per-replication intervals and environment
manifest. Reviewer reconstructions are labelled separately.

Use the active entrypoint documented in `docs/WEEK2_COMPLETION_README.md` for
new exploratory executions. No archived result is declared final or pooled with
another estimator by this review. See `reports/mirun_week2_review.md`.
