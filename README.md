# DML Regime Dependence

**When Does Causal ML Fail in Financial Event Studies?**
Testing DML confidence-interval calibration under dense regime-level common shocks.
ADA Finance Track: Mirun (lead), Deeptanshu, Preksha, Sudarshan.

## Final research release

The registered final study contains **78 scenarios, 43,200 complete four-cell
blocks and 172,800 primary intervals**, with zero failed or missing cells.
All 24 independent-control cells pass the frozen calibration/bias criteria.
CR2 improves focal coverage; grouped folds add no material benefit under the
prespecified paired rule. Few-regime undercoverage remains a reported finding.

The real-data illustration now uses **six firms over 1,511 common trading dates**
(2016–2021), with 9,066 returns, strictly prior VIX labels, joint calendar-block
uncertainty and prior-only market residuals. The fresh seven-event classical
benchmark uses the actual S&P 500 index and an SEC-verified ADS/BFH crosswalk.
Original missing archives remain unauthenticated; fresh evidence is separately
saved and audited. **439 tests pass**, and the submission notebook contains
**48 explained code stages**. See the [final technical review](docs/final_validation/FINAL_RESULTS_AND_TECHNICAL_REVIEW.md)
and [reproduction commands](submission/README.md). Source, registered configs and
small summary tables/figures are versioned; the sibling submission folder and
raw archives stay outside Git. Older sections below describe the component and
historical releases.

## Research objective

The core experiment is random/grouped cross-fitting × naive/robust variance.
The central comparison is random+robust versus grouped+robust. Coverage of 95%
intervals is primary; empirical size under a zero effect is the key diagnostic.
Similar performance of the robust cells is a valid result. Width and power alone
cannot establish inferential benefit.

Classical event studies provide a secondary contextual benchmark. Synthetic
Control is excluded by the final-week plan and the user's explicit instruction.
S&P 500 inclusions provide a qualitative real-data check, not coverage evidence.
The project introduces no new estimator, variance formula, or theorem.

## Available components

The shared baseline contains Preksha's Week 1 regime generator (`src/dgp/regime_shocks.py`),
its demo/tests, and Deeptanshu's standalone Week 1/2 package:

- Gaussian firm-level GARCH(1,1), fixed intended unconditional variance, explicit
  NumPy RNG, burn-in, standard-deviation/innovation outputs shaped `(firm, time)`.
- Persistence/variance/moment/pathology diagnostics, squared-return ACFs and plots,
  longer-burn and series-length checks, and component runtime measurements.
- Volatility/regime separation checks using exact pinned teammate source, full
  regime-process randomization, and a deliberately dependent positive control.
- Coverage, null size, power, MCSE, failure denominators, Wilson intervals, paired
  binary differences, replication-budget arithmetic, and independent CSV recomputation.

Read the [validation report](reports/deeptanshu_week1_week2.md),
[project state](docs/PROJECT_STATE.md), and
[decisions and protocol draft](docs/DECISIONS.md). The report distinguishes tested
component behavior from team gate approval. Sudarshan's Week 1/2 infrastructure
adds YAML configuration, independent RNG streams, atomic replication files,
parallel/resumable mock runs, and four-cell reports using the existing metrics.
See [the infrastructure guide](docs/Sudarshan_INFRA.md). The mock engine has no
integrated DGP or DML estimator.

## Preksha's Week 2 prototypes

The reviewed delivery adds single-membership pair-density and treatment/exposure
diagnostics, a descriptive market-model event-study prototype and a source-checked
seven-event inclusion sample. Run `python -m src.benchmarks.event_study` for the
toy example. The [integration review](reports/preksha_week2_review.md) records
corrections, assumptions and commands. The sample is not a labelled return panel;
these prototypes do not establish final benchmark or Gate 2/3 results.

## Week 3 verification package

Deeptanshu's independent saved-results verifier, numerical monitoring snapshots,
per-cell audit checks and qualitative calm/turbulent dependence diagnostics are
included in the Week 3 delivery. Start with the
[contract and commands](docs/week3_verification.md). Run the complete **mock**
example with:

```bash
python examples/week3_mock_review.py --output results/raw/week3_software_example
```

The independent review reconstructed 5,360 interval rows from the existing pilot
and ablation settings; all 76 reported coverage rates match. Small continuous
legacy discrepancies remain flagged. The actual calendar runner now has a strict
raw-file adapter and monitoring support. See the [Week 3 report](reports/deeptanshu_week3.md).
This historical Week 3 package preceded the new final design, robustness runs
and labelled panel documented in the final research release above.

