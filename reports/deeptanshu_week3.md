# Deeptanshu: Week 3 verification, audit and diagnostics

3 November 2026. Local branch: `deeptanshu/week3-verification-audit`, based on
main `6c5ff70fdec127b9e11494b931ed92deb27f74ae`. Changes are deliberately
uncommitted/unpushed at the user's request.

## Assignment and source audit

Source: `Project_A_Week_3_Team_Work_Plan.docx`, supplied from Downloads, issued
3 November for 2–8 November. SHA-256:
`ffc0e4fb9a3d31a2b45c57c37e51c0fcfc15956b047857d8f04ea539f5795dd2`.

The plan requires independent pilot coverage/size/MCSE recomputation, numerical
monitoring, the agreed robustness subset, statistical/manipulation audit,
calm/turbulent real-data diagnostics and Methods notes. It explicitly permits
mock interval checks before saved results arrive and diagnostics on partial data.

The plan **assumes** Gate 2 and Gate 3 are approved and the design memo is shared.
The repository/remote audit found neither the actual decision records nor Mirun's
integrated DGP/DML or saved pilot. Dataset v1, daily return/residual observations
and a documented calm/turbulent label definition were not available. Preksha's
unmerged Week 2 branch contains an event schema/list, which alone cannot supply
return-panel dependence diagnostics. The user will provide the missing inputs.
No DGP, benchmark, data-curation or DML work was taken over.

## Deliverable accounting

| Week 3 item | Delivered locally | Scientific execution remaining |
| --- | --- | --- |
| Independent verification report | Standard-library verifier; strict raw/plan adapter; reference-summary and paired-comparison checks; mock report | Recompute Mirun's saved pilot/full-run numbers and explain discrepancies |
| Numerical monitoring | Read-only repeated snapshots; failure/missing accounting; estimate/interval/runtime and optional trace screens | Attach actual producer outputs/traces and monitor the real run |
| Agreed robustness subset | Same four-cell accounting applies to explicitly planned robustness scenarios; mock role exercised | Obtain the Gate 3 subset/configs, execute with the actual DML, and audit its saved records |
| Statistical audit | All six cell pairs have MCSEs; per-cell manipulation-check interface; actual-component positive-control recheck | Verify actual manipulation evidence per cell and apply the approved interpretation criteria |
| Real-data diagnostics | Labelled-panel reader, missingness/overlap audit, pair correlations, matched-pair label contrast; synthetic validation | Run on the frozen/partial return panel with Preksha's documented labels |
| Methods notes | Contract, formulas, commands, assumptions, inference limits and provenance documented | Add the final producer/design/data details when supplied |

This is a completed **standalone preparation package**, not a declaration that all
Week 3 scientific deliverables or Gate 4/5/6 are complete.

## Implemented files

- `src/evaluation/verification.py`: independent raw arithmetic and accounting.
- `src/evaluation/week3_audit.py`: adapters, numerical/manipulation screens,
  claimed-result comparisons, provenance, source snapshots and CLI.
- `src/evaluation/monitor.py`: repeated snapshots; the producer is never modified.
- `src/real_data/dependence.py`: qualitative calm/turbulent diagnostics.
- `examples/week3_mock_review.py`: reproducible constructed-interval and
  synthetic-panel exercise with a separate production-metrics reference.
- `scripts/check_week3_positive_control.py`: pinned actual-component recheck.
- `docs/week3_verification.md`: runnable handoff contract and Methods notes.

No existing GARCH/regime, production metric, DML or runner source is modified.
The independent calculation path imports neither NumPy nor production metrics.

## Verification evidence

The fresh environment was installed from the unchanged `requirements-dev.txt`;
coverage was added as a temporary validation tool. Python 3.13.13, NumPy 2.5.4,
Matplotlib 3.11.2, PyYAML 6.0.3, pytest 9.2.0: **245 tests passed with warnings as
errors**, including 81 new hand-calculated, malformed-input, provenance, pairing,
monitoring and real-data cases. The existing local environment also passed the
new targeted suite. Native Windows/macOS execution remains unverified.

