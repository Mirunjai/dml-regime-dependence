# Mirun pilot reproduction (Session 2)

Status: **Reproduced** (independent recomputation by the repo's audit + a second summary script). Exploratory pilots only; nothing here is a Gate 2/3 approval or a final conclusion.

## What was run (exact commands, branch `mirun/execution-session1`, base `b558156`)
1. `python scripts/replay_mirun_pilots.py --output results/raw/mirun_session2/replay` — extracts source from pinned commit `26e65f1`, replays seeds `20000+r` (calendar DGP, `week2_mc.json`: 4 scenarios x 20 reps) and `10000+r` (legacy `week2_mirun` DGP: 15 scenarios, 1,260 scenario references, **1,020 unique worlds**).
2. The first launch was killed by the sandbox (background processes do not survive between tool calls) after 78/80 calendar worlds; that directory is retained unmodified as `results/raw/mirun_session2/replay_aborted_partial`. The second launch completed the calendar part and was killed at 469/1020 legacy worlds. `scripts/mirun_resume_legacy_replay.py` (new, reuses the original `worker`, skips saved attempts, no overwrite) completed the remaining 551. All 1,020 attempt files parse; none was edited.
3. `python scripts/audit_mirun_replays.py --calendar-dir ... --legacy-dir ... --output results/raw/mirun_session2/audit --summary results/tables/mirun_session2_replay_audit_summary.json`
4. `python scripts/mirun_pilot_summary.py <legacy_intervals.csv> <calendar raw_intervals.csv> results/tables/mirun_session2_pilot_summary.json` (new; independent recomputation of coverage, Wilson intervals, paired contrasts, sd).

Environment: Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, pandas 3.1.1 (Session 1 recorded pandas 3.0.6; not used by the estimators).

## Result
- **520 numeric fields compared with saved summaries; 0 discrepancies; 0 coverage discrepancies; max |delta| 4.4e-16.** All planned replication IDs present (calendar 320 rows, legacy 5,040 rows). **0 failed cells** in every reconstructed scenario.
- Caveat: this reproduces the *published reviewer-reconstructed tables from pinned source*. Original raw archives never existed in the repo (`docs/PROJECT_STATE.md`), so "original raw records" cannot be compared. Repeated worlds across tables (same seeds) are not independent samples.
- Legacy and calendar variants are different DGP/estimator pairs and are reported separately, never pooled.

## Legacy variant, 200 reps (coverage, MCSE) — random/naive, random/robust, grouped/naive, grouped/robust
| Scenario | R/N | R/Rb | G/N | G/Rb | sd(tau-hat) R vs G | G-R robust (paired) |
|---|---|---|---|---|---|---|
| K4 gamma0 | .970 (.012) | .945 (.016) | .945 (.016) | .940 (.017) | .28 / .29 | -0.005 +- .013 |
| K4 gamma1 | .820 (.027) | .905 (.021) | .730 (.031) | .865 (.024) | .43 / .51 | **-0.040 +- .019** |
| K16 gamma0 | .965 (.013) | .970 (.012) | .955 (.015) | .955 (.015) | .27 / .27 | -0.015 +- .013 |
| K16 gamma1 | .915 (.020) | .935 (.017) | .940 (.017) | .945 (.016) | .31 / .31 | +0.010 +- .014 |

## Calendar variant (`week2_mc.json`), 20 reps — MCSE ~.07-.08, uninformative
Coverage .85-.90 in all cells for all four gamma/tau scenarios; robust and naive cells are often identical; zero-effect "size" at n=20 is not interpretable. No conclusion can be drawn.

## Session 1 claims checked
| Claim | Verdict |
|---|---|
| 200-rep pilot shows no miscalibration at gamma=0 | Confirmed (.94-.97; all within ~2 MCSE of .95) |
| gamma=1, K=4: grouped covers worse than random | Confirmed numerically (.73/.865 vs .82/.905). Paired robust difference -0.040 +- 0.019 (~2.1 MCSE): suggestive, **not decisive**; not seen at K=16 |
| Grouped sd larger | Confirmed only at K4 gamma1 (.51 vs .43); absent at gamma0 and at K16 |
Cause not established (see `reports/mirun_grouped_folds_diagnostics.md` for hypotheses; none tested by an intervention yet).

## Limitations
No new DGP draws beyond the pinned seeds; no canonical-GARCH rerun; legacy GARCH has infinite 4th moment at rho=.99 (not used in these pilots, which use persistence .9). Raw outputs live in gitignored `results/raw/mirun_session2/` and are **not** in the patch; the small summary tables in `results/tables/` are.
