# Project instructions

## Scope and research boundaries

- Follow the locked Gate 1 question: random/grouped cross-fitting crossed with
  naive/robust variance. Coverage is primary; empirical size is the key diagnostic.
  Similar performance of the two robust cells is a valid result.
- Deeptanshu owns firm-level GARCH, its validation, standalone coverage/size/Monte
  Carlo metrics, and the protocol proposal. Do not take over teammates' tracks.
- Inspect actual files and evidence before treating a weekly plan as completion.
  See `docs/PROJECT_STATE.md` for the latest audited snapshot.
- Discuss significant approaches before implementation and wait for user approval.
  Numerical settings, validation thresholds, replication budgets, and final
  experimental design require the appropriate Gate 2/Gate 3 team decision.
- Do not implement final DML experiments, benchmarks, or real-data pipelines under
  the standalone volatility/metrics task. Do not claim novelty without a literature audit.

## Scientific correctness

- GARCH must use only each firm's own idiosyncratic shocks and lagged variance.
  Never feed common factors, regime shocks, treatment, or total returns into it.
- Hold intended unconditional variance fixed when varying persistence. Distinguish
  conditional variance, conditional standard deviation, standardized innovations,
  and idiosyncratic returns. Document shapes, units, initialization, and burn-in.
- Check finite fourth moments before interpreting squared-return ACFs; finite
  unconditional variance alone does not guarantee this.
- Use explicit NumPy generators and separate recorded random streams for components
  and independent replications. Do not depend on worker scheduling for seeds.
- Keep known simulation truth in evaluation, outside estimator/adaptation inputs.
  Preserve held-out scoring boundaries in any later DML integration.
- Never clip or normalize away pathological paths silently. Record failures,
  denominators, seeds, and configurations. Independence diagnostics need a
  deliberately dependent positive control; a small correlation is not proof.
- Label mock checks, smoke tests, actual-component validation, and gate approvals
  separately. Real data with unknown truth cannot establish coverage.

## Workflow and verification

- Read `README.md`, `CONTRIBUTING.md`, and relevant decision proposals first.
- Prefer small standalone NumPy modules; use portable paths and a project-local
  environment. Do not change global Python packages without discussion.
- Consult original papers and official implementations before research-specific
  implementation. Keep reference clones outside this repository, in the parent
  directory's `references/`. Check licenses before adapting source.
- Test recurrence, shape, parameter boundaries, deterministic replay, and meaningful
  statistical properties. Test metrics against mock intervals with known outcomes.
  Execute a small example and review the complete diff before reporting success.
- Update existing `docs/PROJECT_STATE.md` after meaningful milestones.
  Record proposed decisions in `docs/DECISIONS.md`; never imply they were approved.
- Preserve existing work. No destructive Git commands or force-pushes. Do not
  create commits or push without explicit user authorization. Stage only related
  files after approval; exclude raw data, credentials, and large generated artifacts.
