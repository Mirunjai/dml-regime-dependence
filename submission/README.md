# Final research release build

The latest study is the separately registered 78-scenario / 43,200-block campaign
in `configs/experiments/final-validation/`. Its frozen source and raw archives are
not substituted for the older 3,200-block RF/overlap-CR0 exploratory evidence.
Read `docs/final_validation/FINAL_RESULTS_AND_TECHNICAL_REVIEW.md` for the final
user-delegated decisions, acceptance criteria, results and scope. The
[scope/submission crosswalk](../docs/final_validation/FINAL_SCOPE_AND_SUBMISSION_CROSSWALK.md)
separates the completed implementation from the remaining handoff items.

The current main Git checkout passes 439 tests in CI. The submission notebook has 48 explained
code stages and independently recomputes the full raw audit, actual DGP/fold/CR2
components, external-reference fixtures, daily labels, block bootstraps and CARs.
Source and input digests identify the exact matching clean-run receipt. Never
reuse an older notebook's PASS after rebuilding its source/bundle.

### Supported verification environments

Run the full pytest suite from a Git checkout. The standalone source ZIP has no
Git metadata, while six repository tests/tools resolve committed files with
`git show` or `git rev-parse`; those checks fail when invoked from that ZIP. This
is an archive-portability limitation, not evidence that six scientific tests
failed in CI. Do not claim the full suite passed from a ZIP. The notebook also
requires IPython and a Jupyter kernel (`ipykernel`); include both in any offline
reproduction environment file. The exact five-package requirements file
mentioned in the independent audit is not tracked in this repository, so its
pins still need to be reconciled with the final deliverables bundle.

## Scientific evidence

From the repository root, with the frozen cloud archives extracted to `core`
and `robustness` under `results/raw/final_research_20261112`:

```bash
python -m scripts.audit_final_campaign \
  --plan configs/experiments/final-validation/final_design_20261112.json \
  --run-dir results/raw/final_research_20261112/core \
  --run-dir results/raw/final_research_20261112/robustness \
  --source-root . --out results/raw/final_research_20261112/new_audit
python -m scripts.summarize_final_campaign \
  --plan configs/experiments/final-validation/final_design_20261112.json \
  --audit results/raw/final_research_20261112/new_audit/audit.json \
  --intervals results/raw/final_research_20261112/new_audit/intervals.csv \
  --structure results/raw/final_research_20261112/structure/structure.json \
  --out results/raw/final_research_20261112/new_interpretation
```

Audits use exclusive fresh output directories. Producer source fingerprints must
match their manifest. The notebook extracts the immutable producer archive as
its audit source root so a later repository edit cannot silently change it.
The raw source/price inputs stay local; the submission distributes derived daily
returns, regime indicators, configs, acquisition metadata and source hashes.

## Artifacts and clean execution

```bash
python submission/final_figures.py
python submission/build_final_research_notebook.py
python submission/build_final_research_documents.py
python submission/build_final_template_presentation.py
python submission/prepare_final_research_clean_run.py
```

Builders stage artifacts below
`results/raw/final_research_20261112/release_stage/ADA PROJECT DELIVERABLES`.
Run the actual notebook in a fresh local kernel and the private Kaggle clean-run
wrapper against its matching private dataset before installing the final package.
The wrapper never launches the 43,200-block campaign again. It checks the saved
raw campaign and re-executes selected actual components and real-data analyses.

The one-pager uses the supplied Word template. The 11-slide PowerPoint edits the
supplied course template, retaining the branding, master/layouts and theme, with
native editable tables, process diagram and charts/workbooks. The report uses
IEEEtran; compile its `.tex` with Tectonic or a compatible LaTeX distribution.
Render and inspect all final document pages/slides, and validate the PPTX against
its source template before packaging. A standalone bundle and exact SHA-256
manifest support offline reproduction.

The one-pager builder now uses the supplied team name, **Bullish Breakout**; no
course section was provided. The user delegated technical decisions and final
review; no teammate signatures or mentor approval are fabricated. Synthetic
Control and PPT editing are outside this final-file pass. The team is handling
the video; Drive sharing and Google Form submission still require the team.

The older builder scripts and `report_body.tex` remain historical build sources;
the `build_final_research_*` scripts and template presentation builder supersede
them for the current package.
