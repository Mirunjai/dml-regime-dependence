# DGP / DML comparison matrix (session 1, source-level)

Status: **recommendation only. No approval recorded.** Based on reading source
at `b558156` plus `results/tables/mirun_dgp_component_scan.json`.

| Dimension | Canonical (`src/dgp/*`) | Mirun old (`week2_mirun`) | Mirun new (`week2_completion`) |
|---|---|---|---|
| GARCH mapping | alpha=a*rho (a=.1), beta=rho-alpha | alpha fixed .10, beta=rho-.10 (needs rho>.10) | same as old |
| Burn-in / init | 1000, h0=v | 200 | 500 |
| Innovation draw order | one draw per time step across firms | one (n, T+burn) matrix, row-major | same as old |
| Fourth moment (rho=.99) | margin +0.0003 (barely finite) | -0.0001 (**infinite**) | same as old |
| Regime unit | event index: events randomly assigned to K regimes | calendar-time contiguous blocks | same as old |
| Regime shock | N(0,1) per regime, one value per event | N(0,sd_shock) per period block, summed over H-window | same as old |
| "Density" means | fraction of events exposed | fraction of **calendar time** in blocks (exposed events differ: see scan) | same as old |
| Membership | single | first overlapping regime | full set (multi-membership) |
| Independent shocks | exactly K | min(K, active periods) | same as old |
| Calendar factor F | none | shared across overlapping windows (not regime-aligned) | same |
| Treatment | n/a | logit(X, gamma*regime effect), independent of U and sigma | same; adds explicit break switches |
| Folds | n/a | grouped by first-membership cluster | grouped by connected components of overlap graph |
| Variance | n/a | naive; CR1 over first-membership clusters | naive; overlap sandwich (no small-sample factor, meat may be <=0 -> failed cell) |
| Failure handling | raises | none (aborts replication) | per-cell, attempt-level raw JSON |
| Truth leakage | n/a | none seen | none seen (`crossfit` uses only Y, D, X) |

## What each answers
- **Canonical**: clean, validated GARCH and an event-level common-shock layer. Has no outcome/treatment/DML layer, so cannot by itself support the four-cell question.
- **Old**: first DML pilots (200 reps) with CR1. First-membership clustering ignores multi-regime events (rare at tested settings).
- **New**: same DGP with full membership, graph-component folds and honest failure accounting. The overlap sandwich is a *regime-only* proposal; calendar-factor dependence across folds is audited (`audit_folds`) but not corrected.

## Issues found (verified by reading or running)
1. Density is not the exposed-event share and is entangled with K (scan: density .1 gives .13 exposed at K=2, .35 at K=16). Any "dependence density" or "matched density" claim must say which definition is used. Canonical `matched_density.py` NOT YET checked against this.
2. Neither Mirun variant uses the canonical GARCH; the pilot results are therefore not evidence about the canonical component.
3. Legacy alpha=.10 breaks the fourth-moment condition at rho=.99, so squared-return ACF diagnostics are undefined there.
4. Overlap sandwich uses pair-overlap adjacency, which is not guaranteed PSD; nonpositive meat is possible. Frequency of this failure in realistic settings is unmeasured.
5. Old CR1 uses G/(G-1) with G counting unexposed singletons; many nearly-iid clusters make that factor trivial. Not equivalent to the new estimator.
6. Pilot (old, gamma=1, K=4): grouped cells covered *worse* than random (.73/.865 vs .82/.905, MCSE ~.02-.03). Hypothesis (unverified): whole-regime held-out folds leave the regime-level treatment effect in D-tilde. Needs investigation, not assertion.

## Recommendation (for team approval, not decided)
Take **`week2_completion` DGP + DML** to the team as the primary candidate because it has multi-membership, per-cell failure retention and fold provenance, **conditional on**: (a) team choosing the density definition; (b) deciding whether the canonical GARCH replaces the fixed-alpha one (cost: replay of old pilots is lost; benefit: ties to validated component); (c) choosing between overlap-sandwich and a CR1 alternative, with failure rate measured first; (d) deciding gamma in advance. None of these is settled here.

## Open questions requiring measurement (next session)
- Overlap-sandwich failure rate over the proposed grid.
- Does canonical GARCH change any four-cell conclusion on identical seeds?
- Why grouped sd(tau-hat) > random sd(tau-hat)?

---
# Session 3 addendum
- **Matched density:** `src/dgp/matched_density.py` is defined only for the canonical single-membership event-index generator (`regime_id` array, -1 inactive). It cannot express the calendar DGP's multi-membership windows (its docstring says so). Three density quantities exist for the calendar DGP and none is "the" density: configured calendar fraction `density`, realized exposed-event share, and pair density. A primary design must name one as the manipulated/matched quantity.
- **Robust estimator under this DGP (measured):** 0/2,000 failed cells (`reports/mirun_grouped_folds_diagnostics.md` A), yet all cells undercover (robust .81-.905). The sandwich covers regime clusters only. **Correction (Session 3 factor-off check):** switching the shared calendar factor off (sd_factor=0, same seeds, 200 reps) does not restore coverage (K4 robust .83/.785, K16 .855/.885 vs .85/.81 and .895/.905 with the factor), so the factor is not the main driver; the undercoverage source remains unidentified (candidates: few effective clusters with CR0+normal at small K, finite-sample DML bias; neither tested). Any t(G-1)/CR1 or factor-aware alternative is a *separate proposal*, not a replacement.
- **Grouped folds do not isolate the dependence unit fully:** regime leakage 0, but 7-70% of calendar-shared pairs still cross folds.
- **Still unresolved (not run):** whether canonical GARCH on identical seeds changes any four-cell conclusion. This requires a new DGP variant (DGP change), so it is deferred to the Gate 3 decision rather than done silently. Legacy/calendar GARCH remain fixed-alpha (alpha=.10); finite 4th moment at persistence .9 (3a^2+2ab+b^2=.83<1) but infinite at .99.
- **Preferred candidate for team consideration (unchanged, unapproved):** `week2_completion` DGP + DML, with the open choices listed in the Gate 3 proposal.
