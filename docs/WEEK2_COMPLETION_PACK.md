# Project A — Week 2 Completion Pack

**Prepared:** 4 November 2026  
**Owner:** Mirun  
**Status:** Completion-ready draft; team approvals and missing teammate artifacts remain open.

## Executive status
Mirun's implementation is committed and pushed on `mirun/week2-consolidated-completion` at `26e65f1`; reported tests: `171 passed, 14 warnings`. This is code delivery, not automatic scientific gate approval. Gate 2 is **CONDITIONAL** pending the missing independence positive-control, treatment-timing independence, baseline sanity evidence, and team decision. Gate 3 below is a proposal until approved.

## Gate 2 memo — evidence and status

| Check | Evidence | Assessment |
|---|---|---|
| Persistence | ACF5 squared returns rises 0.0075 → 0.1654 as configured persistence moves 0.50 → 0.98 | Encouraging; require stability/pathology and unchanged unconditional-variance report |
| Density | K=4 overlap across configured density 0/.1/.25/.5/.75: 0/.1657/.3140/.5670/.8230 (100 seeds) | Monotone response; define independent manipulation check and threshold |
| Regime count | At density .5, overlap changes .5221 (K=1) to .9053 (K=32) | Not matched density; cannot isolate independent information |
| Matched density | Gamma ablation K4 configured density .428846; K16 .248075 | State exact matched quantity and report other realized quantity |
| Volatility–shock independence | [Week 1/2 component report](../reports/deeptanshu_week1_week2.md) and [review](../reports/mirun_week2_review.md) are present | Component evidence available; calendar-model integration/decision still OPEN |
| Treatment timing independence | Final Preksha report not supplied | OPEN |
| Baseline known-truth sanity | Gamma=0 evidence exists; exact final baseline sanity package not established | OPEN: bias/RMSE, coverage and zero-effect size under locked DGP |
| Membership | K4: 0 multi-regime events; K16: 12/80,000 (0.015%); calendar-window overlap pairs 3.489% | Near-single-membership limitation; team must decide whether this represents intended mechanism |

**Recommendation:** Do not mark Gate 2 PASS until open items are attached or explicitly resolved by a team decision.

### DML evidence caveats
200-replication gamma-ablation coverage, ordered random-naive / random-robust / grouped-naive / grouped-robust:

| Configuration | Coverage |
|---|---|
| K4 gamma=0 | 97.0 / 94.5 / 94.5 / 94.0% |
| K4 gamma=1 | 82.0 / 90.5 / 73.0 / 86.5% |
| K16 gamma=0 | 96.5 / 97.0 / 95.5 / 95.5% |
| K16 gamma=1 | 91.5 / 93.5 / 94.0 / 94.5% |

At n=200 and p=.95, binomial MCSE ≈1.54 percentage points (95% margin ≈±3.0 points). Treat as exploratory, not decisive. Factor ablation (50 reps) is exploratory and not a pure dependence-only intervention because `sd_factor` changes from .5 to 0, removing a variance component too.

**Version control warning:** `week2_mirun` uses one-way CR1 by first overlapping regime label. `week2_completion` uses full membership and multiway inclusion–exclusion. Choose one as primary; never pool them silently.

## Gate 3 design-lock draft

### Four cells
1. Random folds + naive variance
2. Random folds + robust variance
3. Grouped-by-regime folds + naive variance
4. Grouped-by-regime folds + robust variance

Primary contrast: Cell 2 vs Cell 4. Primary outcome: 95% CI coverage. Key diagnostic: empirical size under a separate zero-effect condition. Secondary: bias, RMSE, width, power and fold sensitivity. Width/power alone do not count as benefit.

### Proposed reduced grid (team ratification required)
- Persistence: two validated low/high settings from the completed stability sweep; exact values require Deeptanshu's report.
- Dependence: at least three independently calibrated realized-dependence levels (low/medium/high), holding persistence fixed for H1.
- Regime count: K=4 and K=16, matched on a pre-declared dependence quantity; report the non-matched quantity too.
- Effect conditions: locked non-zero effect for coverage; zero effect for empirical size.
- Replications: select from measured runtime and MC precision. Proposed target MCSE ≤1 percentage point near 95% coverage: n≈475; round to 500 per cell/configuration if runtime allows. At n=200 MCSE≈1.54 pp. If lower, record and disclose precision.
- Randomness: independent reproducible streams by replication/component; save raw estimate, CI bounds, seed, config, cell and diagnostics.

