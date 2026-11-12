# Reviewed Week 4 integration — 12 November 2026

The user explicitly authorized merging the reviewed Week 4 work and executing the
previously named seven-branch cleanup. This integrates Deeptanshu's final-week
implementation and Mirun's additions from PR #14 (`5afe045`) and PR #15 (`5289a40`)
with the independent review corrections. It does not ratify Gate 2/3 or invent
team/mentor approval. Earlier source audits describe their pre-integration snapshot.

## Included source

- Shared-world fingerprints, complete-four-cell pairing and explicit partial-run
  accounting in the calendar engine, with identity/failure regression tests.
- Source-pinned structural grid, matched-exposure and independent-seed control
  diagnostics; fixes for control-path crashes, undefined correlations, invalid
  sigma clipping and membership-product overflow.
- Calibration raw-attempt/manifest retention, correct full-block contrasts and
  atomic checkpoints; separate GARCH parameterization comparison. The proposed
  larger calibration campaign itself is not claimed executed.
- Registered exploratory plan, independent raw-result verifier, real-data
  feasibility auditor and reproducible figure/table builders.
- Source for the narrated **38-code-cell / 40-Markdown-cell** notebook, Kaggle
  producer/collector/clean-run wrappers and final report/presentation build tools.
  Video rendering is not invoked by this integration.
- Source-grounded scope/decision records and navigation to the supplied Gate 1
  documents; actual team approval fields remain untouched.

## Validation

`python -m pytest -q -W error`: **427 passed** in the project environment. The
submission notebook's 38 code cells passed a fresh Kaggle CPU kernel, version 4,
with a matching producer environment and source digest
`4901fef5bf68c27fef2d7fb1b6e5152f94d43fa4d13afe84eb4379c42359f695`.
This is the recorded frozen notebook release; Git metadata/documentation changes
made while publishing the integration do not change its archived scientific code.

The source-pinned structural/control rerun completed 2,800 world builds, and the
frozen exploratory archive independently accounts for 3,200 complete worlds and
12,800 reference intervals, with zero failed/missing cells. These facts are not a
production gate pass. The independent-control miscalibration, unmatched H4,
missing historical original inputs and limited aligned daily support remain.
Synthetic Control is NOT EXECUTED under the supplied final-week Plan B.

## Data and release boundary

The sibling `ADA PROJECT DELIVERABLES` folder/ZIP, raw simulation/provider data,
credentials, caches and private generated Kaggle `.bin` input are excluded from
Git. Small diagnostic summaries and generator source are included. The local
release retains its own frozen checksums and execution record; publishing source
does not silently rebuild it. No Drive upload, sharing or form submission occurs.

## Approved cleanup

Deleted remote branches: `deeptanshu/session5-week3-review`,
`mirun/week2-closeout`, `mirun/week2-consolidated-completion`,
`mirun/session5-reconstructed`, `Sudarshan`, `preksha/regime-shock-module`,
`preksha/week2-validation`. The old local Session5 branch and clean checkout were
removed too. All tips matched the reviewed snapshot; the verified full-history
backup is local at `results/raw/project_scope_audit_20261112/pre_cleanup_all_branches.bundle`.

Retain `preksha/week3-benchmarks`: it preserves nine raw input/provenance files
intentionally absent from main. Retain both new Mirun source branches. The two
original PRs are superseded by this reviewed integration, with source attribution
retained; their experimental proposals remain subject to scientific gates.
