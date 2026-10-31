# Project state

Updated 31 October 2026. Branch: `deeptanshu/garch-validation-audit`.

## Current milestone

The user approved the implementation proposal and requested Deeptanshu's Week 1
and Week 2 package. The standalone code, diagnostic evidence and protocol draft
are ready for review. Week 2 checking against a confirmed team-frozen module and
the integrated event mapping is still pending; the pinned-source diagnostic does
not close that dependency. Integrated scientific sign-off remains a team responsibility.
The user has authorized committing and pushing this implementation branch. Validation
snapshots predate the first implementation commit. No merge into main or edits to
teammates' source have been authorized or performed.

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
remote SHA verified. [Draft PR #3](https://github.com/Mirunjai/dml-regime-dependence/pull/3)
targets main; no main merge has been performed.

Two temporary combinations were tested without committing either merge:

- Preksha's Week 2 branch at `8144aba`: automatic merge without conflicts,
  **119 tests passed** with warnings treated as errors, plus a direct-import toy
  composition of GARCH returns, regime shocks and the classical prototype.
- Her existing [draft PR #2](https://github.com/Mirunjai/dml-regime-dependence/pull/2)
  is the older Week 1 branch at `17b42c0`. It has a `.gitignore` rename/add conflict.
  Retaining our full ignore file preserves every pattern from her minimal file
  and the raw-data/credential exclusions. With that temporary resolution,
  **112 tests passed** with warnings treated as errors.

Recommendation: combine reviewed component PRs into main, preserving the full
ignore policy. Her additional Week 2 prototypes need their own reviewed change;
they are not in PR #2. These checks establish code coexistence, not an approved
integrated DGP, event-window mapping, or Gate 2/Gate 3 decision. Temporary review
worktrees are cleaned after testing; teammate branches remain unchanged.

## Evidence and checks

- **104 tests passed**, including subprocess CLI checks, with warnings treated as
  errors: `.venv/bin/python -m pytest -q -W error`.
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
and snapshotted only in ignored raw outputs. It remains unmerged and not confirmed
team-frozen. The diagnostic aligns one time index to one window index; it cannot
resolve the integrated calendar/event-window mapping.

The local brief, one-pager, detailed methodology, both weekly plans and Bollerslev
(1986) paper remain source materials in the parent directory, outside Git.
`references/arch` is also a sibling clone, not nested in the project. No dataset
or third-party implementation has been ported into project source.

## Open team decisions

- Supply the missing authoritative `docs/gate1_specification.md` and any actual
  Gate 2/3 decision memos. The supplied plans report Gate 1 as locked; a scheduled
  checkpoint does not establish later gate completion.
- Identify/approve a frozen regime version, the date/window mapping and grouping
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
