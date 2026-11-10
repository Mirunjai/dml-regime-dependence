# Robust-variance undercoverage diagnosis and zero-effect size study (Session 4)

Status: **Executed, exploratory.** Calendar DGP and `run_dml`/`estimate` unmodified. All alternatives are *proposals* (`research/mirun_proposals/`), never substituted for the primary estimator; no Gate 2/3 approval is implied; the size study is a pilot with seeds 50000+, not the production campaign. Scripts: `scripts/mirun_undercoverage_study.py`; tests: `tests/test_mirun_proposals.py` (5). Raw: `results/raw/mirun_session4/` (gitignored). Summaries: `results/tables/mirun_undercoverage_*.json`, `mirun_zero_effect_size_*.json`.

## 1. Where does the undercoverage come from? (tau=1, gamma=1, d=.5, seeds 30000+, 200 reps, MCSE ~.02-.03)
Quantity used: SE/sd = mean reported SE divided by the empirical sd of tau-hat over replications (1.0 = calibrated).
| K, n, route | bias/sd | existing (CR0, normal) coverage [SE/sd] | t(G-1) on same SE | CR1-regime + t(G-1) |
|---|---|---|---|---|
| 4, 400, RF random | -.11 | .850 [.74] | .975 | .980 |
| 4, 400, RF grouped | -.10 | .810 [.69] | .955 | .965 |
| 4, 400, GBR random (2nd learner) | -.13 | .825 [.70] | .950 | .980 |
| 4, 400, **oracle nuisance** (truth, diagnostic only) | -.09 | .880 [.79] | .995 | .995 |
| 4, 1000, RF random | -.13 | .835 [.74] | .955 | .985 |
| 4, 2500, RF random | -.07 | .855 [.72] | .985 | .990 |
| 16, 400, RF random | -.02 | .895 [.84] | .925 | .930 |
| 16, 400, RF grouped | -.01 | .905 [.82] | .915 | .940 |
| 16, 400, GBR random | -.03 | .880 [.81] | .900 | .910 |
| 16, 1000, RF random | -.05 | .925 [.88] | .950 | .950 |
| 16, 2500, RF random | -.01 | .920 [.90] | .955 | .955 |
Naive-normal coverage is far lower at K=4 (.61-.76 at n=400; .625 at n=1000 and .48 at n=2500, i.e. naive worsens with n). CR1 with G_all clusters (singletons included) and HC3-style leverage scaling change nothing (factor ~1.00-1.01) because most events are singletons.

**Conclusions (with limits):**
1. **Not nuisance/finite-sample DML bias:** bias is <= .13 sd; oracle (known-nuisance) residuals still undercover (.88, SE/sd .79); a second learner behaves alike; at K=4 SE/sd does not improve from n=400 to 2500.
2. **A few-effective-cluster variance problem:** the CR0 SE is too small by 21-31% at G=4 regimes and 10-19% at G=16, and the deficit at K=16 shrinks with n (SE/sd .84 -> .90). Together with the earlier factor-off result (calendar factor is not the cause) this points to cluster-level variance estimation with few, unequal clusters. Not proven: effective cluster count (cluster-size heterogeneity) was not computed.
3. **t(G-1) helps but is not a fix:** at K=4 it overcovers (.95-.995; conservative, large power cost likely); at K=16 it reaches ~.95 only from n>=1000 (n=400: .90-.925). CR1-regime+t overcorrects a little more. These are heuristic pivots, not validated.
4. The primary estimator's problem is therefore best described as "CR0-normal under few regime clusters", not "regime-robust variance cannot work".