## Sudarshan’s Week 3 reporting

The saved calendar-pilot comparison, four-cell tables/heatmaps, event-timing
figure and reproducibility log can be regenerated with
`python -m scripts.sudarshan_week3_report --help`. See
[his reporting handoff](reports/sudarshan_week3.md). This compares saved summaries;
it does not replace an independent raw-result replication or real-data analysis.

## Preksha’s Week 3 benchmark tools

Dated event-study and Synthetic Control helpers, pre-announcement VIX event labels,
source audits and acquisition tools are integrated. See the
[review and remaining data gaps](reports/preksha_week3_review.md). Install optional
acquisition/calendar dependencies with `python -m pip install -r requirements-data.txt`.
The saved historical CARs remain unauthenticated without their original inputs.
The final release executes fresh classical calculations and daily labelled-panel
diagnostics; SCM stays excluded.

## Historical final-week exploratory release

The 12 November review completes a registered 16-scenario, 200-world-per-scenario
CPU Kaggle audit: **3,200 complete four-cell blocks, 12,800 interval records and
zero failed/missing cells**. The independent-control reference robust coverage is
.870/.875, so the final-week plan's exploratory submission path is retained.
See the [decision memo](docs/final_review/DECISIONS_20261112.md),
[independent audit](docs/final_review/INDEPENDENT_AUDIT_20261112.md) and
[scoped literature verification](docs/final_review/LITERATURE_VERIFICATION.md).
That frozen source passed 427 software tests; its 38 notebook code cells passed in a
fresh Kaggle CPU kernel with the declared frozen bundle. These are reproducibility
and exploratory findings, not production-gate approval. Build inputs/commands are
in [submission/README.md](submission/README.md). No provider prices are redistributed.

## Installation

Use Python 3.11 or newer (tested locally with 3.13.13). No GPU is required.
From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Standalone runtime dependencies are NumPy, Matplotlib and PyYAML. The development
installation also includes SciPy/scikit-learn for Mirun's research layer and pytest. The
simulation and metric APIs themselves import NumPy only. Dependency ranges are in
`requirements.txt`; actual versions and source hashes are recorded with each run.
The infrastructure integration passed 164 tests with warnings as errors in a
fresh environment installed from these requirements (Python 3.13.13, NumPy 2.5.4,
Matplotlib 3.11.2, PyYAML 6.0.3, pytest 9.2.0). Earlier component evidence retains
its original software versions. Native Windows/macOS execution is unverified.

## Quickstart

```bash
# Week 1 standalone example: prints a small numerical summary
python -m src.dgp.volatility --persistence 0.9 --n-firms 50 --n-periods 500

# Known-outcome mock intervals: exactly 95% coverage and 5% null rejection
python -m src.evaluation.metrics

# Fast complete pipeline smoke: creates plots, raw summaries and provenance
python -m src.dgp.validate_volatility --quick --run-name smoke

# Substantive component validation, including the actual pinned regime source
python -m src.dgp.validate_volatility --run-name week1_week2_validation

# A separate recorded root seed for corroboration
python -m src.dgp.validate_volatility \
  --config configs/experiments/deeptanshu_corroboration.json \
  --run-name week1_week2_corroboration
```

For a software-only four-cell check:

```bash
python -m src.infra.experiment_runner \
  --config configs/experiments/sudarshan_mock.yaml --workers 2
# Copy the run ID printed above:
python -m src.infra.ablation_report --run-dir results/raw/<run_id>
```

The mock runner resumes missing replications without retrying saved failures.
Reporting raises on failed cells unless `--failure-policy report` is explicitly
selected. These outputs test infrastructure; they do not measure DML performance.

Run names protect existing results; choose another name or explicitly use
`--overwrite` for generated files. `--output-root` changes the output location.
Overwrite removes this harness's old named outputs, including optional evidence
that the replacement run skips or cannot generate; unrelated user files remain.
The pipeline returns exit code 2 for numerical failures or blocked/incomplete
independence checks. A missing teammate Git object does not prevent standalone
GARCH or metric work: `--skip-independence` explicitly records that check as skipped.

The Week 1 regime generator was merged through PR #2. The diagnostic now reads
its source from the current committed revision (`regime_ref: HEAD`), resolves that
reference to a full commit SHA, and records the exact SHA, source hash and snapshot.
This works in a fresh main-only clone without retaining an old feature-branch
commit. Uncommitted regime edits are deliberately excluded. Historical validation
reports retain their original pinned source at `17b42c0`. Neither merging the
component nor the one-period/one-window diagnostic alignment establishes the
team's integrated date/event-window mapping or Gate 2/3 approval.

