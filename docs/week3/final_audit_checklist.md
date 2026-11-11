# Week 3 Final Audit Checklist for Deeptanshu

Status date: 2026-11-11. Branch: `preksha/week3-benchmarks`.

## Evidence and estimands

- [ ] Confirm frozen Gate 1 specification and event sample; this branch is secondary-benchmark work, not a scope change.
- [x] Verified event announcements/effective dates are recorded for the eight candidate additions.
- [x] Classical event-study output covers seven firms; CTLT is explicitly excluded for unavailable historical adjusted prices.
- [x] VIX regime method is documented as pre-announcement, trailing 20 sessions, with event-specific historical thresholds; inspect the generated labels against the documented configuration before citing categories.
- [ ] Reconcile the exact VIX reference configuration used by the generator, output, and method document (the method document currently says trailing five years; ensure code and result match).
- [ ] Check all classical event-study rows against event-day-zero file and verify estimation/event windows, market proxy, missingness, and adjusted-return definitions.
- [ ] Report clustered announcements as shared shocks; do not treat firms in the same cluster as independent replications.

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
- [ ] Recheck all bibliographic metadata and working-paper versions before final external circulation.
- [ ] Clearly separate Monte Carlo coverage evidence (primary) from classical and SCM contextual benchmarks (secondary).

## Reproducibility and repository

- [x] Week 2 reports and output are archived in `docs/week2/`.
- [x] Week 3 methods, literature, and benchmark outputs are archived in `docs/week3/` and `results/benchmarks/`.
- [ ] Run the documented unit tests and donor evidence validator in the actual checkout; this environment had no local clone, so no execution is claimed here.
- [ ] Confirm raw price files are available from the authorized source and document retrieval date, version, adjustment, and any licensing/redistribution limits.
- [ ] Confirm branch head and clean working tree after the final commit.

## Handoff

Current checked-in branch head at audit: `499138b63199a5522d6c8c94fb4c3a02d542275c`. The H4 proposal rename is already committed there. Do not characterize the branch as fully complete: the donor pool, CTLT price series, explicit SCM approval, and SCM inference remain blockers.
