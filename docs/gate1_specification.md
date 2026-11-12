# Gate 1 specification and source map

This is a navigation summary of the supplied locked proposal, not a new team approval.
The authoritative local sources are `../Project_A_One_Page_Proposal.docx` and
`../Project_A_Research_Idea_and_Methodology.docx` (relative to the repository root).
Their SHA-256 fingerprints are recorded in the final scope audit source index.

The primary question is whether dependence-robust variance alone restores DML
95% interval calibration under regime common shocks, or whether regime-aware
cross-fitting adds inferential benefit. The comparison is random/grouped folds
crossed with naive/robust variance; random robust versus grouped robust is central.

- H1: increasing independently measured dependence may worsen naive calibration.
- H2: robust variance may improve calibration with folds fixed.
- H3: grouped folds may add benefit with robust variance fixed; no added benefit
  is an admissible outcome, not equivalence without appropriate evidence.
- H4: compare few versus many regimes at a defined, matched dependence quantity.

Coverage is primary; null size is the key diagnostic. Width, nonnull power,
bias/RMSE and fold sensitivity are secondary. Classical and Synthetic Control
benchmarks are contextual. Real S&P inclusion data supply qualitative evidence,
not known-truth coverage. No estimator, variance formula or theorem is claimed.
Numerical settings and manipulation thresholds require later design decisions.

The final-week v3 handout explicitly permits an exploratory Plan B submission and
closes Synthetic Control. Current completion and departures from the older,
broader proposals are recorded in
[the scope audit](final_review/PROJECT_SCOPE_AUDIT_20261112.md).
