# Grouped cross-fitting and overlap-sandwich diagnostics (Session 2)

Status: **Executed, exploratory.** Structure-only (no nuisance fit). Script `scripts/mirun_fold_variance_diagnostics.py` (tests: `tests/test_mirun_overlap_sandwich.py`, 12 tests), output `results/tables/mirun_fold_variance_structure.json` (100 seeds, 20000-20099, defaults n=400,T=260,H=5, 5 folds, `week2_completion` DGP). Not a Gate 2 decision.

## Estimator facts (verified by execution/tests)
- The overlap "multiway" meat is `psi' A psi`, `A_ij = 1{events i,j share >=1 regime}`, no small-sample factor, normal critical value.
- With single membership it equals the CR0 cluster-sum (PSD). With multi-membership `A` can be indefinite: `{0},{0,1},{1}` has min eigenvalue 1-sqrt2 and returns meat -1 for psi=(1,-1,1). The code records this as a failed cell (not clipped).
- Dependence assumed: regime-only, cluster-type dependence. It does **not** model shared calendar factor F (`sd_factor=.5`). With K=4 clusters plus singletons, CR0 + normal quantile is expected to be anti-conservative (hypothesis, consistent with robust R/Rb .905 at K4 gamma1; untested directly).

## Structure across the grid (means over 100 worlds)
| K, density | comps | largest comp | exposed events | worlds with multi-regime | A not PSD | grouped fold max/min (median) | calendar-sharing pairs cross-fold: random / grouped |
|---|---|---|---|---|---|---|---|
| K4, .5 | 176 | 65 | 228 | 0% | 0% | 1.00 | .80 / .34 |
| K4, .75 | 74 | 93 | 331 | 0% | 0% | 1.39 | .80 / .07 |
| K2, .75 | 84 | 167 | 318 | 0% | 0% | **6.15** | .80 / .16 |
| K8, .75 | 54 | 69 | 354 | 38% | **38%** | 1.16 | .80 / .13 |
| K16, .5 | 113 | 31 | 303 | 43% | **43%** | 1.00 | .80 / .30 |
| K16, .75 | 27 | 81 | 383 | 100% | **100%** | 1.12 | .80 / .09 |
Full 16-cell table in the JSON.

## Findings
1. **Feasibility:** 5 grouped folds were feasible in every world (0% infeasible) because unexposed events are singleton components. "Grouped" thus means: whole regime blocks go to single folds; unexposed events are scattered. Session 1's "~28 components at density .75, K16" is confirmed (26.6).
2. **Balance:** near 1.0 except low K / high density (K2, d=.75: max/min 6x).
3. **Regime leakage:** grouped folds have 0 cross-fold regime-sharing pairs in all worlds (by construction). Random folds leak ~80% of such pairs.
4. **Calendar-factor leakage (new):** grouped folds do not eliminate it: 7-70% of event pairs with shared calendar dates remain cross-fold (random: 80%), because regime blocks are contiguous in time. The dependence the research question calls "dense common-shock" is only partly aligned with the units the folds separate. Whether this is intended is a **team decision**.
5. **PSD risk:** `A` is PSD (so meat cannot go negative) at K<=4 and low density; non-PSD is common at K>=8 with density >=.5. Non-PSD `A` is necessary, not sufficient, for failure; the actual failure rate under real scores is **not yet measured** (0 failures in all 5,040 legacy and 320 calendar reconstructed cells, but legacy uses CR1, and the calendar runs were K=4, d=.5 only).

## Why might grouped spread exceed random? (hypotheses, untested)
Pilot spread inflation appears only at gamma=1, K=4. H1: with gamma>0 a regime-level shifter of D is absent from X; a held-out whole regime is predicted by a model that never saw it, so D-tilde keeps a regime-level component that random folds partially absorb. H2: few large held-out blocks make the score sum noisier. H3 (excluded by data): fold imbalance (grouped fold max/min ~1.0 at K4,d=.5). Discriminating tests needed: an intervention putting regime effect into X (oracle-style, evaluation only), and fold-size-matched random blocks.

---
# Session 3 additions (executed, exploratory, calendar DGP only; legacy results not pooled)

## A. Empirical overlap-sandwich failure rate with real fitted DML scores
`scripts/mirun_failure_rate_scan.py` (resumable, unmodified `run_dml`, gamma=1, tau=1, n=400, 5 folds, seeds 30000+rep, 200 reps per setting; summary `results/tables/mirun_failure_rate_scan.json`).

| K, density | reps with a multi-regime event | failed multiway cells random / grouped (of 200) | 95% Wilson upper bound | median SE(multiway)/SE(naive) random / grouped |
|---|---|---|---|---|
| K4, .5 | 0% | 0 / 0 | 1.9% | 1.15 / 1.32 |
| K8, .5 | 0% | 0 / 0 | 1.9% | 1.19 / 1.28 |
| K8, .75 | 28% | 0 / 0 | 1.9% | 1.37 / 1.53 |
| K16, .5 | 48% | 0 / 0 | 1.9% | 1.16 / 1.20 |
| K16, .75 | 100% | 0 / 0 | 1.9% | 1.30 / 1.35 |

