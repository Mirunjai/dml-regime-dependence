# Project A — Priority 1 Gate 2 validation

**Date:** 12 November 2026  
**Classification:** EXPLORATORY_DIAGNOSTIC_NOT_GATE_APPROVAL  
**Generator:** research/week2_completion/dgp.py::build_world  
**Pinned DGP Git blob:** 47e24f88c4724be4708271931f03492eb968f741  
**Design:** n=400, T=260, H=5, K in {4,16}

## Technical decision

Use realized event-exposed share as the primary density axis and H4 matching quantity:
exposed_share = (1/n) sum_i 1{|M_i| > 0}, where M_i is the set of regimes touched by event i.

Configured calendar active fraction is a DGP input, not realized event-level density. Report unconditional and conditional shared-pair density, multi-regime share, membership-count distribution, and inverse-HHI effective regime exposure count separately.

Candidate calendar fractions for H4 exposure targets:

| Target | K=4 | K=16 |
|---:|---:|---:|
| 0.32 | 0.250 | 0.075 |
| 0.56 | 0.500 | 0.300 |
| 0.82 | 0.750 | 0.575 |

A maximum paired exposure gap of 0.02 is used as a practical engineering tolerance only, not a team-ratified Gate 2 threshold.

## Source-faithful execution

The diagnostic imports the exact integrated DGP build_world() and checks its Git blob SHA before running. Fixed, disjoint seed ranges:

- Structural grid: 100 worlds per each of six cells, seeds 10000–10099.
- H4 matched exposure: 200 worlds per each K/density cell, seeds 11000–11199, paired by seed across K.
- Independence threshold calibration: 100 null worlds per K, seeds 12000–12099.
- Independence validation: 100 fresh null and 100 paired-seed positive-control worlds per K/arm, seeds 13000–13099.
- Known-truth contrast: 100 paired worlds, seeds 14000–14099.

The complete JSON result is stored at results/tables/mirun_gate2_validation_2026-11-12.json.gz.

## Structural grid

Means over 100 worlds per cell:

| K | Calendar active fraction | Exposed-event share | Shared-pair density | Multi-regime event share | Effective regime exposure count |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.25 | 0.31593 | 0.02499 | 0.00000 | 3.904 |
| 4 | 0.50 | 0.57008 | 0.08130 | 0.00000 | 3.947 |
| 4 | 0.75 | 0.82313 | 0.16941 | 0.00000 | 3.964 |
| 16 | 0.25 | 0.50555 | 0.01605 | 0.00015 | 14.848 |
| 16 | 0.50 | 0.75845 | 0.03628 | 0.00328 | 15.239 |
| 16 | 0.75 | 0.95633 | 0.06298 | 0.04990 | 15.401 |

Equal calendar fractions do not yield equal exposure across K. Multi-regime windows remain rare, especially for K=4. This is a few-versus-many regime-cluster exposure design, not widespread multi-regime overlap within each event window.

## H4 exposure matching

Paired differences are K=4 minus K=16; MCSE is across the 200 paired worlds.

| Target | K=4 exposure | K=16 exposure | Paired exposure gap (MCSE) | K=4 pair density | K=16 pair density | Pair-density gap (MCSE) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.32 | 0.31791 | 0.32691 | -0.00900 (0.00244) | 0.02530 | 0.00674 | 0.01856 (0.00030) |
| 0.56 | 0.56839 | 0.55449 | 0.01390 (0.00250) | 0.08081 | 0.01926 | 0.06155 (0.00052) |
| 0.82 | 0.82355 | 0.82573 | -0.00218 (0.00194) | 0.16948 | 0.04359 | 0.12589 (0.00054) |

All exposure gaps are below 0.02. At matched exposure, K=4 has substantially higher shared-pair density. This is a structural consequence of concentrating exposed events across fewer regimes, not the matched quantity itself.

## Independence controls

Absolute-correlation 95th-percentile thresholds are calibrated on the separate null seed set. Rates are successes/trials with 95% Wilson intervals.

| K | Metric | Null false positives | Volatility-break detection | Treatment-break detection |
|---:|---|---:|---:|---:|
| 4 | volatility vs abs(shock) | 2/100 = 2% [0.6%, 7.0%] | 100/100 = 100% [96.3%, 100%] | 2/100 = 2% [0.6%, 7.0%] |
| 4 | treatment vs signed shock | 4/100 = 4% [1.6%, 9.8%] | 4/100 = 4% [1.6%, 9.8%] | 93/100 = 93% [86.3%, 96.6%] |
| 16 | volatility vs abs(shock) | 8/100 = 8% [4.1%, 15.0%] | 100/100 = 100% [96.3%, 100%] | 8/100 = 8% [4.1%, 15.0%] |
| 16 | treatment vs signed shock | 6/100 = 6% [2.8%, 12.5%] | 6/100 = 6% [2.8%, 12.5%] | 100/100 = 100% [96.3%, 100%] |

The unbroken validation false-positive rates are 2–8%; their Wilson intervals include 5%. Injected violations are detected in 93–100% of worlds. These checks only test the two implemented violations and are not proof of general independence.

## Known-truth structural check

For 100 paired worlds with no regime shocks, no common factor and gamma=0, the same world at tau=1 and tau=0 satisfies (Y_tau=1 - Y_tau=0) - D with maximum absolute error 8.88e-16 (tolerance 1e-12). This verifies the structural treatment-effect identity, not DML size or coverage.

## Outcome and blockers

Priority 1 technical diagnostic scope is complete: source-pinned density grid, H4 exposure validation, separate-seed null/positive independence controls, known-truth structural contrast, machine-readable results and targeted tests.

Gate 2 remains NOT APPROVED / NOT PASSED. Still outstanding: outcome-level dependence threshold checks, DML zero-effect empirical-size and nonzero-effect coverage/power calibration, canonical-versus-fixed-alpha GARCH reconciliation, paired four-cell runner verification (S13), variance estimator selection/validation, and recovery/reconciliation of the authoritative Gate 2 checklist. Do not label these outputs production results.
