# Methods and Results — Mirun's draft (Session 3)

**Status: DRAFT (Methods only).** No primary experiment has been executed; Gate 2 and Gate 3 are not approved. The design in `reports/mirun_gate3_experiment_proposal.md` is unapproved. Settings that depend on the approved design are marked as unresolved.

## Methods

### M1. Research question
Under regime-clustered financial events with dense common-shock cross-sectional dependence, does dependence-robust variance estimation alone restore 95% confidence-interval calibration of a DML estimate, or does regime-aware grouped cross-fitting add inferential benefit? Primary outcome: empirical coverage of 95% intervals; key diagnostic: empirical size under a separate zero-effect condition. The central comparison is random cross-fitting + robust variance vs grouped cross-fitting + robust variance; width and power alone do not establish benefit; similar performance of the two robust cells is a valid result. Classical event studies and Synthetic Control are secondary contextual benchmarks; the S&P 500 sample is a qualitative real-data check, not Monte Carlo coverage evidence.

### M2. Data-generating process (candidate: `research/week2_completion/dgp.py`, unmodified)
n=400 events, T=260 calendar days, event window H=5, p=5 covariates X ~ N(0, I). Event start date t0 ~ Uniform{0..T-H}. Idiosyncratic returns follow a per-event GARCH(1,1) (fixed alpha=.10, persistence .90, unit unconditional variance; finite fourth moment since 3a²+2ab+b²=.83<1). A shared calendar factor F_t ~ N(0, .5²) enters with loading beta_i = 1+.3·X_4. Regime shocks: a fraction `density` of calendar days is covered by K regime blocks, each with a shock U_k ~ N(0, .4²) added on its days. Window sums U_win and F_win accumulate over an event's H days. An event's regime membership is the set of all regimes touched by its window (multi-membership allowed).
Treatment: D ~ Bernoulli(logistic(-.5 + .5X_1 + .3X_2 + gamma·mean_{k in membership} v_k)), v_k ~ N(0,1) a regime-level treatment shifter not observed in X.
Outcome (potential-outcome form with constant effect): Y = g(X) + beta_i·F_win + U_win + sum of window idiosyncratic returns + tau·D, with g(X) = .5X_1 + .3X_2² + .2X_1X_3. Truth tau enters only evaluation. Separate named RNG streams generate covariates, dates, volatility, factor, regime layout, shocks, regime treatment effects and treatment. Because v_k and U_k are independent, regimes create dependence but no confounding by construction.
Caveats: fixed-alpha rather than canonical GARCH parameterisation; the DGP is exploratory until Gate 2/3 approve it; the legacy first-membership DGP (`research/week2_mirun`) is a different variant and is never pooled.

### M3. DML estimator (`research/week2_completion/dml.py`, unmodified)
Partialling-out: nuisance functions E[Y|X] and E[D|X] fit by random forests (40 trees, as implemented), cross-fitted over 5 folds; residuals Ỹ, D̃; tau_hat = sum(D̃Ỹ)/sum(D̃²); score psi_i = D̃_i(Ỹ_i − tau_hat·D̃_i). Truth is never used in nuisance fitting (the oracle diagnostics in R4 are the explicitly labelled exception and are not estimators).
Cross-fitting: **random** (uniform assignment) or **grouped** (connected components of the regime-overlap graph assigned whole to folds; events with no regime are singletons).
Variance: **naive** iid sandwich; **robust** = overlap sandwich, meat = psi'Aψ with A_ij = 1 if events i and j share any regime (equals the cluster-sum CR0 estimator under single membership; A may be indefinite under multi-membership, in which case the code records a failed cell), normal critical value, no small-sample correction. This estimator models regime dependence only; the shared calendar factor is not modelled (assumption/limitation; a factor-off check showed it is not the main source of undercoverage). Intervals: tau_hat ± 1.96·SE.

### M4. Experimental cells and metrics
Four cells: random|grouped × naive|robust on the same simulated world per replication. Coverage = share of attempted-and-valid intervals containing the truth, with Monte Carlo SE and Wilson interval; empirical size = rejection of H0: tau=0 under tau=0; paired contrasts by replication id (`paired_binary_difference`, never two independent binomials). Failed cells are retained, with all-attempted bounds reported. Implemented through `src/evaluation/metrics.py` and the separate engine `src/infra/dml_engine.py` (approval guard; unit-tested; smoke only so far).

### M5. Replication protocol
Seeds: root_seed + replication_id; named streams inside the DGP; atomic per-replication JSON; resumable; manifest with config hash and git state. Proposed budget: 1000 replications per condition (MCSE <= 0.7 pp) — `AWAITING_TEAM_APPROVAL`. Historical pilots used 20-200 replications (MCSE .012-.08).

### M6. Negative controls and sensitivity conditions (Session 5 design; proposals)
Independent control (`sd_factor=0, sd_shock=0, gamma=0`), factor-only (`sd_shock=0, gamma=0`), factor-off unmatched and variance-matched (`sd_factor=0`, `sigma2_bar` calibrated to keep outcome-noise variance fixed), n = 400 vs 1000, a second learner. The original benchmark conditions are preserved unchanged.

### M7. Separately labelled estimator proposals
t(G_reg-1) critical values on the existing overlap-sandwich SE, and a regime-part G/(G-1) correction with t(G_reg-1). They are evaluated side by side with, never instead of, the primary estimator; adoption requires team approval before production.

### M8. Unresolved methodological decisions
(1) CR0-normal vs the proposals; (2) whether the DGP must realize dense common-shock dependence (the calendar factor currently contributes ~none at 3.5% window overlap); (3) event-membership overlap level (0.35% multi-regime events at K=16); (4) calendar (alpha=.10, burn 500) vs canonical (alpha=.1 rho, burn 1000) GARCH; (5) density quantity; (6) learner and fold count; (7) the real-data label-to-regime mapping.

Exploratory results are not part of this Methods draft; see `reports/mirun_undercoverage_diagnosis.md` and `reports/mirun_gate2_evidence.md`.
