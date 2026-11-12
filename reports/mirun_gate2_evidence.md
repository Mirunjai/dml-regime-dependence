# Gate 2 evidence matrix (Session 2) — NOT an approval

**`AWAITING ORIGINAL DOCUMENT / TEAM CONFIRMATION`: the "11 required checks" cannot be reconstructed.** No file in the repo defines eleven checks. What exists: the 8-row table in `docs/WEEK2_COMPLETION_PACK.md`, legacy checks A-E in `research/week2_mirun/gate2_checks.py`, and diagnostics in `research/week2_completion/validation.py`. Rows 1-8 below are the memo's; rows 9-10 are checks Mirun's instructions list that the memo lacks; row 11 is a provenance item. Which of these are the original 11 is unknown. Statuses use only PASS/FAIL/INCONCLUSIVE/MISSING; no thresholds were pre-declared by the team, so nothing is PASS on thresholds.

| # | Check | Evidence (file / command) | Actual result | Status | Limitation / follow-up |
|---|---|---|---|---|---|
| 1 | GARCH persistence / stability | `gate2_checks.json` A (legacy fixed-alpha, `arch` pkg not installed here, not rerun); `scripts/mirun_dgp_scan.py` | ACF5 of r^2 .007->.165 for rho .5->.98; fitted persistence tracks input. Default rho=.9 finite 4th moment; rho=.99 infinite (legacy) | INCONCLUSIVE | Legacy GARCH, not canonical; rho=.99 pathology; no unconditional-variance report in current JSON; Deeptanshu owns |
| 2 | Density manipulation | memo (K4: overlap 0/.166/.314/.567/.823); structure JSON | Monotone in density; exposed share != density; varies with K | INCONCLUSIVE | Threshold not pre-declared; define the density quantity |
| 3 | Regime count effect | memo; structure JSON | Overlap at d=.5 .52 (K1) -> .91 (K32) | INCONCLUSIVE | Confounded with density definition |
| 4 | Matched density | memo; `src/dgp/matched_density.py` (single-membership event-index generator only, not the calendar DGP) | Gamma-ablation K4 vs K16 not matched (.43 vs .25) | FAIL (as currently configured) | Matching quantity undecided; team decision |
| 5 | Volatility-shock independence + positive control | `gate2_checks.json` E (legacy) | Production corr -0.001 (t=-0.4); positive control corr .70 (t=232) | INCONCLUSIVE | Evidence is legacy DGP only; current DGP's `break_vol_independence` not run; non-rejection is not proof |
| 6 | Treatment-timing independence + positive control | `gate2_checks.json` E (legacy) | D vs shock -0.009 (t=-1.4); date vs shock -0.012; control .45 (t=85) | INCONCLUSIVE | Memo called it OPEN; legacy evidence exists but not for the calendar DGP |
| 7 | Known-truth baseline sanity (gamma=0, zero-effect size) | `reports/mirun_pilot_reproduction.md` | Legacy gamma=0 coverage .94-.97 (200 reps). Calendar variant only 20 reps (MCSE .07-.08) | INCONCLUSIVE | No bias/RMSE/size package at adequate n under candidate DGP |
| 8 | Membership structure | structure JSON | Multi-regime events 0% of worlds at K<=4; 38-100% of worlds at K8 d.75 / K16 d>=.5 | INCONCLUSIVE | Multiway machinery unexercised at default; team must say if intended |
| 9 | Fold construction / balance / leakage | `scripts/mirun_fold_variance_diagnostics.py`, 12 tests | Feasible in all worlds; balanced except K2 d.75 (6x); regime leakage 0; calendar leakage 7-70% | INCONCLUSIVE | Calendar-factor dependence not separated; see grouped-folds report |
| 10 | Event-window / common-factor alignment | `validation.py` pair density; structure JSON | Calendar-sharing pairs ~2,782 per world (3.5%); not regime-aligned | INCONCLUSIVE | Event-time vs calendar-time mapping vs canonical `src/dgp` undecided |
| 11 | Saved Gate 2 JSON provenance | `results/week2_gate2.json` | Schema v1, **no base_config**, 50 seeds; current code writes schema v2 | INCONCLUSIVE | Cannot tie saved file to a recorded config; regenerate under a declared config (`run_gate2`) |

