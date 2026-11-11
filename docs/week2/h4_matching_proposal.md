# Week 2: H4 Matched-Density Proposal

## 1. Objective

H4 investigates whether the number of independent common-shock regimes affects DML inference when dependence density is approximately controlled.

The purpose of matching is to distinguish the effect of regime count from the effect of realized dependence density.

## 2. Proposed Experimental Design

The feasibility experiment uses:

- Number of windows: 1,000
- Random seed: 42
- Target realized pair density: 0.0495
- Regime counts: 5, 10, 20, 50
- Active-density search grid: 0.000 to 1.000 in increments of 0.001

For each regime count, the algorithm selects the active density that minimizes the absolute difference between realized pair density and the target.

## 3. Matching Feasibility Results

| Regimes | Selected active density | Realized pair density | Absolute error |
|---|---|---|---|
| 5 | 0.500 | 0.04955 | 0.00005 |
| 10 | 0.708 | 0.04947 | 0.00003 |
| 20 | 1.000 | 0.04905 | 0.00045 |
| 50 | 1.000 | 0.01902 | 0.03048 |

## 4. Interpretation

The 5-regime and 10-regime configurations achieve close matches to the target pair density.

The 20-regime configuration approaches the target, although its matching error is larger.

The 50-regime configuration cannot achieve the target within the tested search grid. Its highest reported realized pair density is 0.01902, substantially below the target of 0.0495.

Therefore, all four configurations should not be treated as equal-density experimental conditions.

## 5. Recommended H4 Experiment

Subject to team approval:

1. Establish an acceptable matching-error tolerance before running the main experiment.
2. Consider using the approximately matched 5-, 10-, and 20-regime configurations.
3. Exclude the unmatched 50-regime configuration from equal-density comparisons, or redesign the target and matching procedure.
4. Run repeated Monte Carlo simulations using the approved matched configurations.
5. Compare empirical DML confidence-interval coverage, interval width, and estimator behavior across the regime counts.
6. Evaluate whether dependence-robust variance estimation alone is sufficient or whether regime-aware cross-fitting improves inference.

## 6. Current Status

The matching-feasibility implementation and numerical results are complete.

The full H4 DML inference experiment and hypothesis evaluation are not established by this feasibility analysis.

## 7. Reproducibility

Implementation: `src/dgp/matched_density.py`

Recorded terminal output: `docs/week2/h4_matching_output.txt`

Execution command:

`python -m src.dgp.matched_density`

## 8. Conclusion

The feasibility analysis identifies an important experimental-design constraint: a common target pair density is not achievable for all four proposed regime counts under the current generator.

This limitation must be addressed before making valid equal-density comparisons of DML inference across regime counts.