# Gate 2 density mapping: operational definition and H4 matching proposal

Status: **technical proposal / diagnostic evidence; not a team Gate 2 approval.**

## Why the mapping must be explicit

In research/week2_completion/dgp.py, Config.density controls the fraction of calendar periods assigned to contiguous active regime blocks. It is not equal to the fraction of event windows exposed to a regime shock, nor to the fraction of event pairs that share at least one regime shock. The configured parameter therefore cannot be reported as realized event dependence without structural diagnostics.

## Quantities to report separately

For event i with regime-membership set M_i:

- **Calendar active fraction:** configured active calendar periods divided by T.
- **Event-exposed share:** n^{-1} sum_i 1{|M_i|>0}; this is the closest operational analogue to the project's original candidate definition, “fraction of event windows exposed to a common regime shock.”
- **Unconditional shared-pair density:** [sum_{i<j} 1{M_i intersect M_j is nonempty}] / choose(n,2).
- **Conditional pair density among exposed events:** shared pairs divided by pairs for which both events are exposed.
- **Multi-regime event share:** n^{-1} sum_i 1{|M_i|>1}.
- **Membership-count distribution:** number of events with zero, one, two, ... regime memberships.
- **Effective regime count:** inverse-Herfindahl summary of event-to-regime exposure counts; report with the raw counts.

The event-exposed share describes how many event windows are hit. Unconditional pair density describes how broadly those events share common shocks. They are related but not interchangeable.

## Structural audit already included in the Plan B package

The accompanying Plan B package contains an exploratory structural diagnostic of 1,000 worlds per setting, seeds 2000–2999, n=400, T=260, H=5 and shock SD 0.40. It reports:

| K | Calendar active fraction | Event-exposed share | Unconditional shared-pair density | Multi-regime event share | Effective regimes |
|---:|---:|---:|---:|---:|---:|
| 4 | .25 | .3169 | .02511 | .00000 | 3.91 |
| 4 | .50 | .5696 | .08114 | .00000 | 3.95 |
| 4 | .75 | .8229 | .16930 | .00001 | 3.96 |
| 16 | .25 | .5040 | .01589 | .00025 | 14.90 |
| 16 | .50 | .7533 | .03585 | .00408 | 15.24 |
| 16 | .75 | .9556 | .06271 | .04875 | 15.41 |

The event-exposed share and pair density both rise with configured calendar activity, but equal calendar fractions do not mean equal event-level dependence across K. Multi-regime event windows are rare in much of the grid, especially at K=4. This is a structural membership audit; it does not estimate outcome-return correlation or DML coverage.

## Candidate H4 pair-density match

The same 1,000-world audit finds a candidate match of the **unconditional shared-pair density**:

| K | Calendar fraction | Unconditional pair density | MCSE | Event-exposed share |
|---:|---:|---:|---:|---:|
| 4 | .31 | .0358521 | .0001421 | .37869 |
| 16 | .50 | .0358482 | .0000679 | .75334 |

The paired difference (K=4 minus K=16) is 0.00000382 with MCSE 0.000155. This is a near-match of one chosen structural quantity. Event-exposed share differs by about 37.5 percentage points, so the two configurations are **not equivalent dependence structures**.

## Proposed Gate 2 / Gate 3 treatment

1. Use event-exposed share as the main descriptive density axis because it matches the original proposal's language. Report configured calendar fraction and unconditional pair density beside it.
2. For H4, consider the K=4,d=.31 versus K=16,d=.50 pair-density match as a distinct comparison. Explicitly state that event-exposed share is not matched. The team must ratify whether this is the intended H4 matching estimand or reject it.
3. Do not claim that the current DGP heavily exercises multi-membership; it does not in most tested settings.
4. Set manipulation-check thresholds before any production DML coverage results are examined. Structural pair density alone does not establish outcome-level dependence.
5. Re-run volatility/shock and treatment/shock independence positive-control checks on the exact integrated DGP and retain source/config/seed provenance.

## Reproducible repository diagnostic

A helper is included at scripts/mirun_event_density_diagnostic.py. It imports the same spawn_rngs and simulate_calendar_regimes implementation as the integrated DGP, recreates event-window memberships, and reports all event-level measures with Monte Carlo uncertainty. It also supports a separate calibration scan for matching event-exposed share across K. That scan is useful as an alternative sensitivity analysis, but it does not replace the candidate pair-density H4 match above.

Example:

    python -m scripts.mirun_event_density_diagnostic \
      --n 400 --T 260 --H 5 \
      --regimes 4 16 \
      --densities 0.25 0.50 0.75 \
      --reps 100 --seed-start 91000 \
      --calibrate-targets 0.32 0.56 0.82 \
      --out results/tables/mirun_event_density_audit.json

The tests in tests/test_mirun_event_density_diagnostic.py check exact membership parity against build_world, boundary cases, multi-membership counting and invalid IDs. The CI run on the close-out branch passed 401 tests with warnings treated as errors.

## Gate decision still required

The team must decide before production results are examined:

- Whether event-exposed share is the main density axis and unconditional pair density is the H4 matched quantity.
- Whether the candidate K=4,d=.31 / K=16,d=.50 pair-density match is accepted, revised or rejected.
- Whether the current rarity of multi-regime windows is acceptable for the locked research question.
- Which numerical manipulation-check thresholds are justified and pre-declared.
- Whether the integrated DGP passes the volatility/shock and treatment/shock independence positive-control checks.

Until the team records these decisions and remaining criteria pass, Gate 2 remains **NOT APPROVED**.