Not executed this session: `run_gate2` regeneration, persistence/ACF sweep on the calendar DGP, positive controls on the calendar DGP, current-DGP size at adequate n. **Gate 2 is not approved; approval belongs to the team.**

---
## Session 4 update (regenerated with explicit provenance; still NOT an approval)
Command: `python -m scripts.mirun_regen_gate2 --raw results/raw/mirun_session4/gate2_regen.json --summary results/tables/mirun_gate2_regen_summary.json` — default `Config()` (n=400, T=260, H=5, K=4, density .5, persistence .90, alpha .10, sd_factor .5), seeds 60000-60099 (100), schema_version 2, config hash + git state + software versions recorded in the summary. Calendar DGP, unmodified.

| # | Update | Result | Status |
|---|---|---|---|
| 1 | Analytic GARCH table (alpha=.10): persistence .9 has 3a^2+2ab+b^2=.83<1 (finite 4th moment); .99 gives 1.0001 (infinite); unconditional variance 1 by construction; empirical mean r^2 of unit-variance returns .9987; 0 NaN/Inf; max |return| 8.1 | stable at the default; ACF persistence sweep on the calendar DGP not rerun | INCONCLUSIVE |
| 5 | Vol-shock independence with positive control on the **calendar DGP**: production Spearman corr(sigma, |U|) +0.008, t=1.23; injected dependence detected, corr .76, t=117 | detects injected dependence; non-rejection is not proof | PASS (criterion |t|<2 with detectable control is Mirun's, not team-ratified) |
| 6 | Treatment-timing independence: production corr(D, U_win) -0.014, t=-0.93; control .42, t=30.9 | as above | PASS (same caveat) |
| 7 | Known-truth baseline: bias/sd -.01 to +.10 (tau-hat essentially unbiased); but size under tau=0 is .14-.15 at K=4 (robust, existing estimator) | calibration failure is an estimator finding (see undercoverage report), no team criterion for acceptable size | INCONCLUSIVE |
| 8 | At the default K=4, d=.5: 0 multi-regime events in 100 worlds; mean exposed share .576, pair density .083 | multi-membership machinery unexercised at default | INCONCLUSIVE |
| 11 | Regenerated Gate 2 file has config, seeds, config hash, git state; the old `results/week2_gate2.json` remains schema v1 and unlinked | provenance gap closed for the new file; raw JSON is gitignored (hash in summary) | PASS |
Rows 2, 3, 4, 9, 10 are unchanged. The "11 checks" remain undefined (AWAITING ORIGINAL DOCUMENT / TEAM CONFIRMATION); Gate 2 is not approved.

---
# Session 5 completion of the Gate 2 evidence package (NOT an approval)

## Research question and diagnostic design
Does dependence-robust variance estimation alone restore 95% CI calibration for DML under regime-clustered events, or does grouped cross-fitting add inferential benefit? Gate 2 asks whether the DGP and diagnostics are sound enough to design Gate 3. Design: structural scans (no nuisance fit), fitted-score scans, controls, and regenerated diagnostics, all on the unmodified calendar DGP.

## Mathematical definitions
- Scores: psi_i = D~_i (Y~_i - tau_hat D~_i); tau_hat = sum D~Y~ / sum D~^2; J = sum D~^2.
- Naive variance: sum psi_i^2 / J^2. Existing robust: (psi' A psi)/J^2, A_ij = 1{events i,j share >= 1 regime}, A_ii = 1. If each event has <= 1 regime this is the CR0 cluster-sum (PSD); with multi-membership A may be indefinite (example `{0},{0,1},{1}`: min eigenvalue 1 - sqrt 2), so psi'A psi can be negative; the code records a failed cell and never clips.
- Effective clusters G_eff = (sum s_g)^2 / sum s_g^2 over regime sizes s_g. SE/sd = mean reported SE / sd of tau_hat across replications (1 = calibrated). Size = rejection rate of H0: tau=0 when tau=0. Coverage MCSE = sqrt(p(1-p)/N).
- GARCH(1,1): h_t = omega + alpha r_{t-1}^2 + beta h_{t-1}; Gaussian fourth moment finite iff 3 alpha^2 + 2 alpha beta + beta^2 < 1.

## Assumptions and what the diagnostics can/cannot show
Regime-only dependence is assumed by the robust estimator; independence checks that fail to reject do not prove independence (positive controls show detectability); pilots are exploratory; one DGP family; thresholds below are proposals.

## Evidence table (statuses: generated / reproduced / independently verified)
| Item | Evidence | Generated | Reproduced | Independently verified |
|---|---|---|---|---|
| Dependence structure; regime clustering; cluster sizes; effective units | structure scan (100 worlds x 16 cells), G_eff 3.95/4, 15.2/16 | yes | partly (seeds recomputed in different scripts agree) | no |
| Calendar-factor dependence | factor-only, factor-off, variance-matched controls | yes | no | no |
| Fold leakage; grouped feasibility/balance | structure scan; 5 grouped folds feasible in all worlds; K=2,d=.75 imbalance 6x | yes | no | no |
| Variance-estimator validity | 12 characterisation tests; 0/2,000 failed cells; iid control undercoverage of CR0-normal | yes | no | no |
| Coverage and size; Monte Carlo uncertainty | 200-1000 rep pilots with MCSE/Wilson; paired contrasts | yes | historical pilots reproduced (520 fields, 0 discrepancies) | no |
| GARCH: calendar vs canonical | `results/tables/mirun_garch_canonical_vs_calendar.json`: same rho/omega/variance; alpha .10 vs .09 at rho .9; kurtosis 3.35 vs 3.28 (theory 3.353 / 3.28); r^2 ACF lag 1 .133 vs .118; burn 500 vs 1000; row-major draw vs per-step draw; different paths for the same seed | yes | no | no |
| Overlap (default Config, 200 worlds) | K=4: 0/80,000 multi-regime; K=16: 280/80,000 (the earlier "12/80,000" is **not reproduced**); calendar-window overlap share 3.48% (earlier 3.489%) | yes | partly | no |
| Gate 2 regeneration | seeds 60000-60099, positive controls t=31 and 117 | yes | no | no |

## Commands
`python -W error -m pytest -q`; `python -m scripts.mirun_regen_gate2 ...`; `python scripts/mirun_session5_checks.py {garch,overlap} --out <json>`; `python scripts/mirun_session5_checks.py run --out results/raw/mirun_session5/controls --reps 200`; `... summarize --dir ... --out ...`; others in `reports/mirun_audit_package_deeptanshu.md`.

## Proposed acceptance criteria (NOT team-approved; AWAITING_TEAM_APPROVAL)
1. Independent control: naive cells within 2 MCSE of .95 (pilot: random .930 +- .018 passes; grouped .900 +- .021 is 2.4 MCSE low, borderline).
2. Positive controls detected (|t| > 3) and production |t| < 2 for the two independence diagnostics (pilot passes).
3. Grouped folds feasible with max/min fold size <= 2 in the primary grid (fails at K=2,d=.75; primary grid K in {4,16} passes in the structure scan).
4. Variance-estimator failure rate <= 2% (pilot 0/2,000).
5. Robust-variance calibration in the independent control within 2 MCSE of .95 — **currently fails** (.870/.875): the existing estimator is not acceptable as a calibrated baseline unless the estimator question is settled.
6. DGP realizes non-trivial dependence: naive coverage < .93 in the primary dependence condition (pilot .74/.65) while the factor-only condition is not what drives it.

## Unresolved decisions
The "11 checks" document; estimator choice; whether the DGP should add genuine dense common-shock dependence (the calendar factor currently adds none); overlap level; GARCH parameterisation (calendar alpha=.10 vs canonical arch_share). **Gate 2 is not passed; criteria above are not approved and criterion 5 currently fails.**
