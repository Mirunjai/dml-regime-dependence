
# Sudarshan — Experiment Infrastructure

## Scope

This package implements reusable infrastructure for the
DML Regime Dependence project.

It does not implement DML, GARCH, common-shock generation
or statistical inference formulas.

## Existing contracts reused

- configs/dgp/week1_skeleton.yaml
- configs/experiments/_template.yaml
- src/evaluation/metrics.py

The mock engine does not call the GARCH or regime generators. It uses artificial
estimates and fixed interval widths to exercise the four-cell data contract.
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

## Integration review: 1 November 2026

The initial branch at `c582846` passed 151 combined tests. Review added 13
regression cases; the combined suite now passes **164 tests**, with warnings
treated as errors, in a fresh requirements-only environment: Python 3.13.13,
NumPy 2.5.4, Matplotlib 3.11.2, PyYAML 6.0.3, pytest 9.2.0.

Review fixes:

- Declare PyYAML as a runtime dependency; record Python/library versions and
  the RNG bit generator in each manifest. Resume rejects a changed environment.
- Use one saved-record validator for resume and reporting, including truth,
  component seed addresses, cell identities and interval validation.
- Reject altered manifest configuration and RNG metadata on resume.
- Resolve output paths within the project and validate run IDs as filename tokens.
- Hold a per-run OS lock while the parent controls execution; competing parents
  fail before modifying the manifest or replications. The persistent
  `.runner.lock` file is expected and is reusable after process exit.
- Detect source edits during execution and invalidate reporting for that run.
  Treat source as frozen while a run executes; a change followed by restoration
  between checks cannot be detected.
- Label generated charts and Markdown as mock infrastructure checks. Remove
  obsolete heatmaps when a replacement report has no successful cells.
- Include the JSON output location before writing the JSON report, so its
  recorded outputs agree with the returned report.

The locking APIs follow Python's
[Unix flock documentation](https://docs.python.org/3/library/fcntl.html#fcntl.flock)
and [Windows locking documentation](https://docs.python.org/3/library/msvcrt.html#msvcrt.locking).
Linux process locking and explicit multiprocessing spawn were tested. Native
Windows/macOS execution and network filesystem locking remain unverified.

A clean-source CLI run of 12 mock replications at source commit `22cb502d`
was resumed with three workers after two replication files were removed. The
regenerated files matched the originals byte for byte. Coverage, size, MCSE and
mean interval widths were independently recomputed from all raw records. The
reviewed small tables and labelled heatmaps replace the original sample outputs;
raw records, manifest and review checks remain under ignored `results/raw/`.

Sample rates of zero or one have a zero plug-in MCSE; this does not mean zero
uncertainty. The sample has only 12 artificial replications and cannot support a
scientific calibration claim. Final experiment budgets and inferential choices
remain team decisions. This package completes the mock infrastructure milestone,
not actual-estimator runtime profiling or final DML experiment integration.
