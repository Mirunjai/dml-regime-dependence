
# Sudarshan — Experiment Infrastructure

## Scope

This package implements reusable infrastructure for the
DML Regime Dependence project.

It does not implement DML, GARCH, common-shock generation
or statistical inference formulas.

## Existing components reused

- configs/dgp/week1_skeleton.yaml
- configs/experiments/_template.yaml
- src/dgp/volatility.py
- src/dgp/regime_shocks.py
- src/evaluation/metrics.py

No existing scientific modules were modified.

## Week 1 implementation

### Reproducibility

File: src/infra/reproducibility.py

Features:
- YAML configuration loading
- Deterministic configuration fingerprints
- Git commit and dirty-worktree tracking
- Deterministic experiment run identifiers
- Independent RNG streams per component and replication
- Existing result-directory conventions
- Atomic JSON saving
- Reproducibility manifest generation

### Reporting

File: src/infra/reporting.py

Features:
- Markdown table formatting
- CSV table generation
- Generic diagnostic line plotting
- Input and shape validation

## Output conventions

Raw per-run artifacts:
results/raw/<run_id>/

Summary tables:
results/tables/

Diagnostic figures:
results/figures/

Raw output is excluded from Git through the existing
.gitignore.

## Installation

From the repository root:

python -m pip install -r requirements-dev.txt

## Verification

Run:

python -m pytest tests/test_infra_week1.py -v

python -m pytest tests/test_infra_reporting.py -v

python -m pytest -q -W error

## Reproducibility conditions

The same configuration, root seed, replication ID and
stream ID should reproduce the same NumPy RNG draws
under a compatible software environment.

Git revision, configuration contents and dirty-worktree
state are recorded for provenance.

A dirty worktree or an unavailable Git revision prevents
a strong claim of exact source-level reproducibility.

## Scientific limitations

These utilities do not validate the DGP or demonstrate
DML confidence-interval calibration.

The existing experiment template contains provisional
design values. Gate 3 approval is required before final
scientific experiments.

## Week 2 scope

Week 2 adds:
- A parallel experiment runner
- Resumable independent replications
- Raw per-replication four-cell results
- 2x2 statistical reporting templates
- Mock-data reproducibility tests




## Week 2 — Four-cell statistical reporting

### Purpose

Consume completed Monte Carlo replication JSON files and
produce four-cell ablation summaries.

The reporter does not implement DML or duplicate the
existing statistical evaluation formulas.

### Dependencies reused

- src/infra/experiment_runner.py
- src/infra/reproducibility.py
- src/infra/reporting.py
- src/evaluation/metrics.py

### Command

python -m src.infra.ablation_report \
  --run-dir results/raw/<run_id> \
  --repo-root .

### Generated outputs

- Four-cell summary CSV
- Four-cell Markdown table
- Machine-readable JSON summary
- Coverage heatmap
- Empirical size or power heatmap
- Mean CI width heatmap
- Paired random+robust minus grouped+robust comparisons

### Scientific interpretation

Coverage is evaluated against the known true effect.

Empirical size is defined only under a true zero effect.
Rejection of zero under a nonzero effect is power.

Each independent replication contributes at most one
observation per cell.

The two robust-variance cells are compared by aligned
replication ID, using the existing paired-difference API.

### Failure handling

All planned replication records must be present.

Strict reporting raises on failed estimator cells.

Explicit --failure-policy report provides conditional-on-
success statistics, failure counts and all-attempted
coverage bounds.

Failed attempts cannot be silently dropped.

### Research limitations

Mock experiments test infrastructure functionality only.

They cannot establish DML confidence-interval calibration,
Gate 2 approval, or the benefit of regime-aware cross-fitting.

Final conclusions require the integrated DGP, actual DML
estimators and team-approved Gate 3 experimental design.

### Verification

python -m pytest tests/test_infra_ablation_report.py -v

python -m pytest -q -W error
