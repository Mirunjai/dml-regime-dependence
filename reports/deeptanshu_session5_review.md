# Independent Session 5 review — 10 November 2026

Reviewed Mirun branch `mirun/session5-reconstructed` at `ceb150e`, based on
main `b558156`. All 62 changes are additions: the shared GARCH, DGP, DML and
metric source were not replaced. Original branch remains unchanged.

## What Mirun delivered

A separate calendar-DML runner with proposed production approvals, raw records,
resumption and aggregation; real-panel/event contract validation; overlap and
few-cluster diagnostics; exploratory nuisance/variance alternatives; Gate 2/3
proposals; Methods draft and deliberately blank Results template. Historical
studies investigate failures, grouped-fold spread, factor removal, larger n,
zero-effect rejection and oracle/GBR alternatives. Oracle routes use simulation
truth and must remain diagnostic routes, not deployable estimators.

The branch labels reconstructed Session 5 tables and explicitly discloses missing
raw controls. No daily-return panel, external labels or ratified design is present.
The handoff's old 'nothing committed' text describes the recovered Claude session;
the reconstructed delivery itself is committed at the SHA above. A recorded
Session 4 test count is not verification of Session 5.

## Independent execution and findings

The original branch passes 355 tests with warnings as errors. Fresh execution of
its unchanged overlap script reproduces K=4: 0/80,000 and K=16: 280/80,000
multi-regime events over 200 seeds. Calendar-overlap pair share is .03481485.
The earlier 12/80,000 claim is not reproduced by these documented settings.

The canonical/calendar GARCH comparison was executed afresh at its existing
settings. Separate alpha mappings, burn-in and draw order remain distinct model
families; neither is silently substituted. Outputs are in the review table.

A bounded reviewer control reconstruction uses the original five configurations,
seeds 70000–70019 and 20 replications each (100 worlds, 400 cell rows). This is
engineering/exploratory verification, not the missing original 200-rep archive or
an approved robustness campaign. The standard-library auditor independently
recomputes coverage, nonnull power, widths, bias/RMSE, paired MCSEs, Wilson
intervals and all-planned accounting. Every planned cell is present and successful.
For the independent control, coverage is .85/.80 for random naive/robust and
.80/.80 for grouped naive/robust. These small samples are imprecise and cannot
establish the mechanism of undercoverage, select an estimator or ratify a gate.
They do not verify equality to rounded historical 200-replication summaries.
Nonzero-effect rejection is power; it must not be labelled empirical size.

Original E3/E6/E7 replication archives are not on this branch. Their reported
numbers remain unverified claims; the fresh reconstruction does not retroactively
validate them. Existing historical replay discrepancies also remain documented.

## Corrections on the review branch

- Reject empty approval metadata that previously bypassed the pending-token guard.
- Enforce approved production root seed and replication count, prohibit production
  overrides and off-grid conditions, and reject unsupported learner/variance choices.
- Fingerprint engine/DGP/DML source and software for resume; refuse source/version
  mixing. Validate existing records on resume and aggregation: IDs, seeds, truth,
  label, world config, four unique cells and interval validity.
- Reject Boolean return values and Boolean contract thresholds; represent numeric
  overflow as a data error rather than leaking an exception.
- Add an independent standard-library raw-controls auditor with explicit planned
  IDs; missing rows remain missing and corrupt seeds are rejected.

363 combined tests pass with warnings as errors, including eight review cases.
Tests establish implementation behavior, not authenticity of an approval memo or
scientific validity of a chosen covariance. Production execution is not certified
merely by filling YAML fields: team decisions and scientific review remain needed.

## Week 3 accounting

Independent review, overlap/GARCH corroboration, fresh raw-control arithmetic,
Methods notes and software corrections are delivered. Tracked review table:
`results/tables/deeptanshu_session5_review.json`. Full raw evidence and audit source
ZIP: `results/raw/session5_week3_review_20261110/` in the primary checkout.
Local environment: Python 3.13, NumPy 2.3.5, SciPy 1.16.3, sklearn 1.7.2.
This differs from Mirun's recorded reconstruction environment; bitwise equality
across those environments is not claimed.

Still required: original archives for independent verification of historical size
and undercoverage claims; team-approved DGP/variance/grid/robustness decisions;
and Preksha's daily-return/residual panel plus documented calm/turbulent labels.
A new final size/robustness campaign or actual real-data analysis cannot honestly
be marked complete from this proposal and reconstructed summaries.
