# Gate 3 design PROPOSAL (Mirun) — not approved

Machine-readable form: `configs/mirun_gate3.yaml` (every tunable value has `approved: AWAITING_TEAM_APPROVAL`). Nothing here is an approved primary configuration; the team (Mirun, Deeptanshu, Preksha, Sudarshan) must ratify before any production run. The original proposal/Gate 1 document is not in the repo; wording from `docs/WEEK2_COMPLETION_PACK.md` (an unratified draft) is marked as such.

## 1. Evidence-backed facts (executed or read)
| Fact | Evidence |
|---|---|
| Four cells, locked 2x2; primary contrast = random+robust vs grouped+robust; coverage primary, size key diagnostic | `AGENTS.md` (Gate 1 locked), runner `CELL_SPEC` |
| Candidate DGP/DML: `research/week2_completion` (multi-membership, per-cell failures, fold provenance) | `reports/mirun_dgp_comparison.md` |
| Naive miscalibration appears only for gamma>0; gamma=0 naive cover .92-.97 | pilots (`reports/mirun_pilot_reproduction.md`), session-3 mechanism runs |
| All four cells undercover under the calendar DGP at gamma=1 (robust .81-.905, K4-K16, d=.5/.75, 200 reps) | `results/tables/mirun_failure_rate_scan.json`, grouped-folds report B |
| Overlap sandwich: 0/2,000 fitted-cell failures | grouped-folds report A |
| Grouped folds inflate sd(tau-hat) up to 1.23x at K=4; ~1.06-1.07 at K=16; due to alignment with true regimes, not fold size | grouped-folds report C |
| Cost 0.68 s per replication (all 4 cells), single core | measured |
| Pilot raw seeds used: 10000+, 20000+, 30000+ | scripts |

## 2. Proposed choices (Mirun's suggestions, each needs approval)
- **DGP:** `week2_completion` calendar DGP as-is (no change), n=400, T=260, H=5, p=5, fixed-alpha GARCH alpha=.10, persistence .90 (4th moment finite), sd_shock=.40.
- **Treatment assignment:** logistic in X plus gamma x regime random effect (existing). **Effect:** tau=1 (coverage/power conditions), tau=0 in a separate null condition for empirical size. Truth is used only in evaluation.
- **Dependence manipulation:** density in {.25,.50,.75} (calendar fraction) x K in {4,16}. Report realized exposed share and pair density alongside; which quantity is "matched" is unresolved (sec. 3).
- **gamma:** {0 control, 1}. Must be declared before looking at primary results.
- **Estimator:** RF nuisance (40 trees), 5 folds, normal 95% interval, overlap-sandwich as "robust" variance (existing code, unchanged).
- **Replications:** 1000 per condition (MCSE <= 0.7 pp near .95; 970 needed); minimum acceptable 500 (MCSE 1 pp; 475 needed). 24 conditions x 1000 x 0.68 s ~ 4.5 h per core. Observed paired-contrast SE was .012-.019 at 200 reps; scaled by 1/sqrt(n), ~.008-.012 at 500 and ~.005-.009 at 1000.
- **Seeds:** `seed = root_seed + replication_id`; identical worlds across cells (paired); independent named RNG streams are created inside the DGP by `SeedSequence.spawn`. Root seed to be chosen and recorded before running (not 10000-10199, 20000-20019, 30000-30199).
- **Paired comparisons:** by replication id using `paired_binary_difference` (never two independent binomial SEs); also paired contrasts for naive-vs-robust within each fold scheme.
- **Outcomes:** primary 95% coverage; key null empirical size; secondary bias, RMSE, width, power, failure rate, fold diagnostics. Width/power alone never count as benefit.
- **Failure policy:** retain all failed cells; denominator = attempted; report conditional-on-success and all-attempted bounds; no silent retry; proposed ceiling 2% (observed 0/200).
- **Robustness subset:** factor-off (`sd_factor=0`), 10 folds, a second learner; each a separate labelled condition, never pooled with primary.
- **Acceptance (draft from the Week 2 pack, unratified):** material difference = |paired coverage diff| >= 3 pp AND 95% interval for the paired difference excludes 0; grouped must also not worsen size. If naive coverage stays nominal under the manipulation, classify as DGP failure, not a DML finding. "Similar performance of the robust cells" is a valid outcome.

## 3. Unresolved choices (need decisions; my findings bear on them)
1. **Is the shared calendar factor part of the intended dependence?** Factor-off check (200 reps, K=4/16): coverage does not improve (robust K4 .83/.785, K16 .855/.885), so the factor does not explain the undercoverage; the choice mainly affects realism, not the headline. The *cause* of robust undercoverage (few effective clusters under CR0+normal? finite-sample DML bias?) is still untested and should be diagnosed before the design is frozen.
2. **Estimator:** keep CR0-normal overlap sandwich, or CR1/t(G-1)/factor-aware alternative? Alternatives are a separate proposal; switching estimator after seeing results is not allowed.
3. **Density quantity** to manipulate/match (calendar fraction, exposed share, pair density) and the manipulation-check threshold.
4. **Canonical vs fixed-alpha GARCH** (not yet tested on identical seeds; requires a DGP change).
5. Learner and fold-count fixed vs robustness only; whether grouped folds should also address calendar-factor leakage (7-70% of calendar-shared pairs cross folds).
6. gamma value(s) and whether gamma>0 is a defensible "regime-clustered financial events" mechanism.

