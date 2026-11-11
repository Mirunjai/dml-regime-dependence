# Literature Integration and Novelty Assessment

## Research context

This project evaluates Double Machine Learning (DML) confidence-interval calibration under a simulated regime-level common-shock dependence structure. Its primary question is whether dependence-robust variance estimation is sufficient, or whether regime-aware grouped cross-fitting adds finite-sample coverage benefits. Classical event study and Synthetic Control are secondary contextual benchmarks; they do not establish DML coverage.

## Related work and attribution

### DML and dependent observations

Chernozhukov et al. (2018) establish orthogonal-score DML with cross-fitting under stated sampling and regularity conditions. The project should not generalize those conditions to its dependent setting without checking them.

There is direct prior work on clustered DML: Chiang, Kato, Ma, and Sasaki, “Multiway Cluster Robust Double/Debiased Machine Learning,” arXiv:1909.03489 (2019; working-paper version), https://arxiv.org/abs/1909.03489. The paper develops multiway cross-fitting and multiway DML for multiway clustered sampling, so the project cannot claim that it is the first to combine DML with dependence-aware cross-fitting or clustered inference.

A newer adjacent working paper is Kallus and Mao, “Cross-Fitting-Free Debiased Machine Learning with Multiway Dependence,” arXiv:2602.11333 (2026), https://arxiv.org/abs/2602.11333. Its abstract develops DML inference for general multiway clustered dependence without sample splitting. This is relevant to the broader question of DML under dependence, but it is not the same design as this project's finite-sample comparison of random versus regime-grouped cross-fitting and naive versus robust variance under a specified financial-event-style DGP. Verify version/date and full assumptions before final citation.

### Cluster robust inference

Cameron, Gelbach, and Miller (2011) develop multiway-cluster-robust inference. This motivates robust variance as one experimental factor; it does not by itself establish validity for every regime-level shock design or solve dependence in nuisance training/evaluation splits.

### Financial event studies

MacKinlay (1997) reviews event-study design. The branch's market-model event study is a contextual benchmark and is sensitive to event timing, estimation window, confounding events, and dependence among firms sharing announcement clusters.

### Synthetic Control

Abadie, Diamond, and Hainmueller (2010) introduce the canonical comparative-case SCM. Abadie (2021) reviews feasibility, data requirements, and methodological choices. The current project helper has no placebo inference, and empirical execution is blocked by donor evidence/data and explicit team-lead approval.

### Adjacent 2026 work: event studies and regimes

Botosaru and Liu (2026), “Event Studies with Feedback,” *AEA Papers and Proceedings* 116, 70–74, DOI 10.1257/pandp.20261110, https://doi.org/10.1257/pandp.20261110, studies dynamic panel event studies with treatment effects and covariate feedback. It is adjacent event-study literature, not the same question about regime-dependent DML coverage.

Everaert and Iseringhausen (2026), “Financial market interdependence, contagion and jumpy risk exposure,” ESM Working Paper 76, https://www.esm.europa.eu/publications/financial-market-interdependence-contagion-and-jumpy-risk-exposure, models regime-varying common factor exposure across European stock markets. It is relevant background for regime-dependent common shocks, not a DML event-study comparison.

## Proposed contribution and novelty boundary

The defensible potential contribution is a controlled finite-sample Monte Carlo comparison of (1) random versus regime-grouped cross-fitting and (2) naive versus dependence-robust variance, across common-shock densities and independent-regime counts, with empirical 95% CI coverage as the primary metric.

This is a proposed and bounded contribution. Do not claim “first,” a new estimator, a new variance formula, a new theorem, or a general failure of DML in finance. The related clustered-DML literature substantially narrows any novelty claim. A comprehensive novelty search across block cross-fitting, clustered/dependent DML, financial econometrics, and regime-switching designs remains necessary before external claims.

## Current evidence

Week 2 reports describe single-seed dependence-generator diagnostics and matched-density feasibility; they do not establish DML coverage or hypothesis tests. Week 3 records classical market-model results for seven firms and VIX regime labels. CTLT is excluded because historical adjusted prices are unavailable. Synthetic Control has not been run: donor eligibility and prices are unavailable, and a team-lead approval is required for the post-November 8 benchmark.

## References

1. Chernozhukov, V., et al. (2018). Double/debiased machine learning for treatment and structural parameters. *The Econometrics Journal*, 21(1), C1–C68. https://doi.org/10.1111/ectj.12097
2. Chiang, H. D., Kato, K., Ma, Y., & Sasaki, Y. (2019). Multiway Cluster Robust Double/Debiased Machine Learning. https://arxiv.org/abs/1909.03489
3. Kallus, N. & Mao, X. (2026). Cross-Fitting-Free Debiased Machine Learning with Multiway Dependence. https://arxiv.org/abs/2602.11333
4. Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2011). Robust inference with multiway clustering. *Journal of Business & Economic Statistics*, 29(2), 238–249. https://doi.org/10.1198/jbes.2010.07136
5. MacKinlay, A. C. (1997). Event studies in economics and finance. *Journal of Economic Literature*, 35(1), 13–39.
6. Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control methods for comparative case studies. *JASA*, 105(490), 493–505. https://doi.org/10.1198/jasa.2009.ap08746
7. Abadie, A. (2021). Using Synthetic Controls: Feasibility, Data Requirements, and Methodological Aspects. *JEL*, 59(2), 391–425. https://doi.org/10.1257/jel.20191450
8. Botosaru, I. & Liu, L. (2026). Event Studies with Feedback. *AEA Papers and Proceedings*, 116, 70–74. https://doi.org/10.1257/pandp.20261110
9. Everaert, G. & Iseringhausen, M. (2026). Financial market interdependence, contagion and jumpy risk exposure. ESM Working Paper 76. See link above.