The full mock exercise has 1,200 saved interval rows across three scenarios,
12 four-cell summaries and 36 paired comparisons. All required summary and
central paired claims matched the separate reference calculations. It exercises
null size and nonnull power, missing/failure handling in tests, and explicit
per-cell fixture probes. The probes are not real manipulation-check evidence.

An additional 80 randomized cases, including missing/failed/single-panel inputs,
produced **6,148 numerical crosschecks** against the production metrics and NumPy
reference calculations. Maximum observed absolute difference was about 4.44e-16.
A 40,000-row mock input-size exercise completed with every planned row accounted
for. Its timing measures verification processing, not DML experiment runtime.

Both CLIs ran with site packages disabled (`python -S`). Extracting their exact
source ZIPs into directories without Git or third-party packages reproduced the
numerical audit/diagnostic payloads exactly. UTC metadata, hashes, source archives,
full reports and the stress/fuzz driver remain in ignored raw evidence.

The synthetic labelled-panel check has near-zero calm mean pair correlation and
about 0.990099 turbulent mean correlation, by construction. These values validate
alignment/arithmetic and are explicitly marked mock; they are not S&P 500 results.

Small reviewable summary: `results/tables/week3_software_validation.json`.
Raw evidence: `results/raw/week3_software_validation_v3/` and
`results/raw/week3_adversarial_validation_v2/`. Earlier development evidence is
retained separately with its exact source snapshot.

## Actual-component positive control

The fresh seed 20261103 was recorded before the recheck. The unchanged GARCH and
regime modules at main `6c5ff70` were used with the existing provisional Week 2
independence settings: 100 independent panels, 16 firms, 512 periods, 199 complete
regime randomizations per check. There were zero failed/undefined panels and zero
stream-invariance failures.

| Diagnostic | Detections | Plug-in MCSE | Wilson 95% interval |
| --- | ---: | ---: | --- |
| Independent component false detections | 6/100 | 0.02375 | [0.02779, 0.12477] |
| Deliberately broken-independence control | 100/100 | 0 | [0.96301, 1] |

Independent rate/MCSE/Wilson recomputation matched. The boundary MCSE of zero for
100/100 does not imply certainty. This tests the existing diagnostic's sensitivity
on actual components; it is not proof of independence, the integrated DGP's
manipulation check, or the approved Week 3 robustness subset.

The run used the existing local environment (NumPy 2.3.5, Matplotlib 3.11.1);
environment details were recorded after execution, with no package changes during
the run. Exact pinned regime source, per-panel results, config and script/source
hashes are retained. Exact selected-panel replay also matched for replication
IDs 0, 17 and 99. See `results/tables/week3_positive_control_recheck.json` and
`results/raw/week3_positive_control_20261103/`.

## Open audit items and immediate handoff

1. Supply the actual Gate 2 decision and dated Gate 3 design memo, including who
   agreed, the grid/effect conditions, replication IDs/budgets, approved robustness
   subset, manipulation definitions, numerical review thresholds and materiality
   criteria. The script will not invent these or infer approval from the schedule.
2. Export Mirun's raw pilot intervals and claimed cell/central-comparison summaries
   using the documented contract, or supply his actual schema so the adapter can
   be reviewed. Include panel/seed/source identities, failure reasons and runtime.
3. Supply per-cell manipulation evidence and numerical diagnostics/traces. Raw
   interval arithmetic alone cannot certify the DML, induced dependence or every
   state/nuisance-fitting path.
4. Supply the frozen/partial daily return, abnormal-return or residual panel and
   external regime-label rationale. The event list alone is insufficient. No true
   effect is known for real data, so there is no coverage/empirical-size calculation.
5. Once the above exist, run the actual pilot audit, agreed robustness jobs, live
   monitoring and real-data diagnostics; update the report with actual outcomes.
   Freeze decisions and the official submission deadline still need team evidence.

Do not interpret signed rate differences as a coverage benefit, replace paired
uncertainty with independent-binomial errors, treat failure-conditioned rates as
unconditional, or claim equivalence from nonsignificance. The P5 materiality rule
remains a proposal until the actual lock memo establishes the team's choice.
