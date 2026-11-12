# Week 3 Final Audit Checklist for Deeptanshu

Status date: 2026-11-12. Branch: `preksha/week3-benchmarks`.

## Final free-data attempt update (2026-11-12)

- [x] Reconciled the frozen treated roster: eight firms across four clusters; no sample change.
- [x] Re-ran Yahoo/yfinance with a saved script and retrieval manifest. Six treated panels are complete; ADS and CTLT returned no history.
- [x] Saved treated, exploratory price-lead, and SPY panels plus missing-session and data-quality reports.
- [x] Saved community membership snapshot checks and the September 2020 change-log excerpt; official cross-check is still incomplete.
- [ ] SEC point-in-time SIC and shares evidence: archive requests returned HTTP 403; no market cap or fully validated matching.
- [ ] Donor eligibility: no candidate passes all frozen criteria; the donor CSV remains unpopulated.
- [ ] SCM: remains blocked; no benchmark run.

## Evidence and estimands

- [ ] Confirm frozen Gate 1 specification and event sample; this branch is secondary-benchmark work, not a scope change.
- [x] Verified event announcements/effective dates are recorded for the eight candidate additions.
- [x] Classical event-study output covers seven firms; CTLT is explicitly excluded for unavailable historical adjusted prices.
- [x] VIX generator uses trailing 20-session averages and trailing five-year event-specific references; saved cluster labels and values match the documented configuration on inspection.
- [x] Compared saved classical CAR rows with event-day-zero and window output: seven rows, 220 estimation observations each, market-model windows are recorded.
- [x] Results note reports CARs and VIX labels descriptively and flags shared announcement shocks.
- [ ] Confirm source price adjustment details and full estimator options from a clean execution. The new Yahoo extraction records raw/adjusted fields, actions, retrieval date, parameters and library versions, but Yahoo adjusted-close point-in-time methodology and end-to-end project checkout provenance still need review.

## Synthetic Control

- [x] Helper reviewed: nonnegative sum-to-one weights, pre-period fit, post gaps, concentration diagnostics.
- [x] Limitations documented: no automatic donor choice, placebo inference, or confidence intervals.
- [x] Donor screening schema and validator exist; validator is documentation completeness, not eligibility proof.
- [x] Saved full-window price panels for the existing exploratory donor leads with per-security coverage; these are price-only and do not certify donor eligibility.
- [ ] Obtain verified point-in-time fundamentals / security attributes and authoritative membership evidence for eligible donors.
- [ ] Complete evidence-backed screening for index membership, industry, size, beta, liquidity, pre-event fit, coverage, and contamination; have a second reviewer sign.
- [x] CTLT retained as a missing-data case after the prior Quiver attempt and the fresh Yahoo/yfinance attempt returned no usable history; exclude it from any complete-case SCM.
- [ ] Freeze donor pool, windows, exclusions, and input hashes.
- [x] Team-lead approval received for remaining post-November 8 SCM work, conditional on all donor and price gates below; it does not authorize execution before those gates pass.
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
- [x] Branch now tracks the reproducible Yahoo treated and exploratory price panels, SPY panel, request logs, data-quality report, missing-session lists and manifest.
- [ ] VIX source snapshot/retrieval metadata still needs recording.
- [ ] Confirm branch head and clean working tree in the actual checkout.

## Handoff

The H4 proposal rename is already committed. The final free-data attempt added a corrected eight-firm coverage matrix, Yahoo panels and acquisition scripts, membership snapshots, SEC retrieval attempt trace, price-based metrics, and a donor eligibility report. Additional documentation commits on this branch add the donor-screening status, SCM method limits, literature attribution update, audit checklist, and classical/VIX results note. Do not characterize the work package as fully complete: the eligible donor pool and validated donor price panel remain blockers; CTLT stays excluded from complete-case SCM unless a full approved adjusted-price series is obtained; benchmark execution and placebo inference remain pending the prerequisites.
