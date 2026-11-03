# Project A — Week 2 completion patch

## What this patch does

This is an additive integration layer. It preserves the exact Week 2 submission
under `research/week2_completion/original/` and adds a testable implementation
under `research/week2_completion/`.

- `gamma=0` and `gamma>0` are run as an explicit treatment-assignment ablation.
  Neither is selected by looking at coverage.
- Every event stores the complete set of regime IDs touched by its outcome
  window. No event is silently assigned only to its first regime.
- The multiway score sandwich uses inclusion-exclusion over all nonempty
  intersections of membership sets. This estimates covariance for pairs of
  events sharing one or more regimes.
- Grouped folds use connected components of the event-regime dependence graph.
  If there are too few independent components to make the requested folds, the
  run fails explicitly. This is important: overlapping windows can connect
  many events into one component, making five regime-pure folds impossible.
- The Gate 2 runner records overlap density, pair density, multiple-regime
  windows, treatment/shock association, return diagnostics and a paired gamma
  ablation.
- The Monte Carlo runner supports tau=1 coverage and tau=0 empirical size,
  records failed replications, and reports Monte Carlo standard errors.

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

## Install

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-week2.txt
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
  --out results/week2_mc.json
```

Outputs:
- `results/week2_gate2.json`
- `results/week2_mc.json`

Start with 20 reps to test the pipeline. Only after the team locks the design
should the replication count be increased. Grouped-fold failures are retained
and reported; do not suppress them or interpret a failed cell as a successful
result.

## Apply patch on Windows

1. Commit or stash local changes first.
2. Copy the patch file to the repository root.
3. Check it:
   ```powershell
   git apply --check .\Project_A_Week2_Completion.patch
   ```
4. Apply it:
   ```powershell
   git apply .\Project_A_Week2_Completion.patch
   ```
5. Verify:
   ```powershell
   git status --short
   python -m pytest -q
   ```
6. Run the pilot command above.

The patch is additive and does not overwrite the canonical `src/dgp` modules.
