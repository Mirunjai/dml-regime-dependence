## Project close-out execution work — 12 November 2026

A draft close-out PR (#14) adds a consolidated audit, an event-level density
mapping proposal, a variance-estimator decision protocol, and a reproducible
calendar-DGP event-density diagnostic. The diagnostic reproduces
`build_world` event memberships from the same named RNG streams and
`simulate_calendar_regimes` function. Its tests cover exact membership parity,
zero exposure, one-cluster pair density, multi-membership deduplication and
invalid labels.

GitHub Actions on the close-out branch ran the full suite with warnings treated
as errors: **401 passed** (Python 3.13.18; run
[43203132264](https://github.com/Mirunjai/dml-regime-dependence/actions/runs/43203132264)).
An earlier run failed one newly written test because its expected pair count
was wrong; the test expectation was corrected and the full suite then passed.
The failed run is retained as history, not hidden.

The density diagnostic distinguishes configured calendar fraction, event-exposed
share, and unconditional shared-pair density. The Plan B structural audit proposes
event-exposed share as the main descriptive density axis and a separate H4
pair-density match (K=4, calendar fraction .31; K=16, .50). Pair density is
approximately .03585 in both cells, while event-exposed shares differ (.37869
versus .75334). This is one matched structural quantity, not equivalent overall
dependence structures. The team must ratify it and the thresholds. Gate 2 and
Gate 3 remain unapproved.

The variance decision memo lists CR0-normal, CR0-t, CR1-regime+t, CR2/BRL with
Satterthwaite degrees of freedom, and restricted wild cluster bootstrap-t as
candidates. None is newly designated as the primary estimator by this work.
Production execution remains blocked by the existing approval guard until the
team records Gate 2/3 decisions.

This PR does not complete production Monte Carlo results, independently verify
the science, or close the missing labelled daily return panel / SCM donor data.
Historical CAR summaries remain unverified. These limits remain explicit.

# Project state

## Preksha Week 3 integration — 12 November 2026

Reviewed source `21b9e38`: date-aware classical/SCM helpers, VIX event labels,
acquisition/source/donor tools and documented data gaps are integrated with
corrections. 395 tests pass with warnings as errors. All eight VIX event labels
reproduce; saved fresh prices cover six of eight treated firms. Historical CAR
results lack their original combined input and remain unverified; SCM has no
eligible donors or executed results. Event-specific calm/mixed/turbulent labels
are not a frozen daily binary-labelled panel. Raw price responses are preserved
in ignored local evidence, excluded from the integration tree. See
[the detailed review](../reports/preksha_week3_review.md).


## Sudarshan local Week 3 check on 11 November 2026

Compared Mirun's saved calendar-pilot table against the pinned-source replay
summary. All 128 field checks matched. Generated four 2×2 tables, 12 pilot
heatmaps, one figure for the verified S&P 500 inclusion events, and a
reproducibility log with hashes and source. See
[the Week 3 report](../reports/sudarshan_week3.md) for commands and evidence.

The original raw pilot archive, team-selected full-run subset and its records,
and labelled daily-return panel remain open. The local work regenerates
reports from saved evidence. Gate 2 and Gate 3 approvals remain with the team.

## Sudarshan local Week 2 check on 11 November 2026

The local `Sudarshan` checkout at `c582846` already contained the original
runner and templates. The reviewed implementation and tests from PR #4
(`6c5ff70`) are now applied as working-tree edits. Heatmap labels have a light
background for legibility across cell colors. On macOS, all 164 tests
passed with warnings treated as errors. A 12-replication serial mock run
resumed with three workers after two records were set aside. All 12 JSON files
matched byte for byte. Independent recomputation matched the four coverage,
empirical-size and mean-width rows, and the reporter rendered three heatmaps.

The Week 2 infrastructure core is complete. The optional saved-diagnostic
pass/fail helper and S&P data-pull helper remain open. The mock results test
reproducibility and reporting. The team still owns Gate 2 and Gate 3 approval.



## 10 November Session 5 review

Mirun's reconstructed branch at `ceb150e` adds a guarded engine, exploratory
studies, a panel contract and proposed design. Independent review passes 363
tests, reproduces K=16's 280/80,000 multi-membership count, regenerates the GARCH
comparison and independently audits 400 fresh control cell rows. Engine approval,
resume and record checks were hardened. See
[the independent review](../reports/deeptanshu_session5_review.md).

These control rows are a bounded reviewer reconstruction, not the missing original
200-replication control archive. Gate 2/3 remain unapproved; historical full raw
archives and the labelled daily-return panel remain absent. Scientific robustness
and real-data completion remain pending. Earlier dated snapshots are historical.


Updated 8 November 2026. Main before this review: `48a28e7` (PR #7).
Earlier dated sections below describe historical milestones; the snapshot here
supersedes their statements about branch availability and current test counts.

## 8 November branch review and Week 3 close-out

Remote inventory found no new code beyond the previously audited branch tips.
Sudarshan PR #8 repeats the exact tree already merged by PR #4 and was closed as
a duplicate. His branch is retained. Mirun's `a84b548` delivery is already merged.

Preksha's previously unmerged Week 2 branch at `8144aba` is integrated in the
review branch with corrections for generator CSV data loss, atomic validated
writes, malformed pair-density inputs, undefined constant-exposure associations,
regime/noise RNG separation and event-study boundary/overflow handling. The
existing generator now rejects boolean settings without changing valid-input
simulation paths. The event-index prototypes remain separate from Mirun's
calendar model. See [the review report](../reports/preksha_week2_review.md).

The seven inclusion events match S&P's two published announcements. They form a
small event sample, not daily returns or dataset v1. The code has no inferred
calm/turbulent labels. All four prototype CLIs ran; the combined suite passes
**317 tests with warnings as errors** in the existing local environment.

Three merged user branches were deleted locally/remotely after complete bundle
backup and exact tree checks against PR #3/#6/#7 squash commits. No teammate
branch was deleted. The review branch is also eligible for cleanup after merge.

Your available Week 3 software, historical pilot audit, component/calendar
controls and Methods are delivered. Remaining scientific work still needs the
team's dated Gate 2/3 design/robustness decisions and Preksha's labelled daily
return/residual panel. Neither was found in the current remote inventory.
Final robustness execution, production-run verification and actual real-data
comparisons cannot be recorded as completed from prototypes or an event list.

## Mirun integration review

PR #5 merged the calendar-time DGP/DML layer at `1b914cd`; PR #6 hardened it at
`0efe494`. Mirun changed none of the existing GARCH, diagnostic, metric or mock
runner source under `src/`. His separate fixed-alpha GARCH and calendar regimes
are different models from the canonical components; the
[review memo](../reports/mirun_week2_review.md) documents the distinction.

The review fixes preserve valid cells after inference/split failures, save atomic
raw attempts, expose denominators/uncertainty, reject invalid memberships/control
switches, replace exponential overlap-sandwich evaluation with the same direct
pair formula, route actual configs/seeds into diagnostics and fix fresh installs.
These are implementation corrections, not approval of the proposed covariance.

## Week 3 independent verification and diagnostics

The user's latest instruction authorizes commits, pushes and merging the delivery
branch `deeptanshu/week3-verification-audit`. The package provides independent
standard-library arithmetic, strict canonical and actual-calendar adapters,
planned/missing/failed accounting, paired MCSEs, read-only monitoring, optional
manipulation checks and qualitative calm/turbulent panel diagnostics.

Actual saved-pilot review reconstructed 320 active-pilot and 5,040 legacy-table
cell records. All 76 reported coverage rates match. Across 520 checked fields,
120 legacy continuous entries differ by at most 6.2211e-6; these remain flagged,
not overwritten or attributed to an unproven cause. Distinct estimators are kept
separate. The legacy tables reuse 1,020 unique worlds across 1,260 references.
A reviewed-producer 32-cell smoke independently matches its headline metrics.

Validation: **283 tests pass with warnings as errors** in a fresh development
environment; the prior 1,200-row mock, 80-case/6,148-crosscheck randomized exercise,
40,000-row input exercise and standalone source-ZIP replay remain documented.
The original component recheck detected the invalid control in 100/100 panels;
the actual calendar-DGP recheck detected its control in 20/20, with 0/20
independent detections. Wilson intervals and boundary-MCSE caveats are reported.
Regime-pure grouped folds still have potential calendar-factor links across folds.

The available software and pilot verification are delivered. The team has not
provided an approved Gate 2/3 memo, locked robustness subset, original full-run
raw archive/environment, or frozen labelled daily-return panel. The friend's
artifact inventory confirms these omissions; an event list/schema is not a
return panel. Final robustness execution, production-run verification and actual
real-data diagnostics remain pending. No gate is marked passed.

See [the Week 3 report](../reports/deeptanshu_week3.md),
[commands and Methods](week3_verification.md), and the small reviewable tables
`results/tables/week3_mirun_verification.json` and
`results/tables/week3_calendar_diagnostic.json`. The schedule's 8 November freeze
and 13 November submission-ready target do not establish an official deadline.

## Sudarshan infrastructure integration

Reviewed branch `Sudarshan`, initially at `c58284635b5b86fbf85a15a86df4bc88558f843d`,
based directly on the shared main at `566ad07c`. It adds independent RNG/config
utilities, atomic saved records, a parallel/resumable **mock-only** runner, generic
report helpers and four-cell coverage/size/power/width reports. Existing
statistical formulas are reused; GARCH and regime source are unchanged.

The original 151 combined tests passed. Integration fixes and 13 regression cases
bring the suite to **164 passing tests with warnings as errors** in a clean,
requirements-only environment. The CLI serial/three-worker resume preserved all
12 replication files byte for byte; raw summary statistics were independently
recomputed. Explicit spawn, engine failure accounting, failure-preserving resume,
provenance tampering, parent locking and all-failed stale-plot handling were tested.
See [the infrastructure review](Sudarshan_INFRA.md#integration-review-1-november-2026)
for fixes, exact software versions, commands and remaining platform limitations.

This milestone supplies executable infrastructure, not an integrated DGP, DML
estimator, actual-estimator benchmark, Gate 2/3 approval, or scientific four-cell
results. Preksha's Week 2 branch remains separate. The scientific next steps and
open team decisions below still apply.

## Current milestone

The user authorized merging the two foundational packages into main. Preksha's
Week 1 generator is merged via PR #2 at `9e810790867dcfb2973bfa0662c2fc429562730b`.
This revision combines that component with Deeptanshu's GARCH, diagnostics, metrics
and protocol draft through PR #3. The full ignore policy is preserved. Preksha's
additional Week 2 prototypes remain on their separate branch.

New diagnostics resolve the current committed regime source and record its exact
SHA/hash, avoiding dependence on a feature-branch object after squash merges.
The integrated event mapping, DGP freeze and scientific gate decisions remain
pending; merging components does not supply that sign-off.

| Responsibility | Artifact | Verification |
| --- | --- | --- |
| Week 1 GARCH and coefficient mapping | `src/dgp/volatility.py` | Exact recurrence, scale, shapes, replay, burn-in and moment tests; official-source parity |
| Volatility/return plots and persistence comparison | `src/dgp/validate_volatility.py` | Five persistence settings, two burn-ins, 32 independent panels per setting; separate seed corroboration |
| Week 2 stability/pathology evidence | `results/tables/week1_week2_validation.json`, matching raw summaries | No numerical failures; large returns logged and retained |
| Volatility/regime separation and positive control | `src/dgp/independence.py` | Actual pinned regime source; 100 independent/control panels per seed, full-process randomization; stream replay |
| Coverage, size, MCSE and paired comparisons | `src/evaluation/metrics.py` | Known mock outcomes, failure/denominator handling, CSV recomputation and ID alignment tests |
| Monte Carlo protocol draft | `docs/DECISIONS.md`, P5 | Concrete budgets, materiality, failure policy and diagnostic threshold proposals; team lock pending |
| STRETCH runtime scaling | Raw runtime tables in each run | Firm/period grid timed locally; not a DML runtime estimate |
| STRETCH fold-split review | Not available | No Mirun DML/fold implementation in fetched refs |

Read [the deliverable report](../reports/deeptanshu_week1_week2.md) for results,
commands, limitations and figures. The README documents the actual current APIs.

## Publication and integration review

Implementation commit `bad08cd8a1402cacc77ba6bea715fc4c74a85b05` was pushed and its
remote SHA verified. [PR #3](https://github.com/Mirunjai/dml-regime-dependence/pull/3)
delivers the volatility/metrics package and the integration update against the
regime component merged in PR #2. The user authorized these selected component
merges; this revision contains the combined baseline.

Two temporary combinations were tested without committing either merge:

- Preksha's Week 2 branch at `8144aba`: automatic merge without conflicts,
  **119 tests passed** with warnings treated as errors, plus a direct-import toy
  composition of GARCH returns, regime shocks and the classical prototype.
- Her [PR #2](https://github.com/Mirunjai/dml-regime-dependence/pull/2)
  originally used the Week 1 branch at `17b42c0`, with a `.gitignore` rename/add conflict.
  Retaining our full ignore file preserves every pattern from her minimal file
  and the raw-data/credential exclusions. With that temporary resolution,
  **112 tests passed** with warnings treated as errors.

Recommendation: combine reviewed component PRs into main, preserving the full
ignore policy. The PR #2 ignore policy was restored before its merge, avoiding
that conflict when the new main was merged into our branch. Her additional Week 2
prototypes need their own reviewed change; they are not in PR #2. These checks
establish code coexistence, not an approved
integrated DGP, event-window mapping, or Gate 2/Gate 3 decision. Temporary review
worktrees are cleaned after testing. The temporary trials did not alter teammate
branches; the later user-authorized PR #2 update restored its full ignore policy
without changing the regime implementation.

## Evidence and checks

- **113 combined tests passed at the prior component milestone**, including the eight regime tests and a new
  regression for a repository without the original feature-branch commit. The
  original standalone suite had 104 tests. Warnings are treated as errors: `.venv/bin/python -m pytest -q -W error`.
- Compared the actual official `arch.univariate.GARCH.simulate` API across 16
  persistence/variance/burn-in combinations: matching returns, maximum absolute
  variance difference about 8.9e-16. Its source clone was not edited; the unbuilt
  source's missing version metadata was supplied in-process. Optional check script
  and its provenance are retained.
- Primary seed 20261031: average squared returns 1.0002-1.0024 for intended variance
  1; zero numerical failures; 6/100 independent detections and 100/100 deliberately
  dependent-control detections at diagnostic alpha .05.
- Corroboration seed 20261101: average squared returns 0.9997-1.0006; zero numerical
  failures; 5/100 independent detections and 100/100 controls detected. Its config
  and screening proposals were recorded before execution, not team-approved.
- Independent raw-summary/MCSE/p-value recomputation and exact selected-series
  replay from extracted source snapshots passed for both roots. Links, figures,
  ignore boundaries and the full diff were reviewed. All-failed and one-usable-panel
  reporting paths have dedicated regression tests.
- Scope re-audit corrected two edge cases: stable near-boundary coefficient/moment
  arithmetic (checked against high-precision Decimal), and removal of obsolete
  optional outputs on explicit overwrite. User-created files are preserved.
- Finite-series ACF sensitivity was investigated rather than hidden: rho=.97
  sample lag-1 ACF approaches the population .2169 as series length increases.
- Raw data retain per-replication summaries, all extreme counts and up to 100
  extreme examples per panel with truncation flags, selected series, exact configs,
  seeds, source/protocol snapshots and hashes. Full panels are streamed, not saved.
- `.gitignore` now has the correct filename. Local environment, Python caches and
  raw artifacts are excluded. Only small report summaries/figures are intended
  for review. Development-run outputs are archived under ignored raw storage.

The local `.venv` uses system-site scientific packages (Python 3.13.13, NumPy
2.3.5, Matplotlib 3.11.1); pytest 9.2.0 and its small dependencies were installed
locally from copied cache entries. No global packages were changed. DNS blocked
package downloads and remote checks during validation; branch publication was
subsequently verified through normal Git push and the GitHub API. No clean online
installation was verified.
Exa failed during the audit; relevant original papers and official web references
were read through web search. See the decision notes for those sources.

## Repository audit and teammate dependencies

Base main: `77a10eb739cb6630dbd736037158e528f9d69463`. The initial main had only
README/contribution/templates/config files; its README described unimplemented
modules and its ignore patterns were incorrectly named `gitignore`.

Fetched teammate refs:

- `origin/preksha/regime-shock-module`:
  `17b42c0408b9b512da029f70da3a619706e6649b`. Generator, demo, tests and `.gitignore`.
- `origin/preksha/week2-validation`:
  `8144abad3e4cf338f1fcd24096d2feabdb397745`. Additional diagnostics and prototypes;
  relevant regime files were inspected, not a complete review of the branch/data.

No prior GARCH source was found, so the authorized standalone implementation was
written fresh. Preksha's source is imported temporarily from its exact Git object
and snapshotted in ignored raw outputs. Its Week 1 code is now merged via PR #2;
the separate Week 2 branch remains unmerged. Formal DGP freeze is still pending.
The diagnostic aligns one time index to one window index; it cannot
resolve the integrated calendar/event-window mapping.

The local brief, one-pager, detailed methodology, both weekly plans and Bollerslev
(1986) paper remain source materials in the parent directory, outside Git.
`references/arch` is also a sibling clone, not nested in the project. No dataset
or third-party implementation has been ported into project source.

## Open team decisions

- Supply the missing authoritative `docs/gate1_specification.md` and any actual
  Gate 2/3 decision memos. The supplied plans report Gate 1 as locked; a scheduled
  checkpoint does not establish later gate completion.
- Approve the integrated DGP freeze, date/window mapping and grouping
  unit. Its exposure fraction and realized same-regime pair density differ;
  changing regime count at fixed exposure fraction changes pair density.
- Approve or revise the final grid, robust variance, zero/nonzero-effect conditions,
  replication budget, materiality/failure policy and manipulation-check thresholds.
- Mirun's full pipeline/runtime and fold code are not available here. Do not infer
  a DML budget from the volatility-only timings.
- Confirm the official submission deadline. The Week 2 plan's 1 November design
  lock and 8 November result-freeze dates are targets, not verified outcomes.

No final DML ablation, real-data analysis, estimator coverage claim, or gate
approval is implied by this component milestone.
