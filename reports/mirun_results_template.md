# Results template (NO RESULTS GENERATED — every cell below is a placeholder)

Fill only from an approved production run produced by `src/infra/dml_engine.py`, using `aggregate()` output. Pilot or exploratory numbers must never be copied here. Every table needs: run directory id, git commit, config hash, replication count, failure counts.

## R0. Run provenance
| Field | Value |
|---|---|
| Run id / directory | `[PLACEHOLDER]` |
| Git commit / config hash | `[PLACEHOLDER]` |
| Approval record (who/when) | `[PLACEHOLDER — AWAITING_TEAM_APPROVAL]` |
| Replications planned / completed / failed per cell | `[PLACEHOLDER]` |

## R1. H1 — naive variance under dependence (coverage of 95% CI)
| K | density | gamma | cross-fitting | coverage | MCSE | Wilson 95% | failed |
|---|---|---|---|---|---|---|---|
| `[ ]` | `[ ]` | `[ ]` | random / grouped | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

## R2. H2 — robust variance (and separately labelled estimator proposals, if approved)
Same columns; one block per variance estimator. Proposal estimators are reported beside the primary, never instead of it.

## R3. H3 — central contrast: random+robust vs grouped+robust (paired by replication)
| Condition | coverage random+robust | coverage grouped+robust | paired difference | MCSE | 95% interval | discordant pairs | verdict (material / not material / inconclusive) |
|---|---|---|---|---|---|---|---|
| `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
Material-difference rule: `[PLACEHOLDER — AWAITING_TEAM_APPROVAL]` (proposal: >= 3 pp and interval excludes 0).

## R4. Zero-effect empirical size (tau = 0)
| Condition | cell | size | MCSE | Wilson 95% |
|---|---|---|---|---|

## R5. H4 — trade-offs
Bias, RMSE, mean interval width, power (tau != 0), failure rate, grouped-fold feasibility and balance (max/min fold size), runtime.

## R6. Negative controls and sensitivity
Independent control, factor-only, factor-off (unmatched / variance-matched), n = 400 vs 1000, second learner. State pass/fail against the approved criteria, not the proposed ones.

## R7. Gate 2 diagnostics and undercoverage diagnosis (link, do not copy numbers)
`reports/mirun_gate2_evidence.md`, `reports/mirun_undercoverage_diagnosis.md`.

## R8. Real-data qualitative check
`[MISSING — requires Preksha's panel and labels]`. Not Monte Carlo evidence.

## Figure placeholders
F1 coverage by cell and condition with MCSE bars; F2 paired difference forest plot; F3 size under zero effect; F4 SE/sd by cell; F5 fold balance; F6 failure/runtime summary. `[NOT GENERATED]`

## Limitations to state
`[PLACEHOLDER — one DGP family, learners, folds, seeds; independent audit status]`
