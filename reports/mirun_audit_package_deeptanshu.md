# Statistical audit package for Deeptanshu (Mirun sessions 2-4)

Scope: independent verification requested; **nothing below has been independently verified**. Everything is exploratory on the calendar DGP (`research/week2_completion`) unless stated, with the legacy DGP (`research/week2_mirun`) kept separate. The primary estimator and DGP were never modified; alternatives live in `research/mirun_proposals/`. Branch `mirun/execution-session1`, base `b558156`, nothing committed. Environment: Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.1.1. Use `OPENBLAS_NUM_THREADS=1 PYTHONPATH=.`

## A. Setup
`git apply handoff/mirun-progress.patch` on `b558156`; `pip install -r requirements-dev.txt`; `python -W error -m pytest -q` (354 expected). Raw outputs: tarball `mirun_raw_outputs.tar.gz` (same tree as `results/raw/`); verify with `results/tables/mirun_raw_manifest.json` (file counts, bytes, directory sha256 from `scripts/mirun_raw_manifest.py`).

## B. Experiment register
| ID | Question | Command (abridged) | Config / seeds / reps | Raw dir | Summary table |
|---|---|---|---|---|---|
| E1 | Do saved pilots reproduce? | `scripts/replay_mirun_pilots.py --output results/raw/mirun_session2/replay`; completed with `python -m scripts.mirun_resume_legacy_replay --dir ... --budget-seconds 230` (x2); `scripts/audit_mirun_replays.py ...` | pinned commit 26e65f1; calendar seeds 20000+r (20 reps x 4 scenarios), legacy 10000+r (1,020 unique worlds) | `mirun_session2/{replay,audit}` (`replay_aborted_partial` = killed first run, kept) | `mirun_session2_replay_audit_summary.json`, `mirun_session2_pilot_summary.json` |
| E2 | Structure of folds / overlap matrix | `python -m scripts.mirun_fold_variance_diagnostics --seeds 100 --out ...` | seeds 20000-20099, K x density grid | (tracked JSON) | `mirun_fold_variance_structure.json` |
| E3 | Sandwich failure rate, fitted scores | `python -m scripts.mirun_failure_rate_scan --out results/raw/mirun_session3/failure_scan --reps 200` | seeds 30000+r, gamma=1, tau=1, 5 settings x 200 | `mirun_session3/failure_scan` | `mirun_failure_rate_scan.json` |
| E4 | Why grouped sd is larger | `python -m scripts.mirun_grouped_spread_mechanism --out ... --reps 200 --gamma 1` (and `--reps 100 --gamma 0`) | K=4, d=.5, seeds 30000+r, 8 variants incl. oracle (truth) | `mirun_session3/mech_K4_g{1,0}` | `mirun_grouped_spread_mechanism_K4_gamma{1,0}.json` |
| E5 | Calendar factor off? | `PYTHONPATH=. python scripts/mirun_factor_off_check.py <out> {4,16} 200 230` | sd_factor=0, seeds 30000+r | (tracked JSON) | `mirun_factor_off_K{4,16}.json` |
| E6 | Source of undercoverage; alternatives; larger n | `python -m scripts.mirun_undercoverage_study run --out results/raw/mirun_session4/uc_K{K}_n{n} --K K --n n --reps 200 --routes ...` | seeds 30000+r; K in {4,16}; n in {400,1000,2500}; routes rf_random, rf_grouped, gbr_random, oracle (K=4,n=400 only) | `mirun_session4/uc_*` | `mirun_undercoverage_K*_n*.json`, `mirun_power_and_effective_clusters.json` |
| E7 | Zero-effect size | `... run --out .../size_K4_g1 --K 4 --reps 1000 --tau 0 --gamma 1 --seed0 50000 --routes rf_random rf_grouped` (K=16 g1 1000 reps; K=4 g0 500 reps) | seeds 50000+r, n=400, d=.5 | `mirun_session4/size_*` | `mirun_zero_effect_size_K*_gamma*.json` |
| E8 | Gate 2 regeneration | `python -m scripts.mirun_regen_gate2 --raw results/raw/mirun_session4/gate2_regen.json --summary results/tables/mirun_gate2_regen_summary.json` | default Config, seeds 60000-60099; config hash in summary | `gate2_regen.json` (gitignored, not in manifest dirs) | `mirun_gate2_regen_summary.json` |
Engine (`src/infra/dml_engine.py`): smoke runs only; bit-identical to direct `run_dml` (test).

## C. Suggested independent checks
1. Recompute coverage/size/SE-over-sd for E3, E6, E7 from the raw JSON with your own code (formulas: SE/sd = mean reported SE / sd of tau across reps; size = share |tau - truth| > crit*SE).
2. Re-run replication 0 of E6 (K=4, n=400, seed 30000) and E7 (seed 50000) and compare tau/SE to raw files bit-for-bit.
3. Check the overlap sandwich algebra (`psi' A psi`, A_ij = shared-regime) and that `research/mirun_proposals/variance_alternatives.py` reduces to the repo estimator (`tests/test_mirun_proposals.py`).
4. Verify the oracle residuals (`research/mirun_proposals/nuisance.py`): E[D|X] formula assumes single membership (exact only for K=4, d=.5; at K=16 the oracle route was not run).
5. Challenge the conclusions below (esp. #3, #4) with another learner/fold count.

## D. Findings (exploratory) and limitations
1. Pilot reproduction: 520 fields, 0 discrepancies; reconstructions come from pinned source, original raw archives never existed; shared seeds across tables.
2. 0/2,000 failed multiway cells (gamma=1, tau=1 only).
3. Existing robust SE is 69-90% of the true sd; bias <= .13 sd; oracle nuisance and GBR don't fix it; calendar factor and cluster-size heterogeneity (G_eff ~ G) are not the cause; cause unresolved (see diagnosis report sec. 4).
4. Size (tau=0): robust .143/.151 (K=4 g1), .087/.083 (K=16 g1), .084/.114 (K=4 g0, 500 reps); grouped-random paired difference not detectable at g1, +.030 +- .010 at g0 (one comparison of several; no multiplicity adjustment).
5. Grouped sd inflation 1.23x at K=4 g1 requires alignment with true regimes (size-matched random 1.01x, pseudo-blocks .98x); mechanism consistent with held-out regime effects being unlearnable, not isolated.
6. Limitations: one DGP family; RF (40 trees) + one GBR; 5 folds; n up to 2500 at random folds only; t(G-1)/CR1-regime are heuristic proposals, power not size-adjusted; the |t|<2 + positive-control criterion in Gate 2 rows 5-6 is Mirun's, not team-ratified; the "11 Gate 2 checks" are undefined; seeds blocks used: 10000+, 20000+, 30000+, 50000+, 60000-60099.
## E. Unresolved / for Deeptanshu to decide with the team
Cause of residual SE deficit at G=16; whether to ratify a t(G-1)/CR1-regime estimator proposal before production; canonical vs fixed-alpha GARCH comparison; the 11-check list; independent confirmation of E7.
