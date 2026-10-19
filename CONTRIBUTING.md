# Contributing

This describes how the four of us actually use this repo day to day. It follows the non-blocking, parallel-track workflow in the team tracker — nobody waits on anybody else's branch to start their own work.

## Branches

- **`main`** is always in a working state. No direct pushes — everything lands via Pull Request.
- Create one branch per task, named `<yourname>/<short-topic>`:
  - `mirun/dgp-skeleton`
  - `deeptanshu/garch-volatility`
  - `preksha/regime-shock-module`
  - `sudarshan/repro-infra`
- Delete your branch after it's merged.
- Skip shared integration branches unless a weekly merge genuinely gets tangled — if so, agree on an `integration/week<N>` branch at the review, and dissolve it once merged.

```bash
git checkout main
git pull
git checkout -b deeptanshu/garch-volatility
# ... work ...
git push -u origin deeptanshu/garch-volatility
# open a PR into main
```

## Commits

Prefix with a type so the history is scannable:

```
feat(dgp): add regime shock module with density diagnostic
fix(dml): correct grouped cross-fitting fold assignment
docs: update gate 2 validation report
data: add sp500 inclusion dataset v1
test: add coverage check for mock intervals
chore: update requirements.txt
```

## Pull requests

1. Open a PR from your branch into `main` as soon as the work is ready for review (even mid-week — don't wait for the Sunday review to open it).
2. Fill in the PR description:
   - **What this does** (1–2 sentences)
   - **Which week / gate / deliverable** this maps to
   - **How to run it** (command or notebook)
   - Any open questions for the reviewer
3. Request your verifier as reviewer, per the tracker's second-person pairing:
   - Mirun's DGP/DML work → reviewed by **Deeptanshu**
   - Deeptanshu's volatility/stats work → reviewed by **Mirun**
   - Preksha's regime/benchmark/data work → reviewed by **Deeptanshu** (dependence diagnostics) or **Mirun** (benchmarks)
   - Sudarshan's infra work → reviewed by whoever uses the tool next
4. One approval is enough to merge. Use **Squash and merge** so `main` keeps one clean commit per task.
5. Reference the related issue so it closes automatically: `Closes #12`.

> [!TIP]
> A PR that can't be reviewed in a few minutes is usually trying to do too much. Smaller, more frequent PRs keep the non-blocking workflow actually non-blocking.

## Working independently

- Your module should run and be testable **on its own inputs** (mock data, a toy panel, placeholder values) — never require someone else's unfinished branch.
- If you need another module's output, use the **last merged version on `main`**, not someone's in-progress branch.
- Blocked on something? Say so in the group chat within 24 hours — don't sit on it until the weekly review.

## Issues and the project board

- Each row of the Deliverables Checklist becomes an Issue, labeled by person (`mirun`/`deeptanshu`/`preksha`/`sudarshan`), week (`week1`…`week7`), and gate (`gate2`…`gate7`).
- The board columns mirror the weekly protocol: **Backlog → This Week → In Progress → In Review → Done**.
- Move your own cards; Mirun reconciles the board at the weekly review.

## Data and large files

- Don't commit raw simulation output or raw S&P 500 data. `results/raw/` and `data/raw/` are gitignored — regenerate them from a config and seed instead.
- Commit only small summary tables/figures needed for the report (`results/figures/`, `results/tables/`).
- If a file genuinely needs to be versioned and is large, ask the group about Git LFS before committing it — don't commit large binaries directly.

## Code style

- Keep modules documented with a short README or module-level docstring explaining inputs, outputs, and assumptions.
- Add at least one test per module in `tests/`, even a basic sanity check (shapes, no NaNs, expected direction of effect).
- Don't invent final numerical parameters that belong to a later gate — follow what's locked in `docs/gate1_specification.md` and whatever the team decided at the most recent gate review.

## Scientific boundaries

This repo implements a locked specification. Don't redesign the research question, hypotheses, or scope in code or docs without a team decision — see `docs/gate1_specification.md` for what's frozen and what Gate 2+ is allowed to decide.
