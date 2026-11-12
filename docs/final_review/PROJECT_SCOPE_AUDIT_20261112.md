# Proposal, weekly scope and branch audit — 12 November 2026

> Historical pre-integration snapshot. The user subsequently authorized Week 4
> integration and the named branch cleanup; see [the follow-up](WEEK4_INTEGRATION_20261112.md).

## Outcome

The reviewed Week 1–3 implementations for all four members are integrated into
`origin/main` at `502bfa9cf05eb0be338014ccda07e1349c012d06`, through PRs #2–#13
(excluding closed duplicate #8). Their scientific dependencies were not all
completed. Passing software tests and merging code do not close those requirements.

Main is **not** the complete current working project: Mirun's PR #14
(`mirun/project-closeout-audit`, `5afe045`) and PR #15 (`mirun/week5`, `5289a40`)
remain open. The reviewed combination, bug fixes, final-week tools, decision memo
and notebook work are local on `deeptanshu/final-submission-audit`, not committed,
pushed or merged by this audit. This distinction excludes the separate deliverables
folder as requested; even outside that folder, local source changes remain.

**Validation:** clean main: 395 tests; reviewed combined working source: 427 tests,
all with warnings treated as errors. The previous frozen release's 404-test record
is historical evidence for that source snapshot, not the current test count.
Notebook: expanded from 10 to 38 code cells, with 40 Markdown cells and a brief
explanation before each executable stage. Fresh-kernel results are recorded
separately in the deliverables clean-run record.

## Which proposal defines the scope?

| Source | What it proposed | Treatment in this audit |
|---|---|---|
| `Research_Proposal_A_CausalML_Financial_EventStudies.pdf` | Earlier seven-week design: earnings events, optional FOMC, five estimator families including Causal Forest/BMP/SCM, block bootstrap, 60,000 estimator runs | Historical proposal, substantially different from the later locked specification. These experiments were not executed and are not claimed complete. Its literature/novelty statements are historical claims, not a new current literature verification. |
| `ADA_Project_A_Financial_Event_Study_Causal_ML_Idea.docx` and identical `(1)` copy | Broader multi-estimator comparison; its H4 concerns method differences | Superseded by the later named Gate 1 documents. The copies are byte-identical. |
| `Project_A_One_Page_Proposal.docx` and `Project_A_Research_Idea_and_Methodology.docx` | DML-internal random/grouped × naive/robust; H4 few/many regimes at matched density; contextual benchmarks; qualitative S&P inclusion evidence | Governing research specification supplied for implementation. No new estimator/theorem or broad finance-reliability claim. |
| Week 1, Week 2, Week 3 plans | Component delivery, validation/design gates, then approved full runs and independent review | Used to distinguish implementation delivery from unresolved scientific work. |
| `Project_A_Final_Week_Plan_v3.docx` | Plan B if foundational validation is inconclusive; SCM closed; six artifacts plus clean-run/submission controls | Governing close-out path. Exploratory reporting is allowed; failed gates are not converted into passes. |

This audit records the change in supplied instructions, not an invented record of
mentor approval for the earlier-to-later transition. If the course reviewer still
holds the older PDF as the approved proposal, show the later locked documents and
explain the narrowed scope. No automatic marking or publication outcome follows.

## Weekly assignment reconciliation

| Week / owner | Required work | Evidence and implementation | Completion boundary |
|---|---|---|---|
| 1 / Mirun | Formal DGP, placeholders, assumptions and diagnostics | `research/week2_completion/dgp.py`, DGP/method notes and integration reviews | Implementation on main; financial realism and production validity are separate. |
| 1 / Deeptanshu | Own-shock GARCH, persistence knob, low/high diagnostics, stable intended variance | `src/dgp/volatility.py`, component reports, plots and reference checks | Delivered on main; canonical and calendar GARCH are separate families. |
| 1 / Preksha | Regime shocks, density candidates, assignment/timing explanation | `src/dgp/regime_shocks.py`, standalone demo/tests and Week 2 diagnostics | Delivered on main; configured density is not automatically realized event dependence. |
| 1 / Sudarshan | Config, seeds, repository/result structure and report scaffolding | `src/infra/`, `docs/Sudarshan_INFRA.md` | Delivered on main; mock infrastructure is labelled as such. |
| 2 / Mirun | Integrated candidate DGP, DML toy run, Gate 2 evidence and Gate 3 proposal | `research/week2_completion/`, completion pack, guarded calendar engine | Code/proposals delivered; gates not approved. New close-out additions remain PR #14/#15. |
| 2 / Deeptanshu | Persistence/stability/independence controls, coverage/size/MCSE and protocol | `reports/deeptanshu_week1_week2.md`, `src/evaluation/metrics.py`, DECISIONS P5 | Delivered on main as component evidence/proposed rules. |
| 2 / Preksha | Measured density, matched-K proposal, event/schema and classical prototype | `docs/week2/`, `src/dgp/matched_density.py`, event schema and benchmark prototype | Reviewed integration on main; single-membership prototype is separate from calendar memberships. |
| 2 / Sudarshan | Deterministic resumable runner and four-cell mock tables | Mock engine and report modules, reviewed PR #4 | Delivered on main; actual DML engine is a distinct path. |
| 3 / Mirun | Approved full-run campaign, raw archive, matched H4, robustness and Methods | Candidate engine, saved exploratory studies, Methods and reconstructed pilot evidence | Implementation delivered on main. Approved production run, matched H4 and original missing archives remain unresolved. |
| 3 / Deeptanshu | Independent pilot/full-run audit, monitoring, robustness audit and real-data diagnostics | Week 3 verifier, monitor, mock/actual controls and pilot reconstruction; final-week independent archive auditor | Week 3 tools/pilot review on main. Final-week raw audit is local. No approved full-run archive or agreed robustness subset to certify. |
| 3 / Preksha | Real data v1/labels, classical/SCM execution and provenance | Eight-event roster, six saved price histories, VIX rule and helpers; review PR #12 | Reviewed tools/docs on main. Old CAR inputs missing; SCM not run; daily broad calm/turbulent comparison unsupported. |
| 3 / Sudarshan | Pilot reproduction, chosen full-run subset, figures and reproducibility log | Reporting script, 128 saved-field checks, tables/plots and event metadata figure; PR #11 | Delivered reporting on main. Saved-summary agreement is not a new production replay; selected full-run subset remains unavailable. |

## Recovered original Week 2 Gate 2 criteria

The original `Week2_ADA.docx` explicitly enumerates **seven** checks. Earlier notes
referring to an unavailable eleven-item list do not mean that no original criteria
are available. These source criteria are now reconciled with final-week F1–F5:

1. Persistence changes actual temporal volatility persistence: component evidence
   available; distinguish the two alpha mappings and their moment conditions.
2. A measurable density setting changes realized dependence: structural exposure
   and pair-density response verified; a prospective outcome-level dense-dependence
   acceptance criterion remains unmet/inconclusive.
3. K changes independent shock information: regime counts/effective exposures are
   measured; an isolated matched-density H4 conclusion is not established.
4. Persistence and regime structure remain separate: named streams and source
   separation support construction; not a proof from a single small correlation.
5. Regime shocks independent of volatility state and treatment timing: separate-seed
   null/positive-control diagnostics now rerun on the exact calendar DGP; limited to
   the tested violations and not general independence proof.
6. Nonpathological returns, recoverable truth and an independent DML baseline that
   behaves sensibly: numerical/structural checks pass, but baseline robust inference
   undercovers and over-rejects. This foundational inferential requirement is not met.
7. An independent realized-dependence manipulation check: structural checks exist;
   the final prospective threshold/outcome-level validation is not ratified.

**Production remains NO-GO.** This audit does not fill YAML approval fields, sign
for teammates or turn a waived/inconclusive item into PASS.

## New branch review: findings and corrections

- PR #14 controls crashed from misspelled dictionary key
  `treatment_signed_shokc_corr`, followed by undefined `validation_seedr`.
  Both are corrected; the regression executes the actual control path.
- Nonfinite/constant correlations previously became NaN, which compared false at
  the threshold and silently counted as non-detection. Invalid diagnostics now fail
  explicitly; sigma must be positive/finite rather than being clipped before log.
- Control seed sets must be distinct, disjoint and large enough to estimate MCSE.
- A `uint8` membership product could overflow with 256 shared regimes; int64 and a
  regression case prevent the shared-pair indicator from becoming false.
- Direct script execution now resolves repository imports. GARCH diagnostic input
  and output paths resolve from the repository root rather than the caller's cwd.
- PR #15 adds useful shared-world fingerprints, strict complete-block aggregation
  and opt-in partial-run accounting. A manifest promising pairing can no longer
  accept records with all pairing metadata removed; genuine legacy manifests remain
  readable with their blocks explicitly unverified.
- Its calibration script paired the robust cells even when another cell failed.
  It now requires four successful identified outcomes. Every attempted world and
  a source/config/software manifest are saved, including failures; checkpoints are
  atomic and existing evidence cannot be overwritten. CI uploads the raw directory
  too. The 2,400-world calibration itself has **not** been run by this audit.
- The branch proposes both exposure matching and pair-density matching in different
  memos. They remain alternatives, not a ratified H4 quantity. CR2/bootstrap ideas
  remain unimplemented research proposals, not methods used in the release.
- Restored the missing `docs/gate1_specification.md` navigation target faithfully
  from the supplied source; no new gate authorization is implied.

Full fresh structural diagnostic: 600 grid worlds + 1,200 matching worlds + 800
control worlds + 200 known-truth worlds = **2,800 world builds**. The twelve
control detection numerators reproduce the incoming table exactly (100 trials per
arm): null rates 2/4/8/6%; targeted violation detections 100/93/100/100%. The known
truth identity's maximum error is 8.88e-16. Last-place decimal tie rounding in some
reported grid means is not scientific disagreement. This does not authenticate
an absent original archive. Local fresh output:
`results/raw/project_scope_audit_20261112/recomputed_gate2.json`.

The GARCH comparison also executes at both rho values and both parameterizations;
the rho=.99 fixed-alpha design lacks a Gaussian fourth moment while the canonical
variant narrowly has one. Neither family is silently substituted in the frozen
3,200-world campaign.

## Final-week tracker, after available work

| Task | Status |
|---|---|
| S9/S12 independent raw audit, exact coverage/size denominators, Wilson/MCSE | Verified exploratory archive: 3,200 complete worlds, 12,800 intervals, zero failed/missing cells. Historical authentication remains a separate gap. |
| S10 manipulation/independence evidence | Component checks and source-pinned integrated diagnostic rerun completed; prospective foundational validation remains inconclusive. |
| S13 shared-world orchestration, incomplete/failure handling | Tested in the actual engine and frozen driver; explicit identity and partial accounting added locally. |
| S4/S6/S8 team gates, production freeze and full production archive | Not complete; production NO-GO, Plan B explicitly documented. |
| S11 / D1 / D2 Mirun write-up and one-pager | Local evidence-labelled artifacts exist, with intentional team/section blanks. Human review required. |
| D3/D4/D7 notebook, dataset and clean run | Local package; notebook expanded and independently rerun. See exact clean-run record, not the old ten-cell PASS. |
| B2–B5 sample reconciliation, VIX and daily diagnostics | Six saved histories and 1,872 returns reconciled; prior-only label arithmetic independently checked; insufficient common calm support prevents the planned broad contrast. |
| B1 original classical output | Original combined panel/^GSPC missing; cannot certify the old seven-row CAR output from SPY replacements. |
| B6 Synthetic Control | Closed / NOT EXECUTED under the supplied final plan, not a successful benchmark. |
| D5 PPT | Local content and export exist; course-template mapping and human review remain. |
| D6 video | Existing rehearsal preserved; new rendering explicitly stopped at user request. All-member recordings still needed. |
| D8 submission | Team name/sections, sharing emails/form and human final check outstanding. No Drive upload/sharing or form submission performed. |

The six-firm count is not itself a failure criterion. The binding issue for the
planned calm/turbulent comparison is aligned observations and documented labels.
The positive presentation framing is retained while material scope boundaries
stay visible; detailed fixable issues are recorded separately in the package TXT.

## Reproduction and evidence

- Original-source fingerprints and full extraction map:
  `results/raw/project_scope_audit_20261112/sources.json`; retained source index
  alongside this report.
- Fresh main and reviewed test XML: `main_pytest.xml`, `reviewed_pytest.xml` in
  that same local raw audit directory.
- Main/squash provenance: PRs #2–#7 and #9–#13; open PRs #14/#15. Branch content
  comparisons check the actual trees, not ahead counts after squash merges.
- Branch-deletion proposal: [separate reviewed list](BRANCH_CLEANUP_PROPOSAL_20261112.md).
  **No branch has been deleted. User confirmation is required.**
- The final notebook's input SHA, semantic source SHA, versions and execution
  counts are recorded under `ADA PROJECT DELIVERABLES/07_Audit_and_Reproducibility`.

No new Git commit, push, merge, video rendering or course submission was performed.
