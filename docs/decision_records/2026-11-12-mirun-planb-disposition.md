# Project A — lead authorization and Plan B disposition

**Decision date:** 12 November 2026  
**Decision owner:** Mirun, project lead; authorization supplied directly in the project conversation.  
**Repository baseline:** `Mirunjai/dml-regime-dependence`, `main` at `502bfa9cf05eb0be338014ccda07e1349c012d06`.  
**Disposition:** **Plan A production NO-GO. Plan B selected for the current submission. Gate 2 and Gate 3 remain NOT APPROVED.**

## Authorization boundary

Mirun instructed the assistant to complete the remaining project decisions and work. This records the project-lead disposition and authorizes documentation, analysis and packaging. It does not claim that Deeptanshu independently verified Mirun's work, that Preksha or Sudarshan signed off, or that course staff approved the submission. Those human approvals remain outstanding wherever the course workflow requires them.

## Decision register

| ID | Disposition | Reason / boundary |
|---|---|---|
| DEC-1 — dependence quantities | Report configured calendar-active fraction, event-exposed share, unconditional shared-pair density, conditional exposed-pair density, multi-regime-event share, membership-count distribution and effective regime count separately. Treat unconditional shared-pair density as a candidate H4 matching quantity; report event exposure as a separate primary structural descriptor. | These quantities are not interchangeable. Matching one does not establish equivalent dependence structures. |
| DEC-2 — DGP | Retain the existing calendar-time DGP as exploratory; no redesign under this close-out. | Rare multi-regime membership and incomplete integrated validation mean a redesign needs a separately reviewed specification. |
| DEC-3 — variance | No production primary variance estimator is approved. Keep full-membership CR0-normal as the legacy comparator only; CR0-t and CR1-regime+t remain exploratory proposals. | The exploratory zero-effect pilot shows CR0-normal size distortion; alternatives can be conservative at K=4 and still under-cover at K=16,n=400. No candidate is validated across the intended design. |
| DEC-4 — production design | Do not freeze a production grid, root seed, replication budget or acceptance thresholds. Preserve the locked 2x2 research question. | Those choices must follow validated DGP manipulation and a validated primary variance method. |
| DEC-5 — Gate 2 | **NO PASS / NOT APPROVED.** | Foundational checks are missing, inconclusive or fail. The original authoritative eleven-check list was not found. |
| DEC-6 — Gate 3 | **NOT LOCKED / NOT APPROVED.** | Estimator and production configuration are not validated. |
| DEC-7 — submission route | **Plan B selected. Plan A production GO withheld.** | This is a project-lead disposition under the current evidence, not a claim that the research question has been answered. |
| DEC-8 — benchmarks | Real-data and benchmark work remain contextual. Synthetic Control is deferred and **NOT EXECUTED**. | Original classical inputs/sample remain unreconciled; event-specific VIX labels are not a daily labelled return panel; no eligible donor pool or SCM output exists. |

## Evidence and limits

The exploratory Session 4 report records, at nominal 5% size, K=4, gamma=1 and zero effect, CR0-normal rejection rates of 0.143 (random folds) and 0.151 (grouped folds), based on 1,000 replications. At K=16 the corresponding rates are 0.087 and 0.083. An independent-control summary reports robust coverage around 0.870 and 0.875, but the original raw control archive was unavailable for independent replay. These are exploratory diagnostics, not production estimates.

The t(G-1) alternative improves some K=4 nonzero-effect coverage but can reduce zero-effect size to roughly 0.01–0.024 and materially reduce power. At K=16,n=400, it still under-covers. No alternative is approved as a replacement.

The Plan B structural audit has a candidate pair-density match: K=4 at calendar fraction .31 versus K=16 at .50, with reconstructed shared-pair densities 3.5852% and 3.5848%; event-exposed shares differ 37.87% versus 75.33%. This is a match of one chosen quantity only.

**Source provenance:** the notebook and the 1,000-world structural audit included in the submission package use local DGP/DML mirrors whose Git blob hashes do not match the reviewed `main` source files. Treat those numerical outputs as exploratory reconstruction, not as a clean-`main` reproduction. Separately, PR #14 adds an exact membership-parity diagnostic and tests against the integrated DGP; its GitHub Actions run passed 401 tests with warnings treated as errors. That is software validation, not scientific Gate 2/3 approval or a production coverage campaign.

## Submission package boundary

The package contains a one-page summary, preliminary IEEE-style report, Gate 2/3 decision brief, 12-slide general-purpose deck, preliminary notebook, structural audit script/JSON, metadata-only dataset package and 3–5 minute team video script. It does not contain a complete production DML coverage campaign, complete daily labelled return dataset or an MP4 recorded by the team. The official course PowerPoint template was not supplied.

## Remaining human and environment handoffs

1. Deeptanshu's independent audit of the DGP/DML work and the recorded variance/size diagnostics.
2. Preksha and Sudarshan's confirmation of their owned benchmark, data and reproducibility contributions.
3. A fresh clean-checkout notebook and test rerun using the reviewed repository source.
4. Mapping the deck to the official course template.
5. Team-recorded 3–5 minute MP4, final team/section/member metadata, team Drive folder, required TA/Bhaskarjyoti Das viewer permissions and Google Form submission.

## Conditions to reopen Plan A

Recover the authoritative Gate 2 checklist; validate positive and negative controls on the exact integrated DGP; validate a primary variance method on size, coverage, power, interval width and failure rates; freeze the grid, estimand, root seed, replication count and failure policy before production; run paired four-cell worlds with all attempts/failures retained; obtain independent recomputation; and record explicit Gate 2/Gate 3 approvals before issuing a production GO.

---

**Recorded authorization:** Mirun's direct instruction in the project conversation on 12 November 2026: “Complete all of this, approval to everything, do it yourself.”  
**Recorded outcome:** Plan B selected; Plan A production NO-GO; Gate 2 and Gate 3 NOT APPROVED.