# Week 3 Repository Audit Status

**Branch:** `preksha/week3-benchmarks`  
**Updated:** 2026-11-11  
**Audit type:** GitHub contents review. No tests or benchmark were run.

This note corrects the earlier path-check summary in this file. Several deliverables were present under different filenames/paths; the earlier exact-path checks did not enumerate the directories and incorrectly described them as missing.

## Week 3 documentation and outputs present

The branch contains:

- Methods and interpretation: `docs/week3/classical_event_study_methods.md`, `docs/week3/classical_and_vix_results.md`, `docs/week3/vix_regime_methods.md`, `docs/week3/synthetic_control_methods.md`, and `docs/week3/synthetic_control_donor_screening.md`.
- Literature and source work: `docs/week3/literature_novelty_review.md`, `docs/week3/historical_data_source_audit.md`, `docs/week3/alternative_data_sources_review.md`, and `docs/week3/norgate_sec_validation_status.md`.
- Handoff: `docs/week3/final_audit_checklist.md`.
- Results: `results/benchmarks/week3_classical_event_study.csv`, `week3_regime_labels.csv`, `week3_benchmark_windows.csv`, and `week3_window_coverage.csv`.
- Processed inputs: event evidence, S&P membership history, VIX history, event-day-zero mapping, treated-event candidates, price diagnostics, and the donor-screening template.
- Week 2 archive: `docs/week2/dependence_validation_output.txt`, `dependence_validation_report.md`, `h4_matching_output.txt`, and `h4_matching_proposal.md`.

The donor-screening template has seven treated-event rows but its donor evidence fields are blank. It is a schema/template, not an eligible donor shortlist. The result documents state that CTLT is excluded from classical complete cases because its adjusted-price history was unavailable.

## Confirmed data and reproducibility gap

The branch has no `data/raw/` directory or tracked `data/raw/week3_adjusted_prices.csv`, although the prior terminal transcript reports that file in the local working copy. Therefore the tracked classical and VIX results cannot be regenerated from a clean checkout using only branch contents. The price data must be preserved/reacquired through an approved source with retrieval details and adjustment settings.

The tracked VIX history exists, but the results note says its source snapshot/retrieval metadata is not encoded in the output. Record its source, retrieval date and version/provenance if the final reproducibility checklist requires clean regeneration.

## Source audit reconciliation

`docs/week3/historical_data_source_audit.md` previously named CRSP/WRDS as the recommended source. The team has since confirmed institutional access is unavailable. That file must be corrected to record CRSP/WRDS as unavailable and point to the newer alternatives review and Norgate access status. No subscription purchase or benchmark execution is authorized by this audit.

## Remaining sign-off items

The existing `docs/week3/final_audit_checklist.md` correctly leaves outstanding: clean-run provenance, historical donor-universe and adjusted-price validation, point-in-time screening evidence, an independent reviewer, and final donor-pool/input hashes. The exact Norgate historical sample is still gated on a separate purchase decision; the free trial cannot cover the 2008 event period.

No event window, matching criterion, project scope, or scientific result was changed. No test or benchmark was run.
