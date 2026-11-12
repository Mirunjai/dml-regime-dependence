# Mirun execution baseline (session 1)

Status: **partial reconnaissance.** Items marked NOT YET INSPECTED were read only
through repo docs, not source. Nothing here is a gate approval.

## Environment and provenance
- Source: `dml-regime-dependence.bundle` (uploaded). Base commit `b558156` (main, PR #9). Working branch `mirun/execution-session1` (local only, nothing committed).
- Bundle refs: `main`, and remote-tracking `Sudarshan` (3 commits, unmerged: `0f11603`), `preksha/regime-shock-module` (5 unmerged commits, `bfe19cb`), `preksha/week2-validation` (2 unmerged, `8144aba`), `mirun/week2-consolidated-completion` (`a84b548`, fully merged). Open/closed PR state is not in a bundle; PR numbers come from commit messages and `docs/PROJECT_STATE.md` only.
- Python 3.12.3, numpy 2.5.4, scipy 1.18.1, sklearn 1.9.1, pandas 3.0.6. pytest was absent; installed into a project-local venv (`/home/claude/venv`, system-site-packages), no global change.
- **Executed:** `python -W error -m pytest -q` -> **317 passed** (13.4 s) on `b558156`. This matches the 317 claimed in `docs/PROJECT_STATE.md`.

## Inventory (implemented / executed / verified)
| Component | Files | Evidence seen this session |
|---|---|---|
| Canonical GARCH | `src/dgp/volatility.py` | Source read. Arch-share mapping, burn_in=1000, per-time-step draws. Tests pass. |
| Canonical event-index regimes | `src/dgp/regime_shocks.py` | Source read. Random event->regime assignment, unit-variance shocks, exactly K regimes. |
| Mirun old (Week 2) DGP/DML | `research/week2_mirun/` | Source read (`dgp.py` diff, `dml.py`). Fixed alpha=.10, burn=200, calendar blocks, first-membership clusters, CR1 by first regime. |
| Mirun new DGP/DML | `research/week2_completion/` | `dgp.py`, `dml.py`, `run_week2.py` read. Fixed alpha, burn=500, calendar blocks, full-membership, overlap-sandwich, per-cell failure handling, atomic raw attempts. `validation.py` NOT YET INSPECTED. |
| Metrics / verification / audits | `src/evaluation/*` | NOT YET INSPECTED (tests pass). Used by runner: `summarize_intervals`. |
| Infra runner | `src/infra/*` | NOT YET INSPECTED. Docs say **mock-only**; `run_week2.py` does not use it. |
| Real data | `data/processed/sp500_events_verified.csv`, `src/real_data/*` | CSV is 1.7 KB (event list). **No daily-return panel exists in the repo.** |
| Saved results | `results/week2_mc.json` (4 runs, 20 reps), `research/week2_mirun/results/mc_*` (200 reps) | Structure read. Not independently reproduced yet. |

## Observed facts that matter
1. Two Mirun DML variants are **different estimators**: old = CR1 (G/(G-1)) over first-membership clusters, unexposed events as singletons; new = overlap sandwich over full membership, no small-sample factor, can return negative meat -> recorded as failed cell. Result files from the two must not be pooled.
2. Neither Mirun GARCH equals the canonical one (alpha mapping, burn, draw order). `src/` still has no code path using the canonical GARCH in a DML run.
3. Old 200-rep ablation (`mc_gamma_ablation_200reps.json`): with gamma=0, naive coverage is .945-.97 in every cell, i.e. **no miscalibration to fix**; with gamma=1, K=4: random/naive .82, random/robust .905, grouped/naive .73, grouped/robust .865 (MCSE .02-.03). Grouped was *not* better in this pilot; sd(tau-hat) is larger under grouped (.51 vs .43). Cause not established; this is exploratory and uses the old estimator.
4. Calendar DGP structure (`results/tables/mirun_dgp_component_scan.json`, new, from `scripts/mirun_dgp_scan.py`, 100 seeds): multi-regime events are <=5% (essentially 0 at density<=.5), so full- vs first-membership matters little at those settings. Exposed-event fraction is **not** equal to `density` and varies with K at fixed density (density .1: .13 at K=2 vs .35 at K=16). At density .75, K=16 there are ~28 grouped-fold components with the largest ~87 events: grouped 5-fold is feasible but unbalanced.
5. gamma>0 (regime-level random effect on treatment propensity) is what makes naive SE wrong; at gamma=0 regime shocks in Y alone do not break naive inference in the pilot. Whether gamma belongs in the primary DGP is a team decision (not made).
6. `docs/PROJECT_STATE.md`: no approved Gate 2/3 memo, no frozen daily panel, no original full-run raw archive.

## Blocked / dependencies
- Team decision: primary DGP, variance estimator, gamma, grid, replication budget (Gate 2/3).
- Preksha: labelled daily return/residual panel + regime labels (data contract still to be written).
- Deeptanshu: independent verification of any new estimator/runner changes.

## Not yet done (next session)
Inspect `validation.py`, `src/evaluation/*`, `src/infra/*`, `src/real_data/*`, `src/benchmarks/*`, saved Gate 2 JSON; reproduce `week2_mc.json` from seeds; write the other four reports.

## Session 2 update (executed/verified)
- Restoration: bundle cloned (only `main` + `origin/*`; base `b558156` verified); branch `mirun/execution-session1` created fresh; `mirun-progress.patch` reverse-check failed (not applied), forward-check passed, applied; 5 files byte-identical to checkpoint. Note: the bundle holds only `origin/main`, not the teammate branches Session 1 listed.
- Baseline re-run: `python -W error -m pytest -q` -> **317 passed** (14.4 s), matching the historical claim. Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.1.1, pytest 9.2.0, PyYAML 6.0.3, matplotlib 3.11.2.
- Reconnaissance completed by reading source: `validation.py`, `matched_density.py`, `src/infra/experiment_runner.py` (engine must be `mock`; **rejects any other engine**, so the primary run needs a new engine hook), `src/evaluation/*` (metrics, verification, week3/mirun audits: independent recomputation tools, canonical for metrics), `src/real_data/*` (descriptive, labels supplied externally; no panel), `src/benchmarks/event_study.py` (descriptive OLS market model, no inference), `results/week2_gate2.json` (schema v1, no config).
- Pilots reproduced: see `reports/mirun_pilot_reproduction.md` (520 fields, 0 discrepancies).
- Not yet done: full per-file inventory table (usage/duplication/obsolete/tests) for `src/evaluation`, `src/real_data`, `src/benchmarks`; reading `tests/*` beyond names; `configs/dgp/week1_skeleton.yaml`.

---
# File-level inventory (Session 3; import graph computed by AST scan of `src/ research/ scripts/ tests/`)
Status key: CANON = canonical/shared infrastructure, EXPL = exploratory research code, LEGACY = superseded-for-new-work but needed for replay, DIAG = diagnostic script. "Tests" = test modules that import it (a test existing is not proof the science is validated).

| Component | Role / status | Used by the DML pipeline? | Depends on | Tests | Saved outputs | Limitations |
|---|---|---|---|---|---|---|
| `src/dgp/volatility.py` | CANON GARCH (arch-share alpha, burn 1000) | **No** (no DML path uses it) | numpy | volatility, diagnostics | `results/tables/week1_week2_*`, `acf_length_sensitivity`, `arch_reference` | not wired into any outcome/treatment DGP |
| `src/dgp/regime_shocks.py` | CANON event-index regime generator, single membership | No | numpy | regime_shocks, preksha_review | - | event-time, not calendar windows |
| `src/dgp/matched_density.py` | DIAG pair-density feasibility for the single-membership generator | No | regime_shocks | preksha_review (indirect) | stdout only | **Does not apply to the calendar multi-membership DGP**; its target .0495 is unexplained in-repo |
| `src/dgp/independence.py`, `validate_volatility.py` | DIAG vol-vs-regime independence, positive control | No | volatility | diagnostics | `week3_positive_control_recheck.json`, `week3_calendar_diagnostic.json` | component-level; calendar DGP covered only by `scripts/check_calendar_independence.py` (no test) |
| `src/dgp/validate_dependence.py`, `week2_diagnostics.py` | DIAG toy event-index dependence | No | regime_shocks | week2_diagnostics via preksha_review; `validate_dependence` untested | - | toy |
| `research/week2_completion/{dgp,dml}.py` | EXPL **candidate primary**: calendar DGP, full-membership overlap sandwich, graph-component folds | Yes (all current runs) | numpy, scipy, sklearn | week2_completion, mirun_review, mirun_audit, +3 new | `results/week2_mc.json` (20 reps), session-3 scans | fixed-alpha GARCH; regime-only sandwich; no small-sample factor |
| `research/week2_completion/validation.py` | EXPL Gate 2 diagnostics | via `run_week2` | dgp, reproducibility | **none direct** | `results/week2_gate2.json` (schema v1, no config) | saved JSON predates current code |
| `research/week2_completion/run_week2.py` | EXPL runner, per-attempt raw JSON | standalone | metrics, reproducibility | mirun_review | - | does not use Sudarshan runner |
| `research/week2_mirun/*` | LEGACY first-membership CR1 DGP/DML, 200-rep pilots | replay only | numpy, `arch` (gate2_checks) | **none** | `research/week2_mirun/results/*` | different estimator and DGP: never pool with calendar; `gate2_checks.py` needs `arch` (not installed) |
| `src/evaluation/metrics.py` | CANON coverage/size/power, Wilson, MCSE, paired binary difference, replication budget | Yes (run_week2, ablation_report) | numpy | metrics, infra_reporting, week3_verification | - | independent of estimator; reuse for primary pipeline |
| `src/evaluation/verification.py`, `week3_audit.py`, `mirun_audit.py`, `monitor.py` | CANON independent audit/recompute of saved results | audit only | metrics | week3_verification, mirun_audit | `week3_mirun_verification.json` etc. | audits saved outputs; cannot approve a design |
| `src/infra/reproducibility.py` | CANON config hash, git state, SeedSequence streams, atomic JSON, run lock | Yes | numpy, yaml | infra_* | - | - |
| `src/infra/experiment_runner.py` | CANON parallel resumable runner; **accepts only `engine: mock`** | No (mock) | reproducibility | infra_runner | `sudarshan-week2-mock-*` | mock results must never be read as DML results; needs an engine hook |
| `src/infra/ablation_report.py`, `reporting.py` | CANON 4-cell report, paired Random+Robust vs Grouped+Robust | on mock only so far | metrics | infra_ablation_report, infra_reporting | mock tables/figures | cell ids `random_xfit__robust_var` etc. |
| `src/real_data/dependence.py`, `sp500_schema.py` | EXPL descriptive dependence by external labels; event schema | No | numpy | real_data_dependence, preksha_review | - | labels must be supplied; no panel in repo |
| `src/benchmarks/event_study.py` | EXPL descriptive market-model OLS (no inference) | No | numpy | event_study | - | no intervals; Synthetic Control absent |
| `scripts/*` (replay/audit/check_*, mirun_*) | DIAG | - | see above | only `mirun_fold_variance_diagnostics`, `mirun_grouped_spread_mechanism` | `results/tables/*` | most scripts untested |

Observations: (i) no code path connects canonical `src/dgp` to DML; (ii) `validation.py`, all of `research/week2_mirun`, `validate_dependence.py` and most scripts have no tests; (iii) the Sudarshan runner and the 4-cell report already use the correct cell naming and paired contrast, which should be reused rather than duplicated.
