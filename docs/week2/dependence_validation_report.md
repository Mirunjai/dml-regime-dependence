# Week 2: Dependence-Density Validation Report

## 1. Objective

The objective of this experiment is to validate whether the regime-level common-shock data-generating process produces measurable dependence across firms and windows.

## 2. Experimental Setup

The experiment uses the following configuration:

- Number of firms: 100
- Number of windows: 1,000
- Random seed: 42
- Regime counts tested: 5, 10, 20, 50
- Active-shock densities tested: 0.1, 0.3, 0.5, 0.7, 0.9

Firm returns are generated using independent Gaussian noise and shared regime-level shocks.

Two diagnostics are measured:

1. Average pairwise correlation between firms.
2. Realized pair density, defined as the proportion of distinct window pairs assigned to the same active regime.

## 3. Experiment 1: Varying Active Density

The number of regimes is fixed at five.

| Active density | Average correlation | Pair density |
|---|---|---|
| 0.1 | 0.0544 | 0.0019 |
| 0.3 | 0.1199 | 0.0177 |
| 0.5 | 0.1685 | 0.0495 |
| 0.7 | 0.5077 | 0.0974 |
| 0.9 | 0.2523 | 0.1613 |

**Observation:** Realized pair density increases with active density across the tested configurations. Average correlation does not increase monotonically, indicating that the two diagnostics capture different properties of the simulated dependence.

## 4. Experiment 2: Varying Regime Count

Active density is fixed at 0.5.

| Number of regimes | Average correlation | Pair density |
|---|---|---|
| 5 | 0.1685 | 0.0495 |
| 10 | 0.2067 | 0.0245 |
| 20 | 0.3128 | 0.0120 |
| 50 | 0.3574 | 0.0045 |

**Observation:** Increasing the number of regimes reduces realized pair density in these configurations. Average firm-return correlation increases in this particular single-seed experiment; further replications would be required to establish whether this pattern is systematic.

## 5. Limitations

The results are based on one fixed random seed per configuration. They demonstrate properties of the simulated dependence structure but do not establish statistical significance, DML confidence-interval coverage, or causal estimator performance.

## 6. Reproducibility

Implementation: `src/dgp/validate_dependence.py`

Recorded terminal output: `docs/week2/dependence_validation_output.txt`

Execution command:

`python -m src.dgp.validate_dependence`

## 7. Conclusion

The validation demonstrates that the implemented generator can produce different realized dependence structures through changes in active density and regime count. These results provide preliminary diagnostics for the subsequent DML simulation experiments.