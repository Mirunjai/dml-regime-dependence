# Final review build

This directory contains the report source and reproducible release-building code.
Outputs belong in the sibling `ADA PROJECT DELIVERABLES` folder, not in Git.
The release is Plan B / EXPLORATORY; no production gate or teammate signature is
inferred from a successful build. Do not distribute the local provider price data.

The registered Monte Carlo plan is
`configs/experiments/final-review/exploratory_validation_20261112.json`.
CPU kernels and collector metadata/notebooks are in `compute-tools/`.

After downloading and extracting the two frozen Kaggle validation archives:

```bash
python -m scripts.audit_final_validation \
  --plan configs/experiments/final-review/exploratory_validation_20261112.json \
  --run-dir results/raw/final_validation_frozen/validation_tau0 \
  --run-dir results/raw/final_validation_frozen/validation_tau1 \
  --output results/raw/final_validation_audit_20261112
python -m scripts.final_real_data_audit \
  --config configs/experiments/final-review/daily_panel_audit_20261112.json \
  --output results/raw/final_daily_panel_20261112
python -m scripts.build_final_results_assets \
  --audit results/raw/final_validation_audit_20261112/audit.json \
  --daily results/raw/final_daily_panel_20261112/audit.json \
  --output results/raw/final_submission_assets_20261112
```

Each audit output directory is write-once; use a fresh name for another review.
The daily input script requires the exact local, non-redistributed saved inputs.
A packaged notebook regenerates the Monte Carlo audit/tables/figures and displays
frozen real-data aggregates, explicitly distinguishing their raw-input limitation.

Keep the supplied one-pager template structure. Team name/sections are blank at
the user's request. Course PPT template, all-member recordings, actual Drive
sharing and Google Form confirmation are human release controls.

The current notebook builder uses submission/notebook_sections.py: 38 executable stages, each preceded by a short concept/what/why explanation. Run build_notebook.py, attach/version its checksummed bundle, then prepare_notebook_clean_run.py and execute the wrapper on Kaggle. Copy the executed notebook and matching clean_run.json only after source-digest verification. Rebuilding source requires a new clean run; an older PASS must not be reused. No video build is part of this audit.
