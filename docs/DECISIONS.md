# Decisions and proposals

31 October 2026: the user approved the proposed approach and explicitly requested
implementation of Deeptanshu's Week 1 and Week 2 work. P1-P4 now describe that
authorized implementation. This is not team approval of a final simulation grid,
manipulation-check thresholds, or Gate 2/Gate 3. Gate 1 remains locked.

## P1: Standalone GARCH contract and coefficient mapping

No existing Week 1 volatility artifact was found in the available refs. Implemented:

```python
simulate_volatility(
    n_firms, n_periods, persistence, rng,
    *, unconditional_variance=1.0, arch_share=0.1, burn_in=1000,
) -> (sigma, eps)
```

This is the implemented interface (the sketch above omits type annotations).
The numerical defaults are diagnostic settings, not a Gate 2/3 grid. Simulation
uses NumPy; tests use pytest and plots use Matplotlib. Dependencies are constrained
in requirements files; the tested local versions are recorded with each run.

All returned arrays have shape `(n_firms, n_periods)`. `sigma` is conditional
standard deviation in return units; `eps` is standardized iid N(0,1) innovation.
Idiosyncratic returns are `e = sigma * eps`, and conditional variance is `h = sigma**2`.
Varying regime settings must not change these arrays for the same volatility seed.

With rho = persistence and a = arch_share, propose alpha = a*rho,
beta = (1-a)*rho, and omega = v*(1-rho), where v is intended unconditional variance.
Then h[i,t] = omega + alpha*e[i,t-1]^2 + beta*h[i,t-1]. Require finite v>0,
0<=rho<1, 0<a<=1, positive integer dimensions, nonnegative integer burn-in, and
an explicit NumPy Generator. Reject booleans as dimensions. Start h[i,0]=v, draw
the initial innovation, simulate burn-in, and discard it; this initialization
matches the mean variance but does not sample the stationary distribution of h.

Why this mapping: it supports rho=0 and a controlled coefficient ratio across a
persistence sweep. An alternative fixed alpha with beta=rho-alpha preserves the
shock coefficient but restricts rho>=alpha. The proposed ratio changes shock
responsiveness and higher moments as rho changes: it is a parameterized GARCH
family, not an intervention changing only serial decay. Record both coefficients
and resulting moment conditions, and discuss this trade-off before approval.

Bollerslev (1986), Sections 2-4, gives finite unconditional variance v=omega/(1-alpha-beta)
when alpha+beta<1 under the stated model. For Gaussian innovations, a finite fourth
moment additionally requires 3*alpha^2+2*alpha*beta+beta^2<1. Squared-return ACF
interpretation requires that stronger condition. Under this mapping the expression
is rho^2*(1+2*a^2). Do not silently accept diagnostic settings outside it or conflate
wide-sense stationarity with the separate strict-stationarity question.

Numerical re-audit: form the intercept from the resolved coefficients as
v*fsum(1,-alpha,-beta), algebraically the same fixed-variance rule. Near the unit
boundary, the ordinary subtraction and rounded moment factor can lose decisive
digits. Moment/ACF calculations now use gap=fsum(1,-alpha,-beta) and the stable
fourth-moment margin gap*(2-gap)-2*alpha^2. Its sign determines finiteness; the
displayed factor may round to one. High-precision Decimal regression checks
verify the coefficient-based variance identity and ACF in these edge cases.
This changes numerical evaluation, not the approved DGP or diagnostic grid.

Validation after approval: exact recurrence on a tiny path; parameter boundaries;
replay, shape, finite positive variance; low/high persistence squared-return ACFs;
independent-run estimates of mean h and mean e^2 relative to v; a longer-burn-in
sensitivity check; record maxima, quantiles, NaNs, infinities, and negative/zero h.
Finite-sample ACFs need not be monotone in every seed. Use repeated simulations,
not a fitted persistence estimate from one short path, as supporting evidence.
Never clip or rescale problematic paths to pass checks. Flag numerical failures
immediately; numerical tolerances and extreme-return thresholds need justification.

