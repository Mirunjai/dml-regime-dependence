# Mirun remaining work and integration status — after Session 5

Statuses below distinguish implemented code, exploratory evidence, independent verification, and team approvals. Nothing in this report is an independent audit or a Gate 2/Gate 3 approval.

## Completed in Sessions 1–5 (Mirun work)
| Item | Status | Location |
|---|---|---|
| Baseline restoration and Session 4 additions | Recovered from verified checkpoint | `SESSION4_BASELINE.patch` / `ADA_Project_A_Session5_FINAL.patch` |
| Historical pilot replay (520 fields, zero discrepancies) | Reproduced in prior session | `reports/mirun_pilot_reproduction.md` |
| Overlap-sandwich characterization and grouped-fold diagnostics | Implemented/tested/executed in prior sessions | `tests/test_mirun_overlap_sandwich.py`, `reports/mirun_grouped_folds_diagnostics.md` |
| Failure scan, grouped-spread interventions, factor-off diagnostics | Executed, exploratory | `scripts/mirun_failure_rate_scan.py`, `scripts/mirun_grouped_spread_mechanism.py`, `scripts/mirun_factor_off_check.py`, `results/tables/` |
| Gate 2 regeneration and evidence ledger | Written/executed; not approved | `reports/mirun_gate2_evidence.md`, `results/tables/mirun_gate2_regen_summary.json` |
| Gate 3 design proposal and YAML | Written; all additions remain awaiting approval | `reports/mirun_gate3_experiment_proposal.md`, `configs/mirun_gate3.yaml` |
| Approval-guarded DML engine | Implemented; 11 targeted tests recorded after Session 5 guard change | `src/infra/dml_engine.py`, `tests/test_dml_engine.py` |
| Real-data panel contract | Implemented; synthetic-only validation tests recorded | `src/real_data/panel_contract.py`, `reports/mirun_real_data_requirements.md` |
| Session 5 GARCH, overlap and controls script | Recovered from transcript; syntax-checked | `scripts/mirun_session5_checks.py` |
| Session 5 control pilot | 200 reps per condition, exploratory `tau=1` only; summary reconstructed from printed output | `results/tables/mirun_session5_controls.json` |
| Methods and Results separation | Written; Results intentionally blank | `reports/mirun_methods_draft.md`, `reports/mirun_results_template.md` |

## Research and implementation still required
1. Run the empirical-size study with `tau=0`; no Session 5 control result supplies this diagnostic.
2. Compare CR0-normal, CR0 with `t(G-1)`, and CR1-regime with `t(G-1)` under a separately documented design. No estimator is selected by the current evidence.
3. Decide whether the DGP creates the intended dense common-shock dependence. The factor-only and variance-matched ablations indicate the current calendar factor does not explain the undercoverage.
4. Resolve the K=16 multi-regime count discrepancy (the recovered Session 5 run gives 280/80,000, not the earlier 12/80,000).
5. Restore/regenerate Session 5 raw per-replication controls and verify the reconstructed rounded summary against them.
6. Re-run the complete test suite after all Session 5 changes (`python -W error -m pytest -q`). The 354-pass record belongs to Session 4; only targeted Session 5 runs are recorded.
7. Complete independent reviews (Deeptanshu statistical audit; Sudarshan engine/reproducibility review).
8. Obtain Preksha's daily-return/residual panel, external regime labels and label provenance; validate the real-data mapping.
9. Define the original 11 Gate 2 checks and secure team approval of all Gate 2/3 decisions before production.

## Team-owned decisions/dependencies
- **All:** primary DGP, variance estimator, gamma/density definition, replication grid/budget, seed, common-shock mechanism, and all `AWAITING_TEAM_APPROVAL` fields.
- **Deeptanshu:** independently audit the pilot/control evidence and estimator calibration.
- **Preksha:** supply daily panel, external regime labels, provenance and the label-to-regime mapping.
- **Sudarshan:** review the engine, production guard, output schema and reproducibility package.

## Data gaps and boundaries
- The old Session 5 runtime generated per-replication controls (five conditions x 200 records), but those raw JSON files were not included in the recovered Session 4 archive. They are not fabricated here. See `results/raw/mirun_session5/RECOVERY_NOTE.md`.
- No daily-return/residual panel or regime-label file is present in the recovered project materials.
- The original Gate 1 document / definition of the 11 checks is absent.
- Gate 2 and Gate 3 remain open. No production Monte Carlo has been run or approved.