### Mandatory estimator decision
Choose one primary robust estimator:
- Option A: one-way CR1 by first overlapping regime label.
- Option B: multiway inclusion–exclusion score sandwich using full event-to-regime membership.

Record cluster definition, finite-sample correction, critical-value/df rule, code version and assumptions. The near-single-membership diagnostics mean the current DGP may not meaningfully exercise multiway membership.

### Proposed pre-specification
- Manipulation check: independent realized-dependence statistic must order low < medium < high; threshold fixed before full run.
- Material difference: proposed ≥3 percentage-point absolute coverage difference AND 95% uncertainty interval for the difference excludes zero. Ratify before full results.
- Additional grouped-fold benefit: Cell 4 must improve coverage closeness to .95 over Cell 2 without materially worsening empirical size.
- If naive coverage remains nominal, first require a passed manipulation check; otherwise classify as DGP failure, not a DML finding.
- Benchmarks: same panel, treatment effect, event window, dependence realization and evaluation target; SC placebo inference plus donor-pool diagnostics. Contextual only, not a horse race.
- Pilot: all four cells; save raw replication-level outputs; independently recompute coverage/size; replicate a selected pilot from exact config+seed. Pilot is for pipeline/runtime only.

## Team close-out tracker

| Owner | Required artifact | Current status from reviewed evidence | Close-out |
|---|---|---|---|
| Mirun | DGP v0, Gate 2 memo, DML toy run/runtime, Gate 3 draft | Code pushed; 171 tests pass; formal runtime note and gate memos need repository inclusion | Add memo, runtime evidence, version/tag and team decision |
| Deeptanshu | Stability/independence report, positive control, coverage/size code, MC protocol | Available in [report](../reports/deeptanshu_week1_week2.md), `src/evaluation/metrics.py`, and DECISIONS P5 | Attach to review; apply separately to the calendar model |
| Preksha | Density/regime validation, matching proposal, treatment independence, S&P source/schema, classical toy prototype | Not supplied in reviewed evidence | Attach outputs and schema |
| Sudarshan | Runner, raw-results schema, 2×2 mock tables/plots | Reviewed and merged in PR #4; [evidence](Sudarshan_INFRA.md) records deterministic resume and streams | Integrate actual research records; mock results are not DML evidence |

## Decisions requiring team approval
1. Deeptanshu's independence positive-control and stability results.
2. Preksha's treatment-timing independence and matched-density report.
3. Primary robust estimator/version.
4. Gate 2 PASS/CONDITIONAL decision.
5. Final grid, matching quantity, MC precision and material-difference threshold.
6. Benchmark subset and comparability definition.
7. Official submission deadline and format confirmed with staff.

## Copy/paste team message
Week 2 integration is ready for close-out. My branch `mirun/week2-consolidated-completion` is pushed (`26e65f1`; 171 tests passed). I have prepared the Gate 2 evidence memo and Gate 3 design-lock draft. Please send/confirm: Deeptanshu — persistence stability, unchanged unconditional variance, volatility–regime independence positive control, tested coverage/size code and MC protocol; Preksha — treatment-timing independence, realized-dependence validation, matched-density K comparison, S&P inclusion source/schema and classical toy prototype; Sudarshan — runner raw-output/resume/seed check and 2×2 mock table/plot. At review we must decide Gate 2 status, primary robust variance version, final reduced grid, replication precision, material-difference rule, manipulation-check threshold and benchmark subset. Mark items DONE only with an artifact/link.

## Week 2 exit criteria
- Gate 2 memo reviewed and decision recorded.
- DGP version/commit identified; original and revised implementations distinguished.
- All four DML cells run on toy data; per-replication runtime measured.
- Primary robust estimator and fold construction precisely specified.
- Gate 3 grid, matching quantity, replication budget, thresholds, zero-effect condition and benchmark subset approved.
- Team artifacts received or explicitly waived with reason and fallback.
- Official deadline/format confirmed with staff.

## Integration review clarification (4 November)

The reviewed research-code fixes are described in
[the review memo](../reports/mirun_week2_review.md). Existing Deeptanshu artifacts
were already on main; absence from the original handoff is not absence from the
repository. They establish component behavior, not approval of this different
calendar-time model. The archived 'no dependence' run retains a calendar factor.
The original one-way and full-membership variants remain separate.

This proposal's 3pp rule and 500-rep precision suggestion differ from DECISIONS P5;
the team must reconcile them before a final run. Regime-only versus calendar-factor
conditioning/grouping, the fixed-alpha versus canonical GARCH family, primary
variance, thresholds and the robustness subset remain decisions, not silent code
changes. No approval is supplied by this clarification.
