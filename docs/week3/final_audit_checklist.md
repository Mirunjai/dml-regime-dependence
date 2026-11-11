# Week 3 Final Audit Checklist for Deeptanshu

Status date: 2026-11-11. Branch: `preksha/week3-benchmarks`.

## Evidence and estimands

- [ ] Confirm frozen Gate 1 specification and event sample; this branch is secondary-benchmark work, not a scope change.
- [x] Verified event announcements/effective dates are recorded for the eight candidate additions.
- [x] Classical event-study output covers seven firms; CTLT is explicitly excluded for unavailable historical adjusted prices.
- [x] VIX generator uses trailing 20-session averages and trailing five-year event-specific references; saved cluster labels and values match the documented configuration on inspection.
- [x] Compared saved classical CAR rows with event-day-zero and window output: seven rows, 220 estimation observations each, market-model windows are recorded.
- [x] Results note reports CARs and VIX labels descriptively and flags shared announcement shocks.
- [ ] Confirm source price adjustment details, full estimator options, and data provenance from a clean execution in the actual checkout.

## Synthetic Control

- [x] Helper reviewed: nonnegative sum-to-one weights, pre-period fit, post gaps, concentration diagnostics.
- [x] Limitations documented: no automatic donor choice, placebo inference, or confidence intervals.
- [x] Donor screening schema and validator exist; validator is documentation completeness, not eligibility proof.
- [ ] Obtain historical donor universe, adjusted donor prices and point-in-time fundamentals / security attributes.
- [ ] Complete evidence-backed screening for index membership, industry, size, beta, liquidity, pre-event fit, coverage, and contamination; have a second reviewer sign.
- [ ] Address CTLT data gap or preserve its exclusion.
- [ ] Freeze donor pool, windows, exclusions, and input hashes.
- [ ] Obtain and record explicit team-lead approval before the post-November 8 SCM benchmark. No SCM benchmark has been run under this work package.
- [ ] If approved and data-complete: run the pre-specified benchmark, save weights/gaps/RMSPE and pre-specified placebo diagnostics, then independently audit outputs.

## Literature and claims

- [x] Novelty phrasing is limited to a proposed finite-sample combination; no “first” claim.
- [x] Adjacent dependent-data DML and 2026 papers are disclosed in the literature review.
- [ ] Recheck bibliographic metadata and working-paper versions before final external circulation.
- [ ] Clearly separate Monte Carlo coverage evidence (primary) from classical and SCM contextual benchmarks (secondary).

## Reproducibility and repository

- [x] Week 2 reports and output are archived in `docs/week2/`.
- [x] Week 3 methods, literature, results interpretation, and benchmark outputs are archived.
- [ ] Run the documented unit tests and donor evidence validator in the actual checkout; this environment had no local clone, so no execution is claimed here.
- [ ] The branch does not track `data/raw/week3_adjusted_prices.csv`; preserve or reacquire the authorized input and document retrieval date, version, adjustment, and redistribution limits. VIX source snapshot/retrieval metadata also needs recording.
- [ ] Confirm branch head and clean working tree in the actual checkout.

## Handoff

The H4 proposal rename is already committed. Additional documentation commits on this branch add the donor-screening status, SCM method limits, literature attribution update, audit checklist, and classical/VIX results note. Do not characterize the work package as fully complete: the donor pool, CTLT price series, explicit SCM approval, and SCM inference remain blockers.
