# DML Regime Dependence

**When Does Causal ML Fail in Financial Event Studies?**
Testing DML confidence-interval calibration under dense regime-level common shocks.
ADA Finance Track: Mirun (lead), Deeptanshu, Preksha, Sudarshan.

## Research objective

The core experiment is random/grouped cross-fitting × naive/robust variance.
The central comparison is random+robust versus grouped+robust. Coverage of 95%
intervals is primary; empirical size under a zero effect is the key diagnostic.
Similar performance of the robust cells is a valid result. Width and power alone
cannot establish inferential benefit.

Classical event studies and Synthetic Control are secondary contextual benchmarks.
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

## Installation

Use Python 3.11 or newer (tested locally with 3.13.13). No GPU is required.
From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Runtime dependencies are NumPy, Matplotlib and PyYAML; pytest is for development. The
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

The supplied plans report Gate 1 as locked, but the authoritative
`docs/gate1_specification.md` is absent. No Gate 2/3 approval memo was found.
All diagnostic settings, return flags, budgets and materiality thresholds are
proposals, not final experimental design. Team review must settle the frozen
regime version, time/window mapping, robust variance, grid, budget and benchmark
comparability. Other teammates retain their scientific tracks.

See [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for workflow.
Commits and pushes require explicit user authorization. No project license has
been selected; reference licenses remain separate.
