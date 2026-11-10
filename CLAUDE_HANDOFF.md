# CLAUDE_HANDOFF — ADA Project A (Mirun) — Session 5 reconstruction

Base commit: `b5581562d818534a802f060920465df5fddf8a67` (`main`, PR #9). Intended local branch: `mirun/execution-session1`. The Session 4 checkpoint and Session 5 edits are uncommitted; no commit, push, or PR was created as part of this reconstruction.

## Recovery / application
For a clean checkout at the base commit:

```bash
git apply --check ADA_Project_A_Session5_FINAL.patch
git apply ADA_Project_A_Session5_FINAL.patch
```

If the Session 4 checkpoint is already applied, use `ADA_Project_A_Session5_DELTA.patch` instead:

```bash
git apply --check ADA_Project_A_Session5_DELTA.patch
git apply ADA_Project_A_Session5_DELTA.patch
```

The full patch is an additions-only research-work package against `b558156`; the Session 5 delta is based on the recovered Session 4 additions-only checkpoint. See `SESSION5_PATCH_README.md` for the complete placement map and provenance.

## Session 5 implementation and diagnostics
- `scripts/mirun_session5_checks.py`: canonical-vs-calendar GARCH comparison, event-membership/window-overlap reproduction, and exploratory control runner/summarizer. The Session 5 script was recovered verbatim from the old transcript and passed `py_compile`.
- Gate 3 proposal moved to `configs/mirun_gate3.yaml`; new negative controls, factor ablation, separate estimator proposals, compute budget, output schema and proposed acceptance criteria were added. Every decision remains `AWAITING_TEAM_APPROVAL`.
- Gate 2 and undercoverage reports now include the Session 5 evidence and hypothesis ledger.
- `src/infra/dml_engine.py` now recursively finds every nested `approved: AWAITING_TEAM_APPROVAL` field before production execution. `tests/test_dml_engine.py` adds a regression test for an unapproved nested negative-control field.
- Methods and Results were separated into `reports/mirun_methods_draft.md` and an empty-by-design `reports/mirun_results_template.md`.
- The GARCH, overlap and control summary JSON files are in `results/tables/`. The control summary and GARCH summary carry explicit reconstruction-provenance notes because the original full JSON outputs were absent from the recovered raw archive.

## Session 5 test status
- Session 5 transcript records an earlier targeted run of DML engine + real-data contract tests: 19 passed.
- After the approval-guard change, `tests/test_dml_engine.py`: 11 passed in 7.28s.
- Full suite `python -W error -m pytest -q` was **not rerun after Session 5**. The 354-pass count in the Session 4 handoff is a Session 4 result only.
- In this reconstruction environment, Python syntax compilation passed for recovered/modified files and the renamed Gate 3 YAML parsed successfully. The full project source tree was not restored into this local work directory, so the repository-wide suite could not be rerun here.

## Scientific findings — exploratory only
- Five pilot conditions, 200 replications each, `tau=1`, seeds 70000+, `K=4`, density=.5, `n=400`.
- Default benchmark coverage: random naive .740, random multiway .815, grouped naive .650, grouped multiway .795.
- Independent control: random naive .930, random multiway .870, grouped naive .900, grouped multiway .875. The CR0-normal multiway cell undercovers even without regime/common-factor dependence, so this contrast is confounded by a few-cluster finite-sample calibration issue.
- Factor-only naive coverage was .945/.940; factor-off variance-matched robust coverage .805/.785 versus default .815/.795. The calendar factor is not the evident driver in this DGP.
- Overlap reproduction: K=4, 0/80,000 multi-regime events; K=16, 280/80,000; calendar-window pair overlap 3.4815%. The earlier `12/80,000` figure was not reproduced.
- These results do not establish that grouped cross-fitting is superior. They are not a production result and do not support a causal conclusion about dependence-robust variance generally.

## Still open / blocked
1. Run a separate `tau=0` empirical-size study; the Session 5 controls run used `tau=1` only.
2. Complete a side-by-side finite-sample comparison of CR0-normal, CR0 with `t(G-1)`, and the separately proposed regime-part CR1 correction with `t(G-1)`; team approval is required before selecting one.
3. Decide whether the current calendar DGP actually instantiates the intended dense common-shock dependence, and whether a new dependence mechanism is required.
4. Resolve the K=16 overlap-count discrepancy and review the GARCH-family differences before any approved DGP change.
5. Restore or regenerate Session 5 raw per-replication controls (five conditions x 200 reps); those files were not included in the Session 4 raw archive. Do not treat the rounded reconstructed summary JSON as a byte-for-byte original output.
6. Obtain Preksha's daily panel and externally sourced regime labels/provenance; the real-data work remains blocked.
7. Obtain Deeptanshu's independent statistical audit and Sudarshan's engine/reproducibility review.
8. Define the missing original "11 Gate 2 checks" and obtain explicit team approval for Gate 2/3 decisions.

**No Gate 2 or Gate 3 approval is asserted. No production Monte Carlo is authorized or claimed.**
