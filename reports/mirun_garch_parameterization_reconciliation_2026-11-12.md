# GARCH parameterization reconciliation — Project A

**Classification:** technical reconciliation; not Gate approval.  
**Date:** 12 November 2026.

## Source implementations

The canonical implementation is `src/dgp/volatility.py`:
- `alpha = arch_share * rho`, with default `arch_share=0.10`.
- `beta = rho - alpha`.
- `omega = v * (1-rho)`.
- Defaults to a burn-in of 1,000 and generates Gaussian innovations once per time step across firms.

The historical Week-2 implementation in `research/week2_completion/dgp.py`:
- Fixes `alpha=0.10`.
- `beta = rho - 0.10`.
- Uses the same intended unconditional variance mapping for omega.
- Defaults to a burn-in of 500 and draws a row-major innovations matrix before recursion.

They are not the same parameterization or path generator. Matching persistence and unconditional variance alone does not make them equivalent.

## Parameter comparison

| Persistence rho | Implementation | alpha | beta | omega (v=1) | Finite variance | Finite Gaussian fourth moment |
|---:|---|---:|---:|---:|---|---|
| 0.90 | Historical fixed-alpha | 0.100 | 0.800 | 0.100 | Yes | Yes |
| 0.90 | Canonical arch-share | 0.090 | 0.810 | 0.100 | Yes | Yes |
| 0.99 | Historical fixed-alpha | 0.100 | 0.890 | 0.010 | Yes | **No** |
| 0.99 | Canonical arch-share | 0.099 | 0.891 | 0.010 | Yes | Yes, narrowly |

For Gaussian innovations, finite fourth moment requires `rho^2 + 2*alpha^2 < 1`. At rho=.99, the fixed-alpha model gives 1.0001 and fails this condition; the canonical model gives 0.999702 and passes with a small margin. Both still satisfy finite-variance stationarity (`rho<1`).

## Decision for current study

Do not call the two implementations “GARCH-equivalent” and do not mix their generated panels in one Monte Carlo campaign. The historical Week-2 DGP is the source-pinned generator for the current calibration script and historical pilot reproduction. The canonical implementation is a separate model variant and must be treated as a sensitivity/reproduction comparison. In particular, the rho=.99 fixed-alpha setting is not a finite-fourth-moment design and should not be used where variance-of-squared-return or conventional kurtosis diagnostics are assumed finite.

The added simulation script runs both implementations at rho=.90 and .99 and records sample conditional-variance means, squared-return means and lag-one squared-return autocorrelation where defined. These are finite-sample diagnostics, not a proof of equivalence.

## Status

The mathematical mismatch is reconciled and documented. This does not decide which parameterization the team should use in the final project; it documents the actual Week-2 source and warns against silently substituting the canonical implementation.