## 2. Zero-effect empirical size (tau=0, n=400, d=.5, seeds 50000+; size = rejection rate at nominal .05)
| Condition (reps) | scheme | naive | **existing robust** | t(G-1) proposal | CR1-reg+t proposal |
|---|---|---|---|---|---|
| K=4, gamma=1 (1000) | random | .227 ± .013 | **.143 ± .011** | .015 ± .004 | .010 ± .003 |
| | grouped | .290 ± .014 | **.151 ± .011** | .024 ± .005 | .014 ± .004 |
| K=16, gamma=1 (1000) | random | .122 ± .010 | **.087 ± .009** | .070 ± .008 | .063 ± .008 |
| | grouped | .145 ± .011 | **.083 ± .009** | .062 ± .008 | .054 ± .007 |
| K=4, gamma=0 control (500) | random | .072 ± .012 | **.084 ± .012** | .008 ± .004 | .008 ± .004 |
| | grouped | .090 ± .013 | **.114 ± .014** | .010 ± .004 | .008 ± .004 |
Paired grouped − random rejection difference (existing robust): K4 g1 +.008 ± .008; K16 g1 −.004 ± .006; K4 g0 **+.030 ± .010** (~3 SE; grouped over-rejects). With t(G-1): +.009 ± .004, −.008 ± .005, +.002 ± .004.
Precision: MCSE .003-.014 near the relevant sizes; 1000 reps detect a 3-pp size inflation at ~4 SE at nominal .05; the 500-rep control detects ~2.5 SE.
**Reading:** under the existing estimator, robust variance alone does **not** restore size at K=4 (.14-.15 vs .05) and only partially at K=16 (.08-.09); grouped cross-fitting gives no detectable size benefit at gamma=1 and a possible size penalty at gamma=0; the t(G-1) proposals are conservative at K=4 (size ~.01-.02), so power would suffer (not measured here). Note naive size is also elevated at gamma=0 K=4 (.07-.09; within ~2-3 MCSE of .05 for random, borderline for grouped). One DGP, one learner, one n.

## 3. Implications for the Gate 3 design (proposals, not decisions)
- If the estimator stays CR0-normal, the headline for K=4 will be "robust variance is not enough and neither is grouping" mostly because of few clusters; the team should decide whether K=4 is an intended regime count or a few-cluster artifact.
- A separately labelled estimator proposal (t(G-1) or CR1-regime+t) should be ratified or rejected *before* seeing production results; power under each should be measured (not done).
- Add n (e.g. 400 vs 1000) and a power check to the robustness subset.

## 4. Power and effective cluster counts (`scripts/mirun_power_and_geff.py`, `results/tables/mirun_power_and_effective_clusters.json`)
Power = rejection of H0: tau=0 at tau=1 (RF random folds, 200 reps, from the same records; **not size-adjusted**, so variants with different sizes are not on equal footing):
| K, n | naive | existing CR0-normal | t(G-1) | CR1-regime + t(G-1) |
|---|---|---|---|---|
| 4, 400 | .76 | .69 | .41 | .34 |
| 4, 1000 | .91 | .79 | .54 | .47 |
| 4, 2500 | .96 | .83 | .65 | .57 |
| 16, 400 | .82 | .76 | .73 | .72 |
| 16, 1000 | .97 | .92 | .89 | .89 |
| 16, 2500 | .99 | .96 | .95 | .95 |
- Validity has a power price at K=4 (t-variants .34-.65 vs .69-.83) because few clusters give a very wide t(3) interval; at K=16 the price is small and vanishes with n.
- **Effective cluster count (G_eff = (sum s)^2 / sum s^2 over regime sizes):** K=4: 3.95-3.99 of 4; K=16: 15.2-15.9 of 16. Unequal regime sizes therefore do **not** materially reduce the effective number of clusters, so the earlier "cluster-size heterogeneity" hypothesis is **not supported**. The remaining SE deficit at K=16 (SE/sd .84 at n=400) is unexplained: a sqrt-of-chi-square few-cluster bias alone would predict ~.98 at 15 df, and the lost df from centering at tau-hat only ~.97. Untested candidates: nuisance-estimation error inducing cross-event score dependence beyond regimes; heavy-tailed scores (GARCH) making the meat noisy in small samples.

---
# Session 5: hypothesis ledger (10 competing explanations)
Evidence base: sections 1-4 above plus Session 3 mechanism/factor-off runs and Session 5 controls (`scripts/mirun_session5_checks.py` run, 200 reps, seeds 70000+, K=4, d=.5, n=400, tau=1; `results/tables/mirun_session5_controls.json`). Calendar DGP only; one learner family plus one GBR check. "Concluded" = Mirun's reading of exploratory evidence, not independently verified.

