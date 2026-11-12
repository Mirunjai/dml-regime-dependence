# Branch cleanup proposal — authorized and executed

**Follow-up:** the user approved this exact list. All seven remote references and
the clean local Session5 branch/checkout were deleted after matching-tip checks
and a verified Git-bundle backup. New Mirun source branches and Preksha Week 3
remain. The proposal below records the original rationale and approval boundary.

Remote snapshot: 12 November 2026; main `502bfa9`. No branch had been deleted at proposal time.
Approval applies only to explicitly named branches; recheck exact tips, open PRs
and worktrees immediately before any deletion. Preserve a verified Git bundle.

## Recommended deletion candidates

| Branch | Observed tip | Reason it is redundant |
|---|---|---|
| `deeptanshu/session5-week3-review` | `64e28dd` | Squash-integrated by PR #10. All 66 added/changed feature files are identical on main; only the accumulated project-state document differs. |
| `mirun/week2-closeout` | `e6d55d1` | Exact ancestor of main, with no unique commits. Its tip is the already merged Week 3 reporting integration. |
| `mirun/week2-consolidated-completion` | `a84b548` | Exact ancestor of main; Week 2 delivery already integrated through PR #5 and follow-up fixes. |
| `mirun/session5-reconstructed` | `ceb150e` | Reviewed through PR #10. 59 feature files match; the only three differing code/test paths are the documented stronger review corrections on main. No unique feature file is absent. |
| `Sudarshan` | `40d7165` | Week 1/2 and Week 3 delivery integrated through PR #4/#11. All nine feature/artifact files match; main additionally preserves the integration review, accumulated docs and current dependency comments. |
| `preksha/regime-shock-module` | `bfe19cb` | Week 1 module integrated through PR #2, then strengthened in later reviewed integrations. Remaining source/ignore differences are superseded fixes; no unique feature file is missing. |
| `preksha/week2-validation` | `8144aba` | Week 2 prototypes integrated with documented corrections in PR #9 and preserved through PR #12. The differing code is the reviewed/validated version on main; no unique feature file is missing. |

All seven remote references are candidates. For `deeptanshu/session5-week3-review`,
the local duplicate branch and `/tmp/ada-session5-review-20261110` checkout are also
proposed for removal if the user approves that scope. That checkout is clean; its
only ignored contents are pytest/bytecode caches, with no unique raw evidence.
The current final-submission branch and its uncommitted work remain untouched.

## Keep

| Branch | Reason |
|---|---|
| `main` | Shared integration branch. |
| `deeptanshu/final-submission-audit` (local) | Contains active, uncommitted work; preserve it. |
| `mirun/project-closeout-audit` | Open PR #14; new work absent from main. Reviewed fixes are local, not merged. |
| `mirun/week5` | Open PR #15; new engine/calibration work absent from main. Reviewed fixes are local, not merged. |
| `preksha/week3-benchmarks` | Reviewed code/docs are on main, but **nine raw Yahoo input/provenance files are absent from main by policy**. The branch is still an evidence archive, so it is not treated as useless. |

Do not delete active branches merely because their code exists in the local
working tree. Once the open PRs are safely integrated, reassess them separately.
