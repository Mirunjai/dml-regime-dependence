# Preksha Week 2 integration review — 8 November 2026

Reviewed branch `preksha/week2-validation` at
`8144abad3e4cf338f1fcd24096d2feabdb397745`, against main `48a28e7`.
No remote branch had new code since the 4 November review. Preksha's previously
unmerged Week 2 delivery is integrated and corrected in this review branch;
her remote branches remain unchanged.

## Scope and source verification

The branch adds an event-index dependence diagnostic, a pair-density feasibility
scan, a treatment/exposure association diagnostic, a descriptive market-model
event-study prototype, seven inclusion-event records, and an event-list schema.
These are standalone prototypes, not a frozen calendar-time DGP, final benchmark
campaign, labelled return dataset v1, or scientific gate approval.

The seven records' tickers, addition status, announcement dates and effective
dates match the two primary S&P announcements, checked 8 November:

- [S&P, 6 September 2024](https://press.spglobal.com/2024-09-06-Palantir-Technologies,-Dell-Technologies,-and-Erie-Indemnity-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600):
  PLTR, DELL and ERIE, effective 23 September.
- [S&P, 7 March 2025](https://press.spglobal.com/2025-03-07-DoorDash,-TKO-Group-Holdings,-Williams-Sonoma-and-Expand-Energy-Set-to-Join-S-P-500-Others-to-Join-S-P-100,-S-P-MidCap-400-and-S-P-SmallCap-600):
  DASH, TKO, WSM and EXE, effective 24 March.

The list is a small curated sample, not a complete inclusion universe. It has
no stock/market return observations, residuals, or calm/turbulent labels.
Schema validation is separate from verifying claims against source documents.

The event study uses pre-event OLS alpha/beta, abnormal returns and their
arithmetic cumulative sum, as described in MacKinlay (1997), *Event Studies in
Economics and Finance*, Sections 3–4 ([paper](https://www.bu.edu/econ/files/2011/01/MacKinlay-1996-Event-Studies-in-Economics-and-Finance.pdf)).
No new CI, p-value or claim of comparability with DML is added. Inputs must be
aligned and share units/return convention; CAR is not a compounded buy/hold return.

## Reproduced issues and corrections

| Finding | Correction |
| --- | --- |
| `save_events` consumes generators during validation and then writes only a header | Materialize once, validate all rows, and write the retained rows |
| Invalid extra fields or interrupted writing can truncate a prior CSV | Validate the complete schema first; write a temporary file and replace atomically |
| Whitespace fields, compact dates, incomplete URLs and duplicate events are accepted | Require nonempty strings, canonical dates, HTTP(S) hostname, expected columns and unique event identities |
| Constant exposure yields `NaN` and divide warnings | Return explicit `None`; show defined/attempted counts in aggregate diagnostics |
| Pair-density implementations disagree on accepted inputs and accept fractional/invalid IDs | Reuse one validated 1-D integer-label helper; -1 is inactive |
| Regime/noise draws share a stream whose consumption changes across settings | Use separate recorded `SeedSequence(seed).spawn(2)` children for regime and firm noise |
| Boolean dimensions/density are treated as numerical generator settings | Reject boolean dimensions, boolean density and non-scalar density; valid-input generation is unchanged |
| Event-window floats/booleans cause inconsistent slicing or coercion | Require integer boundaries explicitly |
| Finite inputs can overflow into invalid OLS/CAR outputs | Fail explicitly on unrepresentable arithmetic; no clipping or successful nonfinite result |
| Closest density grid point can be mistaken for an attainable match | Report the balanced generator's maximum and whether the target exceeds it |
| Old `.gitignore` conflicts with current protection rules | Preserve current main's complete ignore policy |

The dependence toy's RNG correction intentionally changes its numerical demo
output. This is not an exact replay of prior toy numbers. The production
volatility, DML, metric and infrastructure implementations are unchanged.

For the existing demonstration with 1,000 windows and target pair density .0495,
the maxima for K=20 and K=50 are approximately .04905 and .01902. Thus those
targets are unattainable with this balanced single-membership generator. Pair
density is fixed by group sizes; its zero SD across seeds does not validate shock
independence or prove the integrated DGP has the intended dependence.

## Validation

The previous main passed **283 tests**. Trial integration of the original branch
passed **290 tests**; 27 new review cases bring the combined suite to **317 tests
passing with warnings treated as errors**, using the existing local environment
(Python 3.13.13, NumPy 2.3.5, SciPy 1.16.3, scikit-learn 1.7.2, pytest 9.2.0).
No global packages were changed. The original seven event-study cases remain.

New cases cover generator retention, prior-file preservation, interrupted-write
cleanup, schema/URL/date validity, duplicate events, direct unordered pair counts,
malformed IDs, undefined endpoint associations, Boolean settings, integer event
windows, no event-effect leakage into fitting, and overflow failures. Every new
CLI demonstration executed successfully:

```bash
python -m pytest -q -W error
python -m src.benchmarks.event_study
python -m src.dgp.week2_diagnostics
python -m src.dgp.validate_dependence
python -m src.dgp.matched_density
```

The injected-event toy reports CAR .141336 for an injected arithmetic effect .12;
the difference includes estimation error and simulated noise, not a failed
known-truth estimator calibration test. Exact no-noise regression fixtures recover
the known alpha/beta and six-day CAR .12. Raw bug reproductions and branch audit
evidence remain under ignored `results/raw/week3_final_review_20261108/`.

## Other branch review and cleanup

Sudarshan PR #8 points to `0f11603`, exactly the same tree merged by PR #4 at
`6c5ff70`. It was closed as a duplicate; rebasing or merging its old files would
add no implementation and could conflict with later work. The teammate branch
was retained. Mirun's current branch ends at `a84b548`, already included in PR #5.

Only these merged user-owned branches were selected for deletion:

| Branch | Merged PR | Proof |
| --- | --- | --- |
| `deeptanshu/garch-validation-audit` | #3 | Identical tree to `566ad07` |
| `deeptanshu/mirun-integration-review` | #6 | Identical tree to `0efe494` |
| `deeptanshu/week3-verification-audit` | #7 | Identical tree to `48a28e7` |

All three were removed locally and remotely after a verified complete Git bundle
was saved in the ignored review evidence directory. Ownership was established
from branch namespace and merged PR authorship, not just the latest commit's
author: some teammate branches contain earlier review commits by Deeptanshu.
The current review branch can also be removed after its result is merged.

## Remaining Week 3 scientific inputs

No approved Gate 2/3 design, agreed robustness subset, original production raw
archive, or labelled daily-return panel was found in the current remote branches.
Preksha's seven-event CSV does not resolve that dependency. The independent
verification/monitoring and real-panel diagnostic software are implemented.
Executing final robustness jobs and actual calm/turbulent comparisons requires
the dated team decisions and return data described in `reports/deeptanshu_week3.md`.
The remaining experiments are not represented as complete.
