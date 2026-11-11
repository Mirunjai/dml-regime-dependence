# Week 3 SCM: Methods, Donor Screening, and Limits

See [donor screening status](synthetic_control_donor_screening.md) for the event-specific evidence table and current blockers.

## Estimand and timing

The planned secondary benchmark compares each treated firm's announcement-period outcome path with a weighted combination of untreated firms. Announcement and effective dates are distinct. Donor eligibility and outcome-fit choices must use pre-announcement information; event day zero remains the value specified in `data/processed/week3_event_day_zero.csv`.

## Implemented estimator

`src/benchmarks/synthetic_control.py` accepts already-aligned treated and donor pre/post outcome arrays. It minimizes pre-period mean squared error subject to nonnegative weights summing to one. It rejects missing/nonfinite values, requires at least two donors, and reports pre-period RMSPE, post-period gaps, and weight concentration/effective donor count.

It is an estimator helper, not a complete SCM research design. It does not establish donor eligibility, select covariate predictors, search/weight predictor sets, handle staggered treatment, run placebo reassignments, derive a randomization distribution, calculate inferential p-values, or form confidence intervals. It does not resolve confounding or spillovers.

## Donor screening

The donor table is an empty screening template, not a shortlist of eligible units. All proposed names remain leads pending point-in-time security identity, historical index membership, dated industry/size/risk/liquidity attributes, aligned price coverage, pre-event fit, and event-contamination checks. See `synthetic_control_donor_screening.md`. Never infer S&P 500 nonmembership from a ticker missing in a community snapshot.

The minimum two-unit check in code is an input-shape guard, not a defensible minimum donor-pool size. A small pool limits fit flexibility and makes placebo inference coarse; concentrated weights make results sensitive to a few firms. Report the complete weights and all screening decisions.

## Fit and inference

Pre-period RMSPE is a fit diagnostic, not evidence that the post-period counterfactual is valid. If a placebo analysis is later approved and specified, apply the same design to each eligible untreated unit, exclude treated/contaminated units from each placebo's donor pool, pre-specify a poor-pre-fit filter, and report the retained placebo count and sensitivity to that filter. Any rank-based placebo p-value relies on comparability/exchangeability assumptions and should be presented as a diagnostic, not a conventional randomized-treatment p-value.

The current helper contains no placebo inference; do not imply otherwise. Keep SCM results contextual: they do not test the project's primary DML confidence-interval coverage question.

## Data and restrictions

The branch has no donor-price panel. The terminal record states the local donor input file was empty, and CTLT historical adjusted prices were unavailable. No donor should be called eligible and no SCM result should be reported until data, evidence, and approval gates are satisfied.

The team lead requires explicit approval before the post-November 8 benchmark. Do not execute it until that approval is recorded.

## References

- Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic Control Methods for Comparative Case Studies. *JASA*, 105(490), 493–505. https://doi.org/10.1198/jasa.2009.ap08746
- Abadie, A. (2021). Using Synthetic Controls: Feasibility, Data Requirements, and Methodological Aspects. *Journal of Economic Literature*, 59(2), 391–425. https://doi.org/10.1257/jel.20191450