**No numerical failures in 2,000 fitted cells.** A non-PSD overlap matrix (previous section: 38-100% of worlds at the high-K/high-density settings) did not translate into negative meat, because the scores within a regime are positively correlated, which makes the meat large and positive here. Failure correlation with K/density/overlap/fold assignment cannot be assessed (zero events). Limits: gamma=1, tau=1 only; failure under other DGP settings (gamma=0, null effect, heavier tails) is untested, and a non-PSD matrix remains a theoretical hazard. This does not show the estimator is valid; see C.

## B. Calendar-DGP coverage and spread (same scan, truth tau=1, 200 reps; not an approved design)
| K, d | cov R/N | R/Rb | G/N | G/Rb | sd(tau-hat) R / G (ratio) | paired G-R robust coverage |
|---|---|---|---|---|---|---|
| K4, .5 | .755 | .850 | .610 | .810 | .518 / .638 (1.23) | -0.040 +- .019 |
| K8, .5 | .765 | .860 | .725 | .850 | .484 / .545 (1.13) | -0.010 +- .012 |
| K8, .75 | .720 | .840 | .620 | .845 | .610 / .709 (1.16) | +0.005 +- .015 |
| K16, .5 | .850 | .895 | .820 | .905 | .411 / .441 (1.07) | +0.010 +- .014 |
| K16, .75 | .815 | .875 | .790 | .885 | .487 / .515 (1.06) | +0.010 +- .016 |
**All four cells undercover in every setting (robust .81-.905).** The robust estimator does not restore nominal coverage under this DGP. The grouped spread inflation shrinks as K grows (1.23 -> 1.13 -> 1.07 at d=.5), reproducing the legacy-DGP pattern (legacy K4 gamma1 ratio 1.19, K16 1.0). The K4 paired robust difference equals the legacy value -0.040 +- 0.019 to three decimals; treated as coincidence of two different DGP/estimator pairs, not as one result.

## C. Mechanism interventions (`scripts/mirun_grouped_spread_mechanism.py`, test `tests/test_mirun_mechanism_folds.py`)
K=4, d=.5, calendar DGP, same worlds for all variants; only folds or nuisance inputs change; variance always from true memberships. **Oracle variants use truth and are diagnostics only.**
| Variant | sd(tau-hat), gamma=1 (200 reps) | ratio vs random [boot 95%] | sd, gamma=0 (100 reps) | ratio [boot 95%] |
|---|---|---|---|---|
| random | .518 | 1.00 | .308 | 1.00 |
| grouped | .638 | 1.23 [1.20, 1.27] | .339 | 1.10 [1.02, 1.20] |
| size-matched random (grouped fold sizes) | .522 | 1.01 [.98, 1.04] | .327 | 1.06 [1.01, 1.13] |
| grouped from shuffled memberships (pseudo-blocks) | .509 | .98 [.96, 1.01] | .306 | .99 [.95, 1.05] |
| random + oracle regime effect (D) | .290 | .56 [.50, .63] | .270 | .88 |
| grouped + oracle regime effect (D) | .527 | 1.02 [.93, 1.12] | .408 | 1.33 [1.17, 1.52] |
| random + oracle D and U_win | .287 | .55 | .261 | .85 |
| grouped + oracle D and U_win | .408 | .79 | .318 | 1.03 |

Reading (limits stated):
1. **Not fold size or block structure per se:** size-matched random and pseudo-block grouped folds show no inflation (ratios ~1.0). The excess spread needs folds aligned with the true regimes. Excludes H3 and the "few large blocks" version of H2.
2. **Regime-level treatment shifter is the dominant spread source:** supplying it to random folds cuts sd by 44%. Under grouped folds supplying it does nothing (ratio 1.02; at gamma=0 where it is pure noise it *raises* sd, 1.33): a held-out regime's covariate value is out of the training support, so a forest cannot use it. Grouped folds thus make a regime-level effect unlearnable by construction. This supports H1 (consistent, not isolated: the specific "own-regime events in training absorb part of the shifter" channel under random folds without an oracle was not separately tested).
3. The inflation is smaller at gamma=0 (1.10, CI barely above 1) and shrinks with K, as H1 predicts (each regime's share of training data ~1/K).
4. **Implication:** larger grouped spread is a statistically honest consequence of not leaking regime information into nuisance fits, but the robust SE does not grow enough (SE ratio ~1.2-1.5 vs sd ratio plus overall undercoverage), so grouped cells cover *worse* at K=4. This is not evidence that grouped cross-fitting is inferior or superior; it is one DGP, one learner (RF, 40 trees), one fold count. Needs: different learner/fold count, The shared-calendar-factor explanation for undercoverage was tested and **not supported** (`results/tables/mirun_factor_off_K{4,16}.json`, 200 reps, sd_factor=0, same seeds): robust coverage K4 R .83 / G .785, K16 R .855 / G .885, i.e. no improvement over factor-on (.85/.81, .895/.905); sd(tau-hat) unchanged (K4 .50/.63). Undercoverage therefore persists without the factor, and its cause (few effective clusters under CR0+normal? finite-sample DML bias?) is untested.
