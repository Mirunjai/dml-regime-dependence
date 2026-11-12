# Gate 3 variance-estimator decision protocol

Status: **methodology proposal for team decision; no primary estimator is selected by this memo.**

## Problem established by existing evidence

The current DML implementation uses a full-membership regime-overlap CR0 sandwich with normal critical values. The exploratory diagnosis reports undercoverage even in the independent control (robust coverage approximately .870/.875 for random/grouped folds) and substantial size distortion in some dependent conditions (K=4, gamma=1: approximately .143/.151 at nominal .05). The t(G-1) and CR1-regime+t variants improve coverage in some settings but can be severely conservative at K=4 (size around .01-.02), with a measurable power cost.

Therefore, the present CR0-normal method must not be described as a validated finite-sample correction. Nor should an alternative be chosen solely because it yields an estimated coverage close to .95 in a selected cell.

## Candidate methods for a pre-production comparison

Keep all candidates separately labelled and compare on identical simulation worlds.

1. **CR0-normal (current):** retain as the legacy comparator; do not assume it is valid for few clusters.
2. **CR0 with t(G-1):** existing exploratory candidate; evaluates critical-value correction without changing the meat.
3. **CR1-regime plus t(G-1):** existing exploratory candidate; evaluates a finite-cluster scale correction plus small-sample reference distribution.
4. **CR2/BRL with Satterthwaite degrees of freedom:** add as a research candidate if the scalar second-stage DML score-regression derivation and implementation can be justified. CR2 is not equivalent to multiplying CR0 by G/(G-1); it applies a leverage-aware bias-reduced adjustment. The degrees of freedom are hypothesis-specific and data-dependent.
5. **Restricted wild cluster bootstrap-t:** an additional candidate for few-cluster inference, implemented at the orthogonal-score level with null imposition and re-estimation rules documented. The bootstrap must preserve the regime as the independent resampling unit; for very small G, the weight distribution and attainable p-value resolution must be reported.

## Candidate evaluation design

For every method, run identical data-generating worlds and both cross-fitting schemes. Report:

- 95% coverage at nonzero truth.
- Empirical size at zero truth (nominal 5%).
- Power at nonzero truth, interpreted only together with size.
- Mean interval width.
- Bias and RMSE of the point estimate.
- Monte Carlo standard errors and Wilson intervals.
- Failed or undefined interval rate, with the attempted denominator retained.
- Performance in a genuinely independent negative control and positive-control configurations.

Include K=4 and K=16, and at least the intended primary density levels after Gate 2 matching has been ratified. Use common worlds across the four ablation cells and across estimator candidates where the random stream contract permits.

## Decision rule

Choose the estimator based on the complete calibration profile, not one cell's coverage. A defensible candidate should have approximately nominal size and coverage across the pre-specified control and dependence conditions without a material loss of power. If no method meets the criteria, report that as the research finding and bound the claim; do not tune the method until it passes.

## Literature grounding

- Bell and McCaffrey's bias-reduced linearization (BRL/CR2) motivates leverage-aware finite-sample corrections for clustered regression.
- Pustejovsky and Tipton (2018) develop small-sample cluster-robust tests using bias-reduced linearization and Satterthwaite degrees of freedom, with implementations in clubSandwich.
- Cameron, Gelbach and Miller (2008) study wild cluster bootstrap-t methods and show why standard cluster-robust Wald procedures can over-reject with few clusters.
- The 2022 paper on few unbalanced clusters compares CR2, CR3 and related corrections; it also highlights that conservative jackknife-style adjustments may overstate standard errors.

References:
- Pustejovsky, J. E., & Tipton, E. (2018). Small-Sample Methods for Cluster-Robust Variance Estimation and Hypothesis Testing in Fixed Effects Models. Journal of Business & Economic Statistics, 36(4), 672-683. https://doi.org/10.1080/07350015.2016.1247004
- Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). Bootstrap-Based Improvements for Inference with Clustered Errors. The Review of Economics and Statistics, 90(3), 414-427. https://doi.org/10.1162/rest.90.3.414
- A New Estimator for Standard Errors with Few Unbalanced Clusters. Econometrics (2022), 10(1), 6. https://doi.org/10.3390/econometrics10010006

This memo does not claim that CR2 or wild cluster bootstrap is already implemented or valid for the current DML score. It requires a derivation, tests and a pilot before Gate 3 can lock a method.