| # | Hypothesis | Diagnostic test | Expected if true | Actual | Conclusion / remaining uncertainty |
|---|---|---|---|---|---|
| 1 | Variance estimator (CR0-normal overlap sandwich) is miscalibrated | iid control (no dependence); t(G-1)/CR1 proposals | Robust undercovers even without dependence; small-sample critical values help | Independent control: robust .870/.875 vs naive .930/.900; t(G-1) lifts coverage to ~.95-.98 (K=4) | **Supported**: CR0-normal with ~4 regime clusters is anti-conservative regardless of dependence. Not a proof that the overlap form is invalid; formal asymptotics not derived |
| 2 | Cross-fitting leakage across dependent units | random vs grouped; size-matched random; pseudo-block grouped; oracle regime effect | Grouped fixes coverage; leakage removal changes sd | Both undercover; grouped sd larger (1.23x) only when folds align with true regimes; paired robust difference -0.040 +- 0.019 (K=4) | **Not the main cause** of undercoverage; grouped changes spread, not calibration. Mechanism of the spread consistent with unlearnable held-out regime effect, not isolated |
| 3 | Too few effective independent clusters | G_eff; larger n at fixed K; K=4 vs 16 | Deficit tied to G, not n | G_eff 3.95/4 and 15.2/16; K=4 SE/sd flat in n (.72-.74); K=16 .84 -> .90 with n | **Supported at K=4**; at K=16 a 10-16% SE deficit remains unexplained |
| 4 | Common calendar-factor shocks | factor-only; factor-off; variance-matched factor-off | Naive miscalibrates under factor-only; removing factor restores coverage | Factor-only naive .945/.940; factor-off .79/.78 and variance-matched .805/.785 vs benchmark .815/.795 | **Rejected as a cause in this DGP** (window overlap only 3.5%). Consequence: the DGP does not realize "dense common-shock" dependence via the factor |
| 5 | Regime/event mismatch (calendar vs event-index regimes) | fold leakage; membership counts | Leakage of shared dates across grouped folds matters | 7-70% calendar-shared pairs cross grouped folds but factor is irrelevant; multi-regime events 0/80,000 (K=4), 280/80,000 (K=16) | **Not supported** as an undercoverage cause here; matters for design (membership barely varies) |
| 6 | Nuisance estimation error / finite-sample DML | oracle nuisance; GBR; larger n | Oracle restores coverage | Oracle .880 (SE/sd .79); GBR .825; bias <= .13 sd; iid control naive SE/sd .90-.92 (≈8% shortfall) | **Not the main cause**; a small (~8%) nuisance-related SE shortfall is visible even with independent data |
| 7 | Small-sample effects | n = 400, 1000, 2500 | Coverage converges with n | K=16 improves (.895 -> .92, t-variant ~.95 at n>=1000); K=4 does not | **Partly**: n helps only when G is large |
| 8 | Invalid / non-PSD covariance | failure scan; PSD scan | Negative meat, failed cells | A non-PSD in 38-100% of high-K worlds but 0/2,000 failed cells; meat positive (SE ratio 1.15-1.5) | **Not a cause of undercoverage** here; remains a theoretical hazard (untested for other DGPs) |
| 9 | Monte Carlo / implementation error | iid control; engine vs direct run; replay audit | Naive miscalibrated even without dependence; discrepancies | Independent control naive nominal (.93/.90 +- .02); engine bit-identical; replay 0/520 discrepancies | **Not supported**; no evidence of a coding error in the cell pipeline (cannot prove absence) |
| 10 | DGP misspecification relative to the research question | factor-only/factor-off; overlap counts; variance matching | DGP fails to instantiate intended dependence | Dependence comes from regime shock + gamma treatment shifter, not the factor; membership overlap ~0 | **Partly supported**: needs a team decision on whether this DGP embodies "dense common-shock dependence" |

**Net reading.** The headline "robust variance does not restore calibration" is, in this DGP, largely a few-cluster property of CR0-normal (visible even with no dependence), not a verdict on dependence-robust inference or on grouping. Any production conclusion about the central contrast requires settling the estimator choice first.