## 4. Approvals required
Gate 2 closure (incl. the undefined "11 checks"), Gate 3 ratification of every `AWAITING_TEAM_APPROVAL` value, root seed, and independent audit by Deeptanshu before the production run. Recorded in `docs/DECISIONS.md` by the team, not by this report.

## 5. Engine integration plan (see `src/infra/dml_engine.py`)
1. Do not edit `experiment_runner.py`: it validates `engine == mock` and mock DGP YAML. A separate `calendar_dml` engine emits the **same per-cell schema** (`cell, status, estimate, lower, upper, error`) so existing readers can parse it.
2. Guard: production run refused unless `approval.gate2/gate3` are set and no parameter's `approved` is `AWAITING_TEAM_APPROVAL`; `--smoke` (<=20 reps) may use `proposed`, writes under a `smoke` directory and is labelled exploratory.
3. Per-replication atomic JSON, resumable, deterministic seed, config hash and git state in a manifest, failures kept, source-change invalidation.
4. Aggregation through `src/evaluation/metrics` (`summarize_intervals`, `paired_binary_difference`), not a new metric engine.
5. Proposed small, separately reviewed change for Sudarshan: allow `engine in {"mock","calendar_dml"}` in `validate_config` so `ablation_report` can render the 2x2 report; until then the engine ships its own table.

## 6. Session 4 findings that bear on this proposal (exploratory; see `reports/mirun_undercoverage_diagnosis.md`)
- Existing CR0-normal robust variance: size .143/.151 (random/grouped) at K=4, gamma=1 and .087/.083 at K=16 (1000 reps, nominal .05). Paired grouped-random difference not detectable at gamma=1; grouped robust over-sized at the gamma=0 control (+.030 +- .010, 500 reps).
- Undercoverage is a variance-estimation problem (SE/sd .69-.90), not nuisance bias (oracle nuisance and a second learner do not fix it; bias <= .13 sd), and not the calendar factor.
- **Decision needed before any production run (unresolved choice 2 becomes binding):** keep CR0-normal, or adopt/reject a separately labelled t(G-1) or CR1-regime+t(G-1) proposal. Trade-off measured: near-nominal size at K=16 (n>=1000) but conservative at K=4 (size .01-.02) with power .34-.65 vs .69-.83. Switching after seeing production results is not permitted.
- Add n (400 vs 1000) to the robustness subset: the K=16 deficit shrinks with n, the K=4 deficit does not.
- Runtime corrected: 24 x 1000 x 0.68 s = 16,320 s = 4.53 h (0.68 s = one run_dml call = all four cells).

## 7. Session 5 design additions (proposals; the YAML `analysis_tiers`, `compute`, `output_schema`, `acceptance_rules` carry each with `approved: AWAITING_TEAM_APPROVAL`)
**Tiers.** Primary (K x density x gamma grid, tau=1 coverage and tau=0 size); negative controls; sensitivity; separately labelled estimator proposals. Pilot results must never be pooled into any tier.
**Negative controls (new).** `independent_control` = default Config with `sd_factor=0, sd_shock=0, gamma=0` (regime layout kept, but regimes carry no shock and no treatment effect, so data are independent across events apart from GARCH heteroskedasticity); `factor_only` = `sd_shock=0, gamma=0`. The original benchmark conditions are preserved unchanged (default Config, gamma=0 baseline). Only these three Config parameters change across the independent control; nothing in code changes.
**Pilot evidence for the controls** (200 reps, seeds 70000+, K=4, d=.5, n=400, tau=1; `results/tables/mirun_session5_controls.json`): independent control naive .930/.900 (random/grouped), existing robust .870/.875; factor-only naive .945/.940, robust .890/.880; default benchmark naive .740/.650, robust .815/.795. The independent control exposes that the existing CR0-normal robust cell already undercovers with *no* dependence (a few-cluster property), so the central robust-vs-robust contrast is confounded by that flaw unless the estimator question (sec. 3, item 2) is settled first.
**Factor ablation.** The earlier factor-off run lowered outcome variance as well as removing the factor. The variance-matched condition (`sd_factor=0`, `sigma2_bar=1.29`, calibrated so outcome-noise variance equals the default's: 8.21) reproduces the default's sd(tau-hat) (.556 vs .551) and coverage (robust .805/.785 vs .815/.795; unmatched .79/.78), so the ablation was not confounded by variance and the factor is not the mechanism.
**Identification caveat.** Multi-regime events are 0/80,000 at K=4 and 280/80,000 (0.35%) at K=16 (default density .5); calendar-window overlap share 3.48%. The multi-membership structure that separates the overlap sandwich from plain CR is barely exercised; the grouped-vs-random contrast is identified mainly through K and gamma, not membership overlap. Raising overlap would be a design change and must be documented as one.
**Seeds / pairing.** Same world (seed = root + replication) for all four cells within a condition; across conditions the same root block gives common random numbers only where parameters share the stream layout (documented, not assumed).
