# Deeptanshu: Week 3 verification, audit and diagnostics

4 November 2026. Delivery branch: `deeptanshu/week3-verification-audit`, integrated
with main `0efe494` (Mirun's PR #5 and follow-up review fixes PR #6). The user's
latest instruction authorizes commits, pushes and the Week 3 PR merge.

## Assignment and source audit

Source: `Project_A_Week_3_Team_Work_Plan.docx`, supplied from Downloads, issued
3 November for 2–8 November. SHA-256:
`ffc0e4fb9a3d31a2b45c57c37e51c0fcfc15956b047857d8f04ea539f5795dd2`.

The plan requires independent pilot coverage/size/MCSE recomputation, numerical
monitoring, the agreed robustness subset, statistical/manipulation audit,
calm/turbulent real-data diagnostics and Methods notes. It explicitly permits
mock interval checks before saved results arrive and diagnostics on partial data.

The plan **assumes** Gate 2 and Gate 3 are approved and the design memo is shared.
Mirun's new code and pilot summaries are now on main, but the completion pack and
decision log contain proposals rather than approval. The friend confirmed there
is no original full-run raw archive or frozen labelled daily-return dataset.
Preksha's separate branch has an event list/schema, insufficient for return-panel
dependence diagnostics. No final robustness design or data labels were invented.

## Deliverable accounting

| Week 3 item | Delivered | Remaining dependency |
| --- | --- | --- |
| Independent pilot verification | 320 active-pilot and 5,040 legacy-table interval rows reconstructed; 76 coverage rates checked; bias/width/MCSE audit and discrepancy report | Original raw archive/environment needed to reconcile small legacy differences; approved full-run archive still absent |
| Numerical monitoring | Canonical and actual calendar-runner adapters; read-only repeated snapshots; failure/missing accounting and source/config/seed/fold checks; 32-cell actual smoke audit | Monitor the approved production run when launched |
| Agreed robustness subset | Verifier accepts explicitly declared robustness/extra-seed scenarios; replay of already-published gamma/factor/K ablations | Team must lock subset/configs/budgets before new robustness execution |
| Statistical/manipulation audit | Paired MCSEs, conditional denominators, Wilson/bounds; 100-panel component positive control and 20-panel actual calendar-DGP recheck; fold-source audit | Approved manipulation/materiality criteria and primary scientific DGP/variance choice |
| Real-data diagnostics | Labelled-panel reader, missingness/overlap audit, pair correlations and matched-pair label contrast; synthetic validation | Preksha's return/residual panel and documented calm/turbulent labels |
| Methods notes | Contracts, formulas, commands, source/environment provenance and limitations | Final approved design and dataset specifics |

Available software and pilot-review work is delivered. Week 3 scientific completion
still depends on the agreed robustness run and real-data inputs; no Gate 4/5/6 is
claimed complete.

## Implemented files

- `src/evaluation/verification.py`: independent raw arithmetic and accounting.
- `src/evaluation/week3_audit.py`: adapters, numerical/manipulation screens,
  claimed-result comparisons, provenance, source snapshots and CLI.
- `src/evaluation/monitor.py`: canonical/calendar repeated snapshots; producer files are never modified.
- `src/evaluation/mirun_audit.py`: strict adapter for the reviewed actual runner.
- `scripts/replay_mirun_pilots.py`, `scripts/audit_mirun_replays.py`: pinned historical reconstruction and independent table audit.
- `scripts/check_calendar_independence.py`: actual calendar-DGP separation/control recheck.
- `src/real_data/dependence.py`: qualitative calm/turbulent diagnostics.
- `examples/week3_mock_review.py`: reproducible constructed-interval and
  synthetic-panel exercise with a separate production-metrics reference.
- `scripts/check_week3_positive_control.py`: pinned actual-component recheck.
- `docs/week3_verification.md`: runnable handoff contract and Methods notes.

No existing GARCH/regime, production metric, DML or runner source is modified.
The independent calculation path imports neither NumPy nor production metrics.

## Verification evidence

The fresh environment was installed from the reviewed `requirements-dev.txt`:
Python 3.13.13, NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, Matplotlib 3.11.2,
PyYAML 6.0.3 and pytest 9.2.0. **283 tests passed with warnings as errors** for
the integrated delivery, including 81 original Week 3 and 15 actual-runner
adapter/monitor cases. Hand-calculated, malformed-input, provenance, pairing,
monitoring and real-data cases are covered. The existing local environment also
passed the targeted new suite. Native Windows/macOS execution remains unverified.

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

## Actual pilot and archived-ablation verification

Exact-source reviewer reconstruction at `26e65f1` produced 320 raw cell rows for
the four active gamma/tau conditions (20 panels each). All 128 available reported
fields across 16 cell summaries matched at absolute tolerance 1e-12/relative
1e-10, including coverage, bias, RMSE, width and null size/MCSE where supplied.
The largest bias/width discrepancy was about 3.1e-16. Missing original power,
width-MCSE and paired-MCSE fields were not invented as verified claims.

The legacy first-membership CR1 variant was replayed separately: 15 scenarios,
1,260 scenario/replication references and 1,020 distinct config/seed worlds,
yielding 5,040 interval rows. Reused worlds across tables were computed once;
they do not increase independent sample size. There were zero failed cells.
Together the two variants reproduce **all 76 reported coverage rates**. Of 520
checked fields, **120 continuous legacy entries differ**, with maximum absolute
difference **6.221053092e-6**. Differences occur in bias, width, empirical SD,
mean SE and SE/SD ratio. Their cause is unresolved: the original replication
archive, exact generating source/environment and per-replication values were not
provided. They are retained as discrepancies; the audit exits 2. Historical
results remain untouched. Runtime measurements are environment-dependent and
are not equality-checked. The separate single-toy runtime example is outside
these Monte Carlo summary counts.

Paired uncertainty is reconstructed from common panel IDs. Selected central
coverage contrasts (random+robust minus grouped+robust):

| Variant / condition | Difference | Paired MCSE | Panels |
| --- | ---: | ---: | ---: |
| Active gamma=0, tau=1 | .05 | .05 | 20 |
| Active gamma=1, tau=1 | 0 | 0 | 20 |
| Legacy K=4, gamma=1 | .04 | .01854 | 200 |
| Legacy K=16, gamma=1 | -.01 | .01416 | 200 |

Zero sample MCSE does not prove equivalence. These exploratory variants are not
pooled, and no budget/materiality rule or primary variant was selected from their
coverage. Nonnull rejection rates are power, never null size.

The reviewed runner's actual 2-rep/four-scenario smoke emitted 32 cell records and
8 atomic attempt files. Independent standard-library adaptation matched every
required headline summary and denominator; source hashes matched the recorded
clean Git object. Missing files remain missing even when run.json contains inline
copies; manifest scenarios absent from an interrupted summary remain planned.
New tests exercise corrupt seeds/configs, failed robust-only CIs, incomplete
scenarios, source invalidation, fold assignments, path escapes and monitoring.

Tracked summaries: `results/tables/week3_mirun_verification.json` and
`results/tables/week3_calendar_diagnostic.json`. Full local raw evidence remains
under `results/raw/week3_mirun_replay_audit_delivery_20261104/`,
`results/raw/mirun_original_review_26e65f1/`,
`results/raw/mirun_legacy_replay_26e65f1/`, and
`results/raw/week3_calendar_audit_final_20261104/`.
The replay environment is NumPy 2.3.5, SciPy 1.16.3, scikit-learn 1.7.2. Three
selected legacy worlds also exactly replayed through the delivered replay worker.
Raw data were reconstructed by the reviewer, not supplied by Mirun.

## Actual calendar-DGP separation and fold-source check

Using the active pilot's exact 20 seeds/configs, the existing whole-process
randomization diagnostic was applied to the calendar regime process, with its
actual separate layout/shock draws. The .05 screen and 199 randomizations are
inherited diagnostic settings, not an approved Gate threshold. The actual
`break_vol_independence=True` path supplies the deliberately invalid control.

Independent panels: 0/20 detections, Wilson 95% approximately [0, .16113].
Invalid-control panels: 20/20 detections, Wilson [.83887, 1]. Both plug-in MCSEs
are zero at the boundary; the intervals express uncertainty. There were no
nonfinite returns, nonpositive sigma values or volatility-stream invariance
failures after changing regime/treatment settings. Maximum absolute idiosyncratic
return was 7.63016; no extreme-value cutoff or clipping was applied.

Regime-grouped folds had zero regime-sharing pairs across folds on every panel,
but still 711–1,097 potential shared-calendar-factor pairs across folds. Thus
regime purity alone does not certify all-source fold separation. These counts
are structural potential links, not significance tests or effect sizes. This is
actual calendar-DGP diagnostic evidence, not a nominal-coverage proof. Raw source,
configs, panel results and diagnostic RNG addresses are retained under
`results/raw/week3_calendar_independence_20261104/`.

## Immediate remaining handoff

1. Team records approved Gate 2/3 decisions, primary DGP and variance variant,
   agreed robustness subset, budgets, manipulation and materiality criteria.
2. Mirun supplies the original per-replication archive/environment to investigate
   the small legacy discrepancies, and the approved production run when ready.
3. Preksha supplies the frozen/partial daily return/residual panel and external
   regime-label rationale. The event list alone is insufficient.
4. Execute and audit the locked robustness jobs, monitor the full run, then run
   real-data diagnostics. Real data with unknown truth cannot establish coverage.

Do not interpret a signed coverage difference as automatic benefit, substitute
independent-binomial errors for paired uncertainty, or treat failure-conditioned
rates as unconditional. P5 and the completion pack remain competing proposals
until the team's dated decision chooses a rule.