Official implementation inspected: [`arch.univariate.GARCH.simulate`](https://bashtage.github.io/arch/univariate/generated/generated/arch.univariate.GARCH.simulate.html)
accepts coefficients, a callable innovation RNG, burn-in, and initial variance;
it returns returns and variance rather than our proposed sigma and standardized eps.
Source: `arch/univariate/volatility.py`, tests: `arch/tests/univariate/test_volatility.py`.
Its different output contract warrants an explicit adapter if later used for a
reference comparison. Prefer our small NumPy panel recursion with deterministic
recurrence tests; `arch` can be an optional reference check after approval. No code
has been copied; any adaptation must preserve its NCSA notices. Fitting GARCH is
not required for the first simulation milestone.

## P2: Independence validation with a meaningful positive control

Use separately spawned, recorded RNG streams for volatility and regime generation.
Audit inputs and call structure in addition to examining diagnostics. Use the
merged, team-frozen regime module once identified; currently only unmerged branches
are available. Do not merge a teammate's branch just to make the check runnable.

After Mirun resolves the time/event mapping, examine associations of h and h's
lagged values with exposure indicators and shock magnitude U^2, alongside signed U.
Use replicated independent panels as the uncertainty unit; do not treat tiled
shocks across firms or shared-regime windows as iid observations. Constant inputs
(e.g. zero exposure) must yield an explicit undefined/not-applicable diagnostic,
not an invented zero correlation or pass.

For a validation-only positive control, deliberately contaminate the otherwise
independent conditional-variance array with a positive factor increasing with U^2.
This is an intentionally invalid construction, not a candidate DGP. Require the
diagnostic to distinguish this control across independent runs. Zero signed
correlation can coexist with this magnitude dependence. Calibrate false-positive
behavior and control detection before proposing thresholds; no universal correlation
cutoff or ordinary iid Pearson p-value is justified here. Failure to reject is
not proof of independence. Construction and diagnostic evidence complement each other.

## P3: Standalone coverage, size, and Monte Carlo uncertainty

Propose `src/evaluation/metrics.py` consuming 1-D interval bounds and scalar known
truth, with no DML/runner imports. Coverage indicator is `lower <= truth <= upper`
(closed endpoints). Null rejection is `upper < 0 or lower > 0`; report empirical
size only when truth is zero. For nonzero truth, the same rejection frequency is
power. Require finite bounds, lower<=upper, matching nonempty arrays and finite
truth. A zero-width finite interval is valid. Malformed arrays raise errors.

Propose an explicit status per attempted replication for numerical/estimator
failures. Strict mode errors on failed/missing rows; an explicit reporting mode
returns attempted, valid, and failed counts plus conditional-on-success metrics.
Never silently drop failures or interpret them as null rejections. Also report
coverage bounds [covered/attempted, (covered+failed)/attempted] when needed to show
the possible impact of missing intervals. Final failure policy requires team lock.

For R valid independent replications and proportion p_hat, use plug-in
MCSE=sqrt(p_hat*(1-p_hat)/R). Report that MCSE=0 at p_hat=0 or 1 is a boundary
artifact, not certainty; a binomial uncertainty interval can accompany it. For
paired cell comparisons on the same simulated panels, align replication IDs,
use d_r=I_A,r-I_B,r, and MCSE(mean(d))=sd(d, ddof=1)/sqrt(R_pairs), requiring at
least two valid pairs. Report pair counts/failures; never use an unpaired formula
or silently compare different successful subsets.

Tests should include exactly 95 covered of 100, exactly five null rejections,
endpoint inclusion, nonzero-truth size rejection, empty/malformed/reversed/nonfinite
inputs, explicit failed rows, and paired examples with hand-computed variance.
Mock results validate arithmetic, not estimator coverage.

Budget proposal: choose an MCSE target and estimate runtime before the design lock.
At expected coverage .95 or null size .05, R >= .0475/s^2; target s=.005 gives
1,900 independent replications. A conservative bound valid for any proportion
uses .25/s^2, giving 10,000. These are planning calculations, not executed results
or approved budgets. Paired comparisons require their own precision assessment.
Use a pipeline/runtime pilot without adapting hypotheses or criteria to its results.
Define a practical coverage/size difference before results; Monte Carlo precision
alone does not define materiality. Closeness to .95 and size near .05 matter;
simply increasing coverage can produce overcoverage. Manipulation checks remain
independent of DML outcomes.

This proposal follows [Morris, White and Crowther (2019), Statistics in Medicine
38, 2074-2102, doi:10.1002/sim.8086](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/)
on planning simulations and reporting Monte Carlo error and failures. Our paired
binary-difference formula follows the sample-mean variance calculation.

## P4: Minimal files and approval questions

Reuse `configs/dgp/week1_skeleton.yaml` as provisional context; do not lock numbers
there. Proposed implementation files only when approved:

- `src/dgp/volatility.py` and `tests/test_volatility.py`;
- `src/dgp/validate_volatility.py` for standalone diagnostics/plots, with an
  optional frozen-regime check once the mapping and version are agreed;
- `src/evaluation/metrics.py` and `tests/test_metrics.py`;
- small reproducible summaries in `results/tables/` and `results/figures/`, with
  raw output excluded after the ignore-file issue is resolved.

Keep protocol discussion here and progress in `PROJECT_STATE.md`; avoid another
overlapping tracker. Runtime/fold review is STRETCH. No full experiment runner,
DML estimator, benchmark implementation, or final grid is part of this proposal.

Local implementation approval resolved (1) a fresh P1 and (2) the coefficient
mapping/initialization. P3 failure semantics are implemented as engineering
behavior, with final reporting policy still a team decision. The unmerged regime
source is pinned for a diagnostic-index test only. A team-frozen version and the
integrated event-window/time mapping remain unresolved.

## P5: Monte Carlo protocol draft for the team design lock

Status: proposed, not locked. Do not change criteria after examining DML results.
The current component runs contain no DML intervals and are not the final pilot.

### Units, pairing, and records

- One replication is an independently generated complete panel/event dataset.
  Firms and overlapping/shared-regime windows inside it are not replications.
- Use the same panel/known effect for all four DML cells; preserve replication ID,
  component seeds/spawn keys, folds, config, source version, estimate, interval
  bounds, cell label, status, and failure reason. Zero- and nonzero-effect
  conditions are separate. Truth is evaluation metadata, never a nuisance input.
- Materialize every planned run as a row, including failures. The metrics API's
  `expected_replications` guards against omitted rows. For paired metrics include
  the complete planned ID set in both mappings, using None for failed runs.
- Strict failure handling is the proposed primary reporting policy: diagnose
  missing/failed runs before interpreting calibration. Explicit report mode gives
  conditional-on-success metrics, denominators, and all-attempted coverage bounds;
  these must never be presented as unconditional coverage. Define any recovery or
  fallback estimator before the main experiment; it changes the method evaluated.

### Replication budget and runtime

Choose R per DGP setting and effect condition, not separately per DML cell. With
anticipated coverage .95 or size .05, approximate marginal MCSEs are:

| R | Expected MCSE (percentage points) |
| --- | --- |
| 1,000 | 0.689 |
| 1,900 | 0.500 |
| 5,000 | 0.308 |
| 7,600 | 0.250 |
| 10,000 | 0.218 |

Recommend targeting at most 0.5 percentage points marginal MCSE as an initial
budget proposal, with 0.25 points preferred if full-pipeline runtime permits.
The conservative any-proportion budget for 0.5 points is 10,000. These values
do not guarantee the same precision for paired differences: use sample SD of the
paired indicators divided by sqrt(R), and report it. A worst-case paired binary
difference has variance at most 1, so an SE bound of .005 can require 40,000 pairs.
Do not substitute an independence formula for paired uncertainty.

Mirun's complete DML runtime determines feasibility. Our GARCH-only timing is
not an end-to-end estimate. Pre-specify a small pipeline/runtime pilot, choose
the budget/grid once with the team, then freeze them. If precision is inadequate,
report an inconclusive comparison; do not redefine materiality to obtain a finding.

### Proposed materiality and benefit rule

Propose a practical difference of **1 percentage point** in calibration loss for
team discussion. Define coverage loss as abs(coverage-.95) and null-size loss as
abs(size-.05); a larger coverage rate is not automatically an improvement.
The primary comparison remains random+robust versus grouped+robust. Report all
four cells and paired contrasts to separate folds from variance correction.

To claim additional benefit, propose that grouped+robust reduces coverage loss
by more than the agreed practical threshold, with Monte Carlo uncertainty that
supports the reduction, and does not materially worsen null size. Width/power
alone cannot establish benefit. Report coverage/size differences and paired SEs.
For uncertainty in the *difference of absolute losses*, propose projecting
simultaneous Monte Carlo intervals through the absolute-value function. For the
two robust cells' coverage/size proportions, four exact binomial intervals at
98.75% each give at least 95% simultaneous Monte Carlo coverage by Bonferroni
under independent complete replications. For a rate interval [l,u] and nominal t,
its loss is bounded below by 0 if t is inside [l,u], otherwise min(abs(l-t),abs(u-t));
the upper loss bound is max(abs(l-t),abs(u-t)). Subtract the resulting loss bounds
to bound the coverage-loss improvement and the possible size-loss worsening.
Recommend requiring the improvement's lower bound above the agreed practical
threshold and the worsening's upper bound below it before claiming benefit.
These bounds are conservative and remain valid with paired/correlated cell
outcomes; signed paired contrasts and SEs should also be reported for precision.

This future analysis rule is not implemented by the current descriptive Wilson
95% utility. It must be approved before the final DML run. It replaces an initial
bootstrap suggestion during protocol review: the absolute-loss kink means an
ordinary bootstrap or a simple signed-rate SE cannot automatically be justified.
Do not claim equivalence from nonsignificance. Pre-specify whether comparisons
across grid settings are descriptive or require wider simultaneous adjustment;
no across-grid superiority claim is approved.

### Proposed component checks and their limits

These proposals were drafted after the first diagnostic run. They cannot be
retroactively called pre-specified acceptance criteria for that run. A fresh-seed
corroboration config (`deeptanshu_corroboration.json`, seed 20261101) is recorded
before its execution; its engineering checks below are not a team gate decision.

- Hard numerical checks: no NaN/inf/nonpositive h in the regular validation grid;
  exact coefficient identity for intended variance within float64 tolerance;
  deterministic replay and exact isolation when only regime streams change.
- Proposed empirical-variance review flag: absolute relative error exceeding
  max(2%, three panel-level MCSEs divided by intended variance). This is a review
  flag, not proof of stationarity or a universal financial calibration rule.
- Interpret squared-return ACF only with finite fourth moments. Inspect low/high
  persistence and increasing series lengths. Do not require every finite-length
  sample ACF to hit its population value or every lag to be monotone in every seed.
- The 12-unconditional-SD return threshold logs potential pathologies; it is not
  an exclusion or a rejection rule. GARCH is heavy-tailed even with Gaussian eps.
  Preserve the counts and coordinates/values (capped at 100 examples per panel,
  with a truncation flag), and investigate them without clipping/rescaling.
- Conditional randomization uses the complete known regime generator, six
  max-calibrated association diagnostics, B=199 draws, alpha=.05. The control
  multiplies h by 1+U²/mean(U²); it is deliberately invalid and never enters the DGP.
  Across 100 independent panels, propose reviewing a false-detection Wilson upper
  bound above .15 or a control-detection Wilson lower bound below .90. Report the
  full rates/intervals regardless. Passing this weak screening standard is not
  proof of independence; input/RNG audit remains essential.
- Preksha owns realized-dependence manipulation checks and matching density across
  regime counts. No threshold for her component, robust-variance choice, grouping
  unit, or final grid has been silently selected by this implementation.

### Data interface for independent metric recomputation

`python -m src.evaluation.metrics --input raw.csv --truth 0 --cell random_robust
--expected-replications 1900` reads lower/upper bounds, optionally cell,
replication, truth, and success=true/false **or** status=ok/failed. Multi-cell files
need explicit cell selection; duplicate IDs, conflicting truth, malformed CSV,
and invalid successful intervals raise. Blank failed bounds are allowed only
with explicit failed status. Other runners can call the array API directly;
this small adapter does not impose an infrastructure format on teammates.

## Reference corrections and limits

The methodology's multiway DML citation omits Yukun Ma: the author list is
Harold D. Chiang, Kengo Kato, Yukun Ma, Yuya Sasaki,
[Multiway Cluster Robust Double/Debiased Machine Learning](https://arxiv.org/abs/1909.03489).
Its multiway sampling assumptions do not automatically select a valid robust
variance for this DGP; that remains Mirun's Gate 3 responsibility.

[Balkus, Laith and Hejazi, arXiv:2601.10899](https://arxiv.org/abs/2601.10899)
addresses cross-fitting with correlated units under rate/dependence assumptions.
It must not be treated as a blanket dense-regime coverage guarantee. Neither a
new novelty claim nor a full audit of every roadmap reference was attempted here.
