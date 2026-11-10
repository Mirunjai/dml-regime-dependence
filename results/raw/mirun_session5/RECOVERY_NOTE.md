# Session 5 raw-output recovery note

The prior Claude session generated 1,000 per-replication control records under `results/raw/mirun_session5/controls/` (five conditions x 200 replications), plus `calibration.json`. Those files were not included in the uploaded Session 4 raw archive (`mirun_raw_outputs.tar.gz`), which contains only Sessions 2–4. They are deliberately not fabricated here.

The rounded summary printed in the Session 5 transcript has been reconstructed into `results/tables/mirun_session5_controls.json`, with an explicit provenance field. To regenerate a fresh raw run, use:

```bash
OPENBLAS_NUM_THREADS=1 PYTHONPATH=. python scripts/mirun_session5_checks.py run --out results/raw/mirun_session5/controls --reps 200 --budget-seconds 225
# Repeat with a larger budget until complete=true; the runner resumes and does not overwrite existing rep files.
python scripts/mirun_session5_checks.py summarize --dir results/raw/mirun_session5/controls --out results/tables/mirun_session5_controls_reproduced.json
```

Do not replace the transcript-reconstructed summary until a fresh run is completed and checked.
