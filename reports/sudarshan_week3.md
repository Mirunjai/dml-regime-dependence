# Sudarshan Week 3 replication and reporting

Local review on 11 November 2026 from the `Sudarshan` checkout at `3e15336`.

| Week 3 deliverable | Evidence available |
| --- | --- |
| Replicate the pilot | The saved calendar-pilot replay matches all 128 field checks against Mirun's published table. This is a fresh comparison of saved summaries. The earlier replay used the pinned source and seeds below. |
| Figure and table set | Four 2×2 tables, a full-precision CSV with Monte Carlo errors and denominators, a paired robust comparison CSV, and 12 heatmaps from the calendar pilot. |
| Replicate the selected full-run subset | Pending the dated team selection, approved design, and original full-run manifest and raw records. |
| Real-data figures | Verified inclusion dates and counts for seven S&P 500 additions across two batches. Calm/turbulent return figures await the labelled daily-return or residual panel. |
| Reproducibility log | The command, input SHA-256 hashes, local versions, archived replay versions, Git state, and a hashed source ZIP are saved with the outputs. |

## Pilot comparison

The producer file `results/week2_mc.json` matches its blob at
`26e65f109d1aea552169bb57cbae894e4ea65e8c`. The recorded calendar replay
used seeds 20000–20019 in each of four scenarios, with `gamma` in {0, 1},
`tau` in {0, 1}, K=4, configured density 0.5, and five folds. The comparison
covers all four cells per scenario, with 112 numeric checks and 16 matching
undefined size fields. The largest numeric difference was about `3.1e-16`.
The comparison uses the existing software tolerance of `atol=1e-12` and
`rtol=1e-10`. See
[the prior replay and audit commands](../docs/week3_verification.md#methods-references).

The calendar pilot and legacy first-membership CR1 studies are separate.
The saved audit reports 120 small continuous-field differences in the legacy
tables, with all coverage rates matching. The original raw pilot archive and
runtime environment are needed for a record-level comparison. Gate 2 and Gate 3
remain pending in the [team design proposal](../configs/mirun_gate3.yaml).

## Regenerate the local reports

Run from the repository root in the project Python environment. Choose a fresh
output directory under `results/raw/` for each regeneration.

```bash
MPLBACKEND=Agg python -W error -m scripts.sudarshan_week3_report \
  --pilot results/week2_mc.json \
  --replay-summary results/tables/week3_mirun_verification.json \
  --events data/processed/sp500_events_verified.csv \
  --output results/raw/sudarshan_week3_regenerated
```

This command reads saved results and event metadata. A comparison discrepancy
is written to `pilot_comparison.csv` and returns exit code 2. At zero truth the
rejection figure shows empirical size. At nonzero truth it shows power. All
rate heatmaps use a common 0–1 scale and all width heatmaps share a width scale.
The event figure shows the verified sample of three September 2024 additions
and four March 2025 additions. The sample contains event dates and identities.

The local check used Python 3.13.0, NumPy 2.2.5, Matplotlib 3.10.3 and PyYAML
6.0.3 on macOS arm64. The earlier calendar replay used NumPy 2.3.5, SciPy
1.16.3 and scikit-learn 1.7.2. The reproduction log records these environments
separately. The reporting command performs no DML estimation.

All 365 local tests passed with warnings treated as errors. Two report runs
produced byte-identical CSV, Markdown and PNG files. The input and archived
source hashes also matched the reproducibility log.

## Integration review — Deeptanshu, 11 November

Reviewed source branch `40d7165` against main `7d9e834`. The merge had reverted
recent README and project-state sections; the integration restores those sections
and the current dependency documentation while retaining Sudarshan's reporting
additions. No DGP, DML or statistical metric formula is changed.

Independent Linux validation: 365 tests pass with warnings as errors. Two fresh
report invocations compare all 128 fields with zero discrepancies and generate
17 byte-identical CSV/Markdown/PNG artifacts (13 figures, three CSVs, one Markdown
report). Input hashes and the archived source ZIP hashes match the log. A generated
coverage heatmap was visually inspected. Raw evidence is retained in the primary
checkout under `results/raw/sudarshan_review_20261111/`.

This verifies reporting against saved evidence. It does not claim a new DML pilot
execution, selected full-run replication, or calm/turbulent return analysis. The
inclusion-event figure describes metadata only. Those outstanding scientific
inputs remain recorded in the current project state.
