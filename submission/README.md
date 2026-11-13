# Final research release build

The latest study is the separately registered 78-scenario / 43,200-block campaign
in `configs/experiments/final-validation/`. Its frozen source and raw archives are
not substituted for the older 3,200-block RF/overlap-CR0 exploratory evidence.
Read `docs/final_validation/FINAL_RESULTS_AND_TECHNICAL_REVIEW.md` for the final
user-delegated decisions, acceptance criteria, results and scope.

The complete suite passes 439 tests. The submission notebook has 48 explained
code stages and independently recomputes the full raw audit, actual DGP/fold/CR2
components, external-reference fixtures, daily labels, block bootstraps and CARs.
Source and input digests identify the exact matching clean-run receipt. Never
reuse an older notebook's PASS after rebuilding its source/bundle.

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

Team name and sections intentionally remain blank. The user delegated the
technical decisions and final review; no fabricated teammate signatures or
mentor approval are needed. Synthetic Control, new video production, Drive
sharing and Google Form submission are excluded by instruction. Existing video
material is backed up, not re-rendered or presented as a new final video.

The older builder scripts and `report_body.tex` remain historical build sources;
the `build_final_research_*` scripts and template presentation builder supersede
them for the current package.
