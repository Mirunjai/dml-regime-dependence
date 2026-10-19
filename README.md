# DML Regime Dependence

**When Does Causal ML Fail in Financial Event Studies?**
Testing Double Machine Learning (DML) confidence-interval calibration under dense, regime-level common-shock dependence in financial event studies.

ADA (Advanced Data Analytics) undergraduate research project — Team: Mirun (lead), Deeptanshu, Preksha, Sudarshan.

> [!NOTE]
> This repo implements an already-locked research specification (Gate 1). It does not redesign the research question. See [`docs/gate1_specification.md`](docs/gate1_specification.md) for the full, authoritative spec.

## What this project does

Financial events (e.g. S&P 500 inclusions) often cluster inside the same market regime, so the firms involved share a common shock and their outcomes become dependent. This project tests, in a controlled Monte Carlo simulation with a known true effect, whether DML's 95% confidence intervals stay calibrated under that dependence — and specifically whether a dependence-robust variance estimator alone is enough, or whether regime-aware (grouped) cross-fitting adds inferential benefit beyond that.

The core experiment is a 2×2 ablation (random vs. grouped cross-fitting × naive vs. robust variance), evaluated primarily on 95% CI coverage. Classical event-study and Synthetic Control estimators are included as secondary, contextual benchmarks, and S&P 500 index-inclusion events provide a qualitative (not coverage) real-data check.

This project does **not** introduce a new estimator, variance formula, or cross-fitting theorem, and makes no general claim that DML is unreliable in finance.

## Repository structure

```
dml-regime-dependence/
├── src/
│   ├── dgp/            # data-generating process
│   │   ├── core.py             # DGP skeleton / integration        (Mirun)
│   │   ├── volatility.py       # GARCH-style volatility module     (Deeptanshu)
│   │   └── regime_shocks.py    # regime/common-shock module        (Preksha)
│   ├── dml/             # DML estimator, cross-fitting, variance   (Mirun)
│   ├── benchmarks/      # classical event study, Synthetic Control (Preksha)
│   ├── real_data/       # S&P 500 loading + regime labeling        (Preksha)
│   └── infra/           # seeding, experiment runner, plots, tables (Sudarshan)
├── notebooks/            # exploratory and weekly deliverable notebooks
├── configs/              # experiment and DGP configuration files
├── tests/                # unit tests for src/
├── results/
│   ├── figures/          # tracked
│   ├── tables/           # tracked
│   └── raw/              # gitignored — regenerate from configs + seed
├── reports/              # gate validation memos, final report drafts
└── docs/                 # locked Gate 1 spec, team tracker references
```

Each `src/` subfolder maps to one person's independent track, so modules can be built and tested in parallel without blocking anyone — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Installation

```bash
git clone https://github.com/<org-or-username>/dml-regime-dependence.git
cd dml-regime-dependence
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> [!IMPORTANT]
> Replace the clone URL once the repo is created, and keep `requirements.txt` up to date as modules add dependencies (e.g. `arch` for GARCH, `scikit-learn`, `doubleml`).

## Quickstart

Run a module's self-contained example — nobody needs another teammate's code to do this:

```bash
# Deeptanshu's volatility module on its own
python -m src.dgp.volatility --persistence 0.9 --n-firms 50 --n-periods 500

# Preksha's regime-shock module on its own
python -m src.dgp.regime_shocks --density 0.3 --n-regimes 5

# Mirun's DGP skeleton (uses placeholders until the above are wired in)
python -m src.dgp.core --config configs/dgp/week1_skeleton.yaml
```

Each command writes diagnostic plots to `results/figures/` and a short run summary to `results/tables/`.

## Reproducing an experiment

All experiments run through `src/infra/experiment_runner.py` with a config file and a seed, so any teammate can reproduce any result:

```bash
python -m src.infra.experiment_runner --config configs/experiments/<name>.yaml --seed 0
```

Raw simulation output goes to `results/raw/` (gitignored); regenerate it rather than committing it.

## Current status

**Gate 1 (research question / specification) is locked.** The project is in **Gate 2** (DGP construction and validation). See the team tracker (linked in `docs/`) for the full 7-week plan, gate criteria, and weekly deliverables.

| Gate | Focus | Status |
|------|-------|--------|
| 1 | Research question / specification | ✅ Locked |
| 2 | DGP construction and validation | 🔄 In progress |
| 3 | Experimental design lock | ⬜ Not started |
| 4 | Monte Carlo / DML experiment | ⬜ Not started |
| 5 | Contextual benchmark methods | ⬜ Not started |
| 6 | S&P 500 real-data validation | ⬜ Not started |
| 7 | Final analysis and reporting | ⬜ Not started |

## Testing

```bash
pytest tests/
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch naming, the PR/review process, and the weekly workflow.

## License

<!-- Add a license if the course or institution requires one, or leave private with no license (all rights reserved by default). -->
TBD — confirm with course staff whether a license is required for submission.
