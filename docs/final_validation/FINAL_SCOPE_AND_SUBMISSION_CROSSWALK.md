# Final Scope and Submission Crosswalk

**Reviewed against:** current `main` release at `0d9d622`  
**Prepared on:** 2026-11-13  
**Status:** final registered DML study is complete for its revised scope; the original broader proposal and course handoff are not fully complete.

## Research scope

| Requirement or claim | Current status | Evidence / boundary |
|---|---|---|
| Four-cell DML comparison: random/grouped cross-fitting × naive/robust inference | Complete for the registered final grid | 78 scenarios; 43,200 complete blocks; 172,800 primary intervals; 24 control cells pass the registered rule. |
| Robust inference and grouped-fold findings | Complete, bounded | CR2 substantially improves focal coverage; grouping adds no material benefit under the registered paired rule. K=4 robust inference still undercovers. This is not equivalence or a universal validity claim. |
| Dependence manipulation and few/many-regime comparison | Complete for selected definitions | Pair-probability and exposure matches were executed. Neither matches the full covariance structure, so claims must stay narrow. |
| Known-truth classical and Synthetic Control comparison | Not completed / excluded | Fresh classical results are descriptive event results, not a comparable known-truth simulation benchmark. Synthetic Control was explicitly excluded and was not run. |
| Real-data four-cell DML inference comparison | Not demonstrated | The real-data panel supports descriptive dependence and event-study context; it does not validate the Monte Carlo coverage findings. |
| Authenticate older project results using original inputs | Unresolved | The original combined-price and replication archives were not recovered. Fresh reconstructions must remain labeled as fresh evidence. |
| Full proposal completed without scope changes | No | The final registered study is narrower than the original broader proposal. The final report documents the change and limits. |

## Implementation and reproducibility

The current main release reports 439 tests passing in GitHub CI and a 48-stage notebook clean run. Those are Git-checkout and recorded clean-run results. The independent audit separately ran the source archive and found six failures caused by Git metadata lookups, plus a notebook assertion that compared all floating-point fields exactly. Those archive/runtime portability limitations do not contradict the main CI result, but they must not be described as fully fixed until the source archive and notebook checks are rerun in their supported environments.

The notebook builder now compares audit identities, types, counts and structure exactly, while allowing a stringent 1e-12 tolerance for derived floating-point summaries. A generated final notebook still needs to be rebuilt and run from the actual final bundle to verify this source change.

The offline requirements file cited in the independent audit is not tracked in this repository. It should include the notebook runtime dependencies, including IPython and a compatible Jupyter kernel, and identify the supported Python/package versions. The actual deliverables ZIP or requirements bundle is needed to finish that check.

## Submission handoff

- Team name provided: **Bullish Breakout**.
- Course section: none provided.
- The one-pager was explicitly left unchanged, along with the PPT and video.
- PPT editing is intentionally left untouched at the user's request.
- Video production is being handled by the team.
- Drive sharing and form submission remain team handoff items; no receipt is recorded in Git.

## What “complete” means

The implementation is complete for the revised, registered DML study and supported by main-branch CI/replay evidence. It is **not** complete for every item in the original proposal or for final course submission. The remaining technical work in this branch is to rebuild and check the non-PPT deliverables from the actual artifact bundle, complete the archive/Jupyter environment instructions, and rerun the updated notebook in a clean supported runtime. The human handoff items above remain with the team.

No code or docs were changed directly on `main`; this crosswalk and the non-PPT fixes are isolated on `preksha/final-audit-fixes`.
