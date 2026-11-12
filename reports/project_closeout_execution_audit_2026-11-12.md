# Project A close-out execution audit — 12 November 2026

## Purpose and status

This report consolidates the repository evidence for the remaining Project A work. It is an execution audit, not a Gate 2/Gate 3 approval and not a final-results report. Gate decisions remain team decisions under the project workflow. The locked research question and scope are unchanged.

**Overall status: software foundation substantially built; scientific validation and final submission are not complete.**

The primary question remains: under dense regime-clustered common-shock dependence, does robust variance estimation alone restore 95% DML interval calibration, or does regime-aware grouped cross-fitting add inferential benefit?

## Verified repository baseline

- Audited branch: `main`
- Audited commit: `502bfa9cf05eb0be338014ccda07e1349c012d06`
- Repository: `Mirunjai/dml-regime-dependence`
- Latest main commit is the 12 November 2026 CSV line-ending normalization (PR #13).
- PRs #1–#7 and #9–#13 are merged; PR #8 was closed without merge. No open PR was present in the prior repository audit.
- The main branch contains the DGP/DML implementation, guarded experiment engine, validation modules, benchmark helpers, reports and tests.
- The latest documented integrated test result is 395 passing tests with warnings treated as errors (Preksha Week 3 review). This is a recorded prior local result, **not a fresh test run performed for this audit**. Main has no configured CI workflow and the latest commit has no CI status checks.
- The connected execution environment could read repository files through GitHub but could not clone the private repository through its shell because DNS/network resolution to github.com failed. No claim is made here that the current checkout's tests were rerun.

## Scientific blockers that must be resolved before production

### 1. Gate 2: event-level density and matched-K semantics are not yet locked

The current `research/week2_completion/dgp.py` generator sets a fraction of calendar periods active, then allocates contiguous blocks across regimes. Its `density` parameter is an active-calendar-time fraction. It is not the realized exposed-event share or the share of event pairs sharing a regime shock. The generator does create shared-regime event clusters; the issue is that the configured value is not the event-level estimand and the K comparison is not matched as currently configured.

Existing evidence in `reports/mirun_gate2_evidence.md` and `reports/mirun_undercoverage_diagnosis.md` reports:
- At K=4, density=.5, no multi-regime events in 80,000 events.
- At K=16, only 280/80,000 events (0.35%) touch multiple regimes.
- Calendar-window overlap share is about 3.48% in the cited diagnostic.
- The canonical `src/dgp/matched_density.py` measures single-membership event-index pair density and explicitly does not accept the calendar DGP's multi-membership contract.

A source-faithful independent replay of the membership portion of `simulate_calendar_regimes` and the DGP's named `SeedSequence` streams was run for 40 seeds per K/calendar-density setting (n=400, T=260, H=5). It reproduces the event start-time and regime-layout stream contract, but it is not an execution of the full repository module; treat it as an independent diagnostic reconstruction, not Gate 2 approval.

| K | Active calendar fraction | Exposed-event share | Event-pair share sharing ≥1 regime | Multi-regime event share |
|---:|---:|---:|---:|---:|
| 4 | .25 | .3181 | .0253 | .0000 |
| 4 | .50 | .5646 | .0799 | .0000 |
| 4 | .75 | .8195 | .1683 | .0000 |
| 16 | .25 | .5048 | .0159 | .0000 |
| 16 | .50 | .7544 | .0359 | .0026 |
| 16 | .75 | .9594 | .0630 | .0469 |

A second calibration scan (30 seeds per candidate calendar-density value, step .025) matched **exposed-event share** across K, consistent with the tracker’s candidate density definition (“fraction of events whose windows overlap a common regime shock”):

| K | Target exposed-event share | Calendar fraction used | Realized exposed share | Event-pair shared-regime density | Multi-regime event share |
|---:|---:|---:|---:|---:|---:|
| 4 | .32 | .250 | .3183 | .0253 | .0000 |
| 4 | .56 | .500 | .5665 | .0800 | .0000 |
| 4 | .82 | .750 | .8243 | .1697 | .0000 |
| 16 | .32 | .075 | .3212 | .0064 | .0000 |
| 16 | .56 | .300 | .5528 | .0190 | .0008 |
| 16 | .82 | .575 | .8232 | .0431 | .0093 |

Interpretation: the current calendar-time parameter is not itself the event-level density. At a matched exposed-event share, K=4 and K=16 generate very different shares of event pairs that share a shock. This is potentially the intended H4 contrast (few versus many regime shocks), but the team must explicitly decide that **exposed-event share is the matched quantity** and report pair density, membership-count distribution and multi-regime share as structural diagnostics. Since multi-regime events remain rare, the current design is predominantly one-regime-per-event clustering; it should not be described as a heavily exercised multi-membership design. The monotone movement of exposure and pair density is encouraging, but the exact full DGP must run the diagnostic through `build_world` and the team must set thresholds before Gate 2 can pass.

### 2. Variance estimator: CR0-normal is anti-conservative even in a control

The current robust method is full regime-membership overlap sandwich CR0 with normal critical values. The exploratory undercoverage report records:
- Independent-control coverage about .870/.875 for random/grouped robust cells.
- For K=4, gamma=1, empirical size about .143/.151 at nominal .05.
- For K=16, gamma=1, empirical size about .087/.083.
- t(G-1) alternatives substantially improve K=4 coverage but are conservative in zero-effect size and reduce power; they remain proposals, not validated replacements.

This means the present robust estimator cannot be treated as a successful correction. It does **not** prove that all dependence-robust variance estimators fail. A pre-production estimator decision must be based on an independently validated control, size, coverage, power and failure-rate study. The production engine currently implements only `overlap_sandwich_full_membership_CR0_normal`; alternative pivots need implementation, tests and review before use.

### 3. Gate 3 is still proposal-only

`configs/mirun_gate3.yaml` explicitly marks Gate 2, Gate 3, root seed, replication count, estimator, grid, failure policy, materiality threshold and robustness subset as awaiting team approval. The guarded production engine correctly refuses production execution without these approvals. This report does not override that guard.

The proposal's 24 primary conditions and 1,000 replications are candidate settings only. A production campaign must not be launched by substituting proposed values for approved values.

## Benchmark and real-data status

The latest repository review records:
- Eight frozen treated events; fresh price coverage is complete for six of eight firms.
- Two treated firms (ADS and CTLT) lack complete fresh-price coverage in the reviewed acquisition.
- Seven old classical CAR rows are not independently reproducible because their original combined inputs are unavailable.
- Eight VIX event labels reproduce, but event-specific calm/mixed/turbulent labels are not a frozen daily labelled return/residual panel.
- The Synthetic Control donor candidate CSV is empty and no final SCM run exists. Donor eligibility and input data remain unresolved.
- CRSP is unavailable in the documented source review; free-source alternatives and point-in-time membership evidence have limitations.

These facts support a transparent limitations section, not a claim that the qualitative real-data stage or SCM benchmark is complete.

## Deliverable inventory on main

| Deliverable | Repository evidence | Status |
|---|---|---|
| One-page proposal | Original source document exists outside the repository; no final tracked one-pager | Source exists; final package not verified |
| Jupyter notebook | No `.ipynb` in main | Missing |
| Dataset package | Partial processed CSVs; raw pulls ignored; no complete frozen daily labelled panel | Incomplete |
| Presentation | No `.pptx` in main | Missing |
| 3–5 minute video | No `.mp4` in main | Missing |
| IEEE report | Methods draft and Results template only; no final PDF/DOCX | Incomplete |

This inventory describes the audited GitHub main branch only. It does not claim that no teammate has local or Drive copies.

## Required execution order

1. **Gate 2 repair and evidence:** implement an explicit event-pair dependence diagnostic for the calendar DGP; run the exact repository generator across the proposed settings; define and match the H4 density quantity; verify positive and negative controls, treatment/shock independence and volatility/shock independence. Record every failed check.
2. **Variance decision:** evaluate CR0-normal, the separately proposed small-sample alternatives and an independent-control benchmark. Measure coverage, empirical size, power, interval width, MCSE and failed-cell rate. Keep each estimator separately labelled. Select one before production results are examined.
3. **Gate 3 ratification:** team signs the exact grid, seed rule/root seed, replications, failure policy, materiality criterion, manipulation-check thresholds, robustness subset and estimator. Archive dated approval.
4. **Production campaign:** use the guarded engine only with the ratified configuration. Preserve all attempted per-replication records, manifests, source hashes, software versions and failure states. Do not silently retry or discard failed cells.
5. **Independent verification:** a second person independently recomputes aggregates from raw records and verifies paired comparisons and all reported figures.
6. **Real-data/benchmark close-out:** either obtain complete point-in-time treated/donor data and run the pre-specified methods, or explicitly narrow the report and mark unavailable analyses as limitations. Do not invent CAR/SCM outputs.
7. **Submission package:** create and verify the notebook, documented dataset package, final one-page proposal, IEEE-style report, presentation and video. Ensure all figures and tables trace to frozen results and provenance.

## Course deadline and team ownership

The re-baselined workflow targets result freeze on 8 November and a submission-ready package by 13 November, but explicitly says the official deadline must be confirmed with course staff. Those dates are planning targets, not verified official deadlines. The team tracker assigns benchmark/data ownership to Preksha, statistical verification to Deeptanshu, infrastructure/reporting to Sudarshan and DML/scientific integration to Mirun. The research lead can coordinate and prepare integration, but cannot fabricate teammate verification or team gate approval.

## Final statement

Project A has substantial reusable software and exploratory evidence. It does not yet have an approved and validated dense-dependence DGP, a selected and validated primary variance estimator, an approved Gate 3 configuration, a complete production Monte Carlo archive, a complete real-data/SCM analysis, or a verified final submission package. The next work must close these scientific and provenance gaps before results are presented as final.