## APIs and conventions

```python
from numpy.random import default_rng
from src.dgp.volatility import simulate_volatility
from src.evaluation.metrics import summarize_intervals, paired_binary_difference

sigma, eps = simulate_volatility(50, 500, 0.9, default_rng(42))
idiosyncratic_returns = sigma * eps  # Never feed regime-contaminated returns back.

summary = summarize_intervals([-1, 0.1], [1, 1], truth=0.0,
                              expected_replications=2)
contrast = paired_binary_difference(
    {"rep0": True, "rep1": False}, {"rep1": True, "rep0": True})
```

`sigma` is conditional standard deviation, `eps` is standardized N(0,1), and
`sigma**2` is conditional variance. Persistence rho maps to alpha=.1*rho,
beta=rho-alpha, omega=v*(1-rho), with configurable `arch_share` and intended
variance v. This changes higher moments as well as serial decay. Finite variance
requires rho<1; the Gaussian fourth-moment factor rho²+2alpha² must be below one
for population squared-return ACFs. The simulator allows finite-variance processes
without fourth moments, while diagnostics mark their population ACF unavailable.
The implementation uses compensated coefficient remainders for the intercept
and a stable moment margin to avoid cancellation close to the unit boundary.

Intervals include endpoints. Failed runs raise by default. Explicit
`failure_policy="report"` requires boolean success flags and returns conditional
metrics, counts, and coverage bounds; it never treats failures as null rejections.
Materialize all planned runs, including failures. `expected_replications` detects
omitted rows. Paired maps must include every planned ID, using None for failures.
Simulation truth is for evaluation; it must not enter nuisance fitting.

Recompute metrics directly from raw interval CSV (no DML/runner needed):

```bash
python -m src.evaluation.metrics \
  --input results/raw/week1_week2_validation/mock_intervals.csv \
  --truth 0 --expected-replications 100
```

CSV requires `lower,upper`, with optional `replication,cell,truth` and either
`success=true/false` or `status=ok/failed`. Select `--cell` for a multi-cell file.
Use explicit `--failure-policy report` to inspect failures; invalid successful
intervals always raise. These mock results test arithmetic, not DML calibration.

## Validation and reproducibility

```bash
python -m pytest -q -W error
python scripts/check_acf_length.py

# Optional official-source parity check; reference dependencies must be available
python scripts/check_arch_reference.py --source ../references/arch \
  --output results/tables/arch_reference.json
```

The optional reference check uses the official API and an in-process version
metadata shim for the unbuilt clone, with its Python fallback. It changes no
reference source. It needs SciPy, pandas, and statsmodels, which are not required
for the standalone components.

Outputs are small summaries/figures under `results/tables` and `results/figures`.
Ignored `results/raw/<run>/` contains per-replication summaries, extreme-return
examples, selected series, mock intervals, seeds, software/config metadata, own
source snapshots, and the exact regime source snapshot. Complete simulated panels
are not retained. Addressed SeedSequence streams are independent of loop order;
settings deliberately reuse innovations for paired persistence/burn-in checks.
Exact reproduction across operating systems/hardware has not been established.

## Scope and remaining team decisions

The supplied plans report Gate 1 as locked. A source-grounded navigation summary
is available in `docs/gate1_specification.md`; the supplied proposal/weekly files
remain the source of the specification. No Gate 2/3 production approval is claimed.
All diagnostic settings, return flags, budgets and materiality thresholds are
proposals, not final experimental design. Team review must settle the frozen
regime version, time/window mapping, robust variance, grid, budget and benchmark
comparability. Other teammates retain their scientific tracks.

See [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for workflow.
Commits and pushes require explicit user authorization. No project license has
been selected; reference licenses remain separate.

This reviewed Week 4 package incorporates Mirun PR #14/#15 additions with review fixes, the exploratory audit pipeline and the 38-stage notebook source. See [the integration note](docs/final_review/WEEK4_INTEGRATION_20261112.md), [the earlier proposal/weekly audit](docs/final_review/PROJECT_SCOPE_AUDIT_20261112.md) and [the authorized branch cleanup record](docs/final_review/BRANCH_CLEANUP_PROPOSAL_20261112.md). The generated submission folder and raw data are distributed separately; production gates remain unapproved.
