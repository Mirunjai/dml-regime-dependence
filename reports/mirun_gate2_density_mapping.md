# Gate 2 density mapping: operational definition and validation plan

Status: **technical proposal / diagnostic helper; not a team Gate 2 approval.**

## Why this clarification is needed

In research/week2_completion/dgp.py, Config.density is passed to the calendar regime generator. It controls the fraction of calendar periods assigned to contiguous active regime blocks. It is not equal to the fraction of event windows exposed to a regime shock. It is also not equal to the fraction of event pairs that share at least one regime shock.

The locked Week 1/2 plan describes a candidate density measure as the fraction of events whose windows overlap a common regime shock. This note recommends making that the primary operational density definition, while separately reporting the event-pair dependence measure.

## Definitions to report separately

For event i with regime-membership set M_i:

- **Calendar active fraction:** configured active calendar periods divided by T.
- **Exposed-event share:** n^{-1} sum_i 1{|M_i|>0}.
- **Shared-regime pair density:** [sum_{i<j} 1{M_i intersect M_j is nonempty}] / choose(n,2).
- **Multi-regime event share:** n^{-1} sum_i 1{|M_i|>1}.
- **Membership-count distribution:** number of events with zero, one, two, ... regime memberships.

The exposed-event share measures the proportion of event windows hit by the common-shock mechanism. The pair density measures how broadly event errors share the same regime-level shock. These are related but not interchangeable.

## Exploratory source-faithful reconstruction

A local diagnostic reimplementation followed the repository's named RNG streams, calendar-block allocation, and event-window mapping (n=400, T=260, H=5). It used 40 seeds for the default grid and 30 seeds per candidate calendar-density in the exposure-matching scan. The full repository test suite and exact source-based CLI were not runnable in the connected shell because GitHub DNS resolution failed. These numbers are therefore **exploratory reconstructed diagnostics, not generated repository artifacts, formal validation or Gate 2 approval**.

### Current proposed grid, no matching across K

| K | Calendar active fraction | Exposed-event share | Shared-regime pair density | Multi-regime event share |
|---:|---:|---:|---:|---:|
| 4 | .25 | .3181 | .0253 | .0000 |
| 4 | .50 | .5646 | .0799 | .0000 |
| 4 | .75 | .8195 | .1683 | .0000 |
| 16 | .25 | .5048 | .0159 | .0000 |
| 16 | .50 | .7544 | .0359 | .0026 |
| 16 | .75 | .9594 | .0630 | .0469 |

The density dial is monotone for both K values, but equal calendar settings do not mean equal event exposure. At density .50, exposure is about .565 for K=4 and .754 for K=16.

### Candidate matched-exposure settings for H4

A grid search with step .025 selected the following calendar fractions to approximately match exposed-event share across regime counts:

| K | Target exposed share | Calendar active fraction | Realized exposed share | Shared-regime pair density | Multi-regime event share |
|---:|---:|---:|---:|---:|---:|
| 4 | .32 | .250 | .3183 | .0253 | .0000 |
| 4 | .56 | .500 | .5665 | .0800 | .0000 |
| 4 | .82 | .750 | .8243 | .1697 | .0000 |
| 16 | .32 | .075 | .3212 | .0064 | .0000 |
| 16 | .56 | .300 | .5528 | .0190 | .0008 |
| 16 | .82 | .575 | .8232 | .0431 | .0093 |

Interpretation: matching exposed-event share leaves pair density substantially higher for K=4 than K=16. That is a plausible and interpretable few-versus-many-regime contrast: approximately the same fraction of events is exposed, but those events are spread across fewer versus more independent shock sources. It must be ratified as the H4 estimand; pair density and membership distribution must still be reported.

The current design is predominantly one-regime-per-event. The multi-membership extension is rarely exercised under the matched candidate settings. The paper should call the primary structure regime-clustered event dependence, not imply that most event windows simultaneously overlap multiple regimes.

## Reproducible repository diagnostic

A helper has been added at scripts/mirun_event_density_diagnostic.py. It calls the same spawn_rngs and simulate_calendar_regimes functions as the integrated DGP and recreates the event-window mapping. It reports JSON and CSV outputs, MCSE across worlds, and optional matched-exposure calibration.

Example command:

    python -m scripts.mirun_event_density_diagnostic \
      --n 400 --T 260 --H 5 \
      --regimes 4 16 \
      --densities 0.25 0.50 0.75 \
      --reps 100 --seed-start 91000 \
      --calibrate-targets 0.32 0.56 0.82 \
      --out results/tables/mirun_event_density_audit.json

The test tests/test_mirun_event_density_diagnostic.py checks exact membership parity against build_world, boundary cases, multi-membership counting and invalid IDs.

## Gate 2 decision still required

The team should decide, before production results are examined:

1. Exposed-event share is the primary density axis and the matched quantity for H4.
2. Shared-regime pair density, exposure share, multi-membership share and membership-count distribution are all reported in each condition.
3. The proposed .32/.56/.82 exposure targets and K={4,16} calibration are approved, revised or rejected.
4. Numerical manipulation-check thresholds are set from the diagnostic's Monte Carlo uncertainty and the locked scientific objective, rather than chosen after examining DML coverage.
5. Volatility/shock and treatment/shock independence positive-control checks are rerun on the exact integrated DGP.

Until the team records these decisions and the integrated DGP passes the remaining checks, Gate 2 remains **NOT APPROVED**.
