# Review of Mirun's Week 2 integration

4 November 2026. Original code: `26e65f1`; completion pack: `a84b548`;
merged through PR #5 at main `1b914cd`. This review is a follow-up hardening
change, not a second merge of the same branch or a scientific gate approval.

## Effect on the existing components

The diff from the previous main `6c5ff70` changes no file under `src/dgp`,
`src/evaluation`, or `src/infra`. The only pre-existing file changed by Mirun's
code commit was `.gitignore`, with additional backup/archive exclusions. Our
GARCH, validation/positive controls, coverage/size metrics and mock runner are
preserved byte for byte.

There is nevertheless a material *integration difference*: the research DGP
implements another GARCH family. Its alpha is fixed at .10 and its burn-in is 500
(200 in the archived original). The canonical default uses alpha=.1*rho and
burn-in 1000; at rho=.90, alpha is .09. Innovation draw order also differs.
Both retain firm-own innovations and intended unconditional variance, but their
paths, fourth moments and persistence sweeps must not be pooled as one validated
process. The fixed-alpha family is retained and explicitly labelled for replay;
this review does not silently substitute either scientific model for the other.

The calendar-time regime process is also a separate model from Preksha's merged
event-index generator. The decision about the primary scientific DGP is open.

## Findings and corrections

| Finding | Correction / disposition |
| --- | --- |
| A failed overlap-sandwich variance raised before returning a valid naive interval | Keep the common point estimate; fail only the affected variance cell |
| An impossible grouped split discarded already-computed random-fold results | Materialize four cell records per replication, preserving successful cells and each failure reason |
| The active runner saved aggregate summaries but no replication-level archive | Persist every raw attempt while running, with config, seed addresses, estimator settings, folds and numeric screens |
| Summaries used only successful runs without per-cell denominators and bounds | Report attempted/valid/failed counts, conditional status, all-attempted coverage bounds and Wilson intervals; undefined metrics stay null |
| Regime IDs such as 1.5 or True were silently coerced to integers | Validate membership IDs before forming groups or the covariance relation |
| Positive-control strings such as "False" activated the control | Require actual boolean switches and finite non-boolean numerical parameters |
| Subset enumeration required 2^K work when an event touched K regimes | Use the algebraically identical sum of diagonals and pairs sharing any regime; a 60-membership regression finishes directly |
| Gate 2 diagnostics ignored the Monte Carlo CLI's dimensions and seed settings | Pass and save the actual diagnostic configuration/seeds; undefined correlations remain null |
| Default execution could overwrite committed summary outputs | Use new ignored run directories with exclusive creation and incremental atomic raw writes |
| A standard fresh development install omitted the new SciPy/sklearn dependencies | Include the research runtime requirements in the development installation; pytest is controlled by requirements-dev |

The old exponential subset-count metadata is no longer computed: its deprecated
field is null, and `n_dependency_pairs` records the directly counted shared pairs.
The covariance *formula* is unchanged. Negative/nonfinite meat still fails; it
is never clipped or projected to a positive number.

Point estimates that survive an inference failure remain in raw records. Summary
bias/RMSE based on successful intervals are labelled conditional; separate counts
and bias over all available point estimates expose the different denominator.

## Scientific issues retained for the team

1. **Regime-only grouping is not automatically all-source grouping.** A shared
   calendar factor may connect windows assigned to different regime-pure folds.
   Fold diagnostics now count regime-sharing and calendar-factor-sharing pairs
   crossing folds separately. These are potential-dependence relations, not
   significance tests or a theorem that every resulting interval is invalid.
2. **Regime-only covariance is a proposal.** Full-membership overlap adjacency is
   not automatically the standard multi-dimensional clustering construction; its
   matrix need not be positive semidefinite. Small-regime calibration is unsolved.
3. **The archived 'baseline_no_dependence' keeps sd_factor=.5.** It removes regime
   shocks and treatment clustering, not every shared source. A genuinely absent
   calendar factor needs an explicitly declared sd_factor=0 condition. Historical
   source/results are retained; their label is not proof of an iid baseline.
4. **Gamma, factor and membership variants differ.** The first-regime CR1 results
   under `week2_mirun` and full-membership sandwich results under
   `week2_completion` are distinct estimators and must not be pooled. Factor-OFF
   changes outcome variance as well as a dependence source. No variant was chosen
   for its observed coverage.
5. **Gate 2/3 remain open.** The completion pack is a proposal. Its suggested 3pp
   rule and budget do not supersede the earlier P5 proposal without team agreement.
   No approved robustness subset or labelled daily-return dataset is available.

## Verification evidence

Before review changes, the branch passed 171 tests with warnings treated as errors
locally. New regression cases first reproduced the failure/isolation/type issues;
they now pass. The full reviewed suite passed **187 tests with warnings as
errors** after a clean requirements-dev installation: Python 3.13.13, NumPy
2.5.4, SciPy 1.18.1, scikit-learn 1.9.1 and pytest 9.2.0. There are 16 new
regression cases beyond the original 171. Historical replay uses the separately
recorded NumPy 2.3.5/SciPy 1.16.3/sklearn 1.7.2 environment; versions are not
silently mixed when comparing generated estimates.

The original consolidated 20-replication pilot was independently replayed from an
immutable source archive, for all gamma=0/1 and tau=1/0 conditions. It generated
320 per-cell rows across 80 independent simulated panels/conditions. All 16
reported cell summaries matched: coverage exactly, bias and width within about
3.1e-16 absolute floating-point difference. The reconstructed raw rows and source
archive are retained under ignored `results/raw/mirun_original_review_26e65f1/`.
This is a reviewer reconstruction, not a claim that the original raw archive was
provided. Larger archived ablations are audited separately in the Week 3 package.

Small replication counts and matching aggregates do not establish nominal
calibration or the H1–H4 conclusions. The numerical verification and the scientific
interpretation/approval are separate deliverables.

## References

- [Chernozhukov et al., Double/Debiased Machine Learning](https://arxiv.org/abs/1608.00060):
  orthogonal scores and cross-fitting; implementation agreement alone does not
  establish the sampling assumptions of a dependent-data application.
- [Cameron, Gelbach and Miller, multi-way clustering](https://cameron.econ.ucdavis.edu/research/multiway06.html):
  distinguishes the standard nonnested multi-dimensional problem from silently
  assigning an arbitrary overlap graph the same guarantees.
