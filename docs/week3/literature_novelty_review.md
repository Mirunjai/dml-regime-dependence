# Literature Integration and Novelty Assessment

## Research Context

This project investigates the calibration of Double Machine Learning (DML) confidence intervals in financial event studies with regime-level common-shock dependence.

The primary objective is to evaluate whether dependence-robust variance estimation alone provides adequate confidence-interval coverage, or whether regime-aware grouped cross-fitting provides additional benefits.

## Related Literature

### Double Machine Learning

Chernozhukov et al. (2018) establish Double/Debiased Machine Learning using Neyman-orthogonal scores and cross-fitting to reduce sensitivity to nuisance-model estimation errors.

Our project uses this methodological foundation but evaluates its finite-sample inferential behavior under a specific simulated dependence structure.

### Dependence-Robust Inference

Cameron, Gelbach, and Miller (2011) develop robust inference methods for multiway-clustered observations.

Their work demonstrates the importance of accounting for dependence in uncertainty estimation. Our project investigates whether robust variance estimation is sufficient when DML nuisance-model training and evaluation observations share regime-level shocks.

### Financial Event Studies

MacKinlay (1997) reviews event-study methodology for evaluating security-price responses to economic events.

Our project implements a classical market-model event study as a contextual benchmark, using abnormal returns and cumulative abnormal returns around announcement dates.

### Synthetic Control

Abadie, Diamond, and Hainmueller (2010) establish Synthetic Control methodology for constructing weighted comparison units.

Our project includes Synthetic Control as a planned secondary benchmark. Its empirical implementation remains conditional on historical donor eligibility, price coverage, and screening validation.

## Proposed Contribution

The intended contribution is a controlled Monte Carlo evaluation of the interaction between:

1. Random versus regime-grouped cross-fitting.
2. Naive versus dependence-robust variance estimation.
3. Common-shock dependence density.
4. The number of independent regimes.

The principal evaluation metric is empirical coverage of nominal 95% confidence intervals, with additional diagnostics used to interpret calibration behavior.

## Novelty Assessment

The project does not introduce a new DML estimator, variance estimator, or theoretical result.

Its potential contribution is the joint finite-sample evaluation of cross-fitting design and variance estimation under a regime-level dependence mechanism relevant to financial events.

This is a proposed empirical contribution, not a verified claim of being the first study to investigate these questions.

A complete novelty assessment requires further comparison with research on dependent-data DML, block cross-fitting, clustered inference, and financial applications.

## Current Evidence and Limitations

Week 2 simulations have validated aspects of the regime-level dependence generator and investigated the feasibility of matching pair density across regime counts.

Week 3 has produced classical event-study estimates for seven firms and VIX-based market-regime classifications.

These completed benchmarks do not establish DML confidence-interval coverage.

Synthetic Control results must not be reported until the donor pool is validated and the benchmark is executed.

## References

1. Chernozhukov, V., et al. (2018). Double/debiased machine learning for treatment and structural parameters. *The Econometrics Journal*, 21(1), C1–C68. https://doi.org/10.1111/ectj.12097

2. Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2011). Robust inference with multiway clustering. *Journal of Business & Economic Statistics*, 29(2), 238–249. https://doi.org/10.1198/jbes.2010.07136

3. MacKinlay, A. C. (1997). Event studies in economics and finance. *Journal of Economic Literature*, 35(1), 13–39.

4. Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control methods for comparative case studies: Estimating the effect of California's tobacco control program. *Journal of the American Statistical Association*, 105(490), 493–505. https://doi.org/10.1198/jasa.2009.ap08746