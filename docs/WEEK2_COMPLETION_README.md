# Project A — Week 2 completion patch

## What this patch does

This is an experimental calendar-time comparison layer. The original scripts and
summaries are tracked under `research/week2_mirun/`; the active comparison is
`research/week2_completion/`. The ignored `original/` path is not distributed.
Read `reports/mirun_week2_review.md` for the integration review and model caveats.

- `gamma=0` and `gamma>0` are run as an explicit treatment-assignment ablation.
  Neither is selected by looking at coverage.
- Every event stores the complete set of regime IDs touched by its outcome
  window. No event is silently assigned only to its first regime.
- The regime-overlap score sandwich counts pairs sharing any regime once. A
  direct pair accumulation evaluates the same inclusion-exclusion formula without
  exponentially enumerating subsets. Negative/nonfinite meat is an explicit
  variance-cell failure, not a reason to discard the naive cell.
- Grouped folds use connected components of the event-regime dependence graph.
  If there are too few independent components to make the requested folds, the
  grouped cells fail explicitly; successful random cells remain saved. This is important: overlapping windows can connect
  many events into one component, making five regime-pure folds impossible.
- The Gate 2 runner records overlap density, pair density, multiple-regime
  windows, treatment/shock association, return diagnostics and a paired gamma
  ablation.
- The Monte Carlo runner supports tau=1 coverage and tau=0 empirical size,
  records all attempted cells (including partial failures), and reports Monte
  Carlo standard errors, denominators, success conditioning and coverage bounds.

## Scientific interpretation and limits

This is an implementation patch, not a Gate 2 or Gate 3 pass decision.

1. The gamma comparison changes treatment assignment by adding an independent
   regime-level latent effect. The team must decide whether that mechanism is
   substantively appropriate before freezing it.
2. The multiway sandwich is an asymptotic estimator. It does not solve the
   few-independent-regimes problem automatically and is not a CR2/Satterthwaite
   correction. Its finite-sample calibration must be judged by the Monte Carlo
   size and coverage experiments.
3. The grouped-fold dependence graph may have very few connected components.
   The code intentionally refuses an invalid fold split rather than pretending
   that assigning an event to its first regime removes all cross-fold leakage.
4. The current canonical repository regime module treats each index as an
   event-window index with a single regime label. It is not semantically
   interchangeable with the contiguous calendar-time regime process in this
   patch. The original calendar-time model is preserved explicitly.
5. Correlations are diagnostics, not proof of statistical independence.
6. Pilot replication counts are not final sample-size decisions.
7. Grouping and covariance here cover regime memberships. Shared calendar factors
   are not automatically removed; raw fold diagnostics expose cross-fold links.
8. This DGP uses fixed alpha=.10, unlike the canonical GARCH default alpha=.1*rho.
   Burn-in/draw order also differ. The family remains explicit; canonical source
   is unchanged.

## Install

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Test

```powershell
python -m pytest -q
```

## Run Gate 2 diagnostics and a small gamma/tau pilot

```powershell
python -m research.week2_completion.run_week2 `
  --reps 20 `
  --gamma-values 0 1 `
  --tau-values 1 0 `
  --density 0.50 `
  --K 4 `
  --folds 5 `
  --out results/raw/week2_exploratory_01/run.json
```

Outputs:
- `results/raw/week2_exploratory_01/manifest.json`: full CLI/source/environment metadata
- `results/raw/week2_exploratory_01/gate2.json`: diagnostic config and evidence
- `results/raw/week2_exploratory_01/run.json`: summaries and all attempted records
- per-scenario `config.json` and `rep_XXXXXX.json`: atomic incremental raw outputs

Choose a new output directory on each run. Existing result directories are not
overwritten. `--gate2-seeds` controls the number of diagnostic seeds (default 50);
all supplied dimensions and starting seeds are recorded. A source change during
execution creates an invalidation marker and returns an error. This runner does
not silently resume/retry failed attempts. Exit 2 signals failed cells for review.
Partial raw evidence survives interruption even if the final summary is absent.

Start with 20 reps to test the pipeline. Only after the team locks the design
should the replication count be increased. Grouped-fold failures are retained
and reported; do not suppress them or interpret a failed cell as a successful
result.

## Review and handoff

The code is already in the repository; do not apply an external patch over it.
The raw schema is documented by the JSON records and includes seed stream
addresses, config, estimator settings, folds, interval bounds and failure reasons.
No DGP truth enters nuisance fitting. Standard errors/intervals remain exploratory
until the team specifies the primary model and approves its design.
