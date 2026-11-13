"""Document, validate and atomically install the final local submission package.

--prepare writes the handoff/dataset docs before the notebook source freeze.
--install requires a matching fresh cloud receipt and preserves the old folder.
No Git publication, video rendering, Drive action or form submission occurs.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/raw/final_research_20261112'
STAGE=BASE/'release_stage/ADA PROJECT DELIVERABLES';AUDIT=STAGE/'07_Audit_and_Reproducibility'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare():
    templates=BASE/'artifact_templates';templates.mkdir(exist_ok=True)
    supplied={'DefaultCourseProject_OnePager.docx':Path('/home/deeptanshukumar/Downloads/DefaultCourseProject_OnePager.docx'),
              'AFML-ppt-template.pptx':Path('/home/deeptanshukumar/Downloads/AFML-ppt-template.pptx'),
              'IEEEtran.cls':ROOT.parent/'ADA PROJECT DELIVERABLES/06_IEEE_Report/IEEEtran.cls'}
    for name,source in supplied.items():
        if not (templates/name).exists():shutil.copy2(source,templates/name)
    (AUDIT/'templates').mkdir(parents=True,exist_ok=True)
    for p in templates.iterdir():shutil.copy2(p,AUDIT/'templates'/p.name)
    (AUDIT/'template_sources.json').write_text(json.dumps({p.name:sha(p) for p in templates.iterdir()},indent=2)+'\n')
    (STAGE/'README_START_HERE.md').write_text('''# ADA Project A: final submission package

Team name: ____________________

Section(s): ____________________

This package contains the completed, user-delegated technical work for the
registered final study. It uses established DML/CR2 methods and reports the
actual finite-grid findings, including the absence of additional material
grouping benefit in the two prespecified focal conditions.

| Course item | File/folder |
|---|---|
| Final one-pager | `01_One_Pager/ADA_Final_One_Pager.docx` and matching PDF |
| Code notebook | `02_Code/ADA_Project_Final.ipynb` (executed, 48 code stages) |
| Dataset | `03_Dataset/` (raw simulation archives and derived daily data) |
| Project PPT | `04_Presentation/ADA_Project_Final.pptx` and matching PDF |
| Video | Team will record separately; no new rendering performed |
| IEEE report | `06_IEEE_Report/ADA_IEEE_Report.pdf` and editable LaTeX source |
| Verification | `07_Audit_and_Reproducibility/` |

The final campaign has 78 scenarios, 43,200 complete four-cell blocks and
172,800 primary intervals. All 24 independent-control cells pass the registered
calibration/bias criteria. The full software suite passes 439 tests. Independent
raw, R-reference and fresh-process replay checks accompany the evidence.

The daily panel has six firms, 1,511 common trading dates and 9,066 valid returns.
Prior-only labels and joint calendar-block uncertainty support descriptive
dependence figures. Seven fresh classical event cases are a separate sample;
there is no requirement that the common daily panel contain seven firms.

To reproduce offline, keep the folder layout, open the notebook and Run All.
The notebook locates `../03_Dataset/source/notebook_bundle.zip` and verifies
its exact SHA-256. On Kaggle attach the matching private research bundle instead.
The clean-run receipt identifies the source/bundle that actually executed.
The full 43,200-block campaign is audited from its raw records rather than
silently rerun in the notebook. Selected actual components and the real-data
analyses are re-executed. No internet or GPU is needed for this reproduction.

Fill team name and sections before submission. The team handles the 3–5-minute
video, Drive folder/sharing and Google Form. Synthetic Control is excluded.
The technical review is complete on the user's delegated authority; no teammate
signatures or mentor approval are fabricated. See `RESEARCH_BOUNDARIES_AND_FIXES.txt`
for research extensions and the original-input authentication boundary.
''')
    (STAGE/'RESEARCH_BOUNDARIES_AND_FIXES.txt').write_text('''RESEARCH BOUNDARIES AND POSSIBLE EXTENSIONS

These do not hide failed or unexecuted results inside the submitted conclusions.
Material limits are also stated in the report, notebook and scope slide.

1. FEW-REGIME CALIBRATION. In the registered focal K=4 condition, CR2 coverage
   is 91.2% random / 90.6% grouped, below 95%. Controls pass, but the correction
   does not universally restore nominal dependent-sample coverage. A separate
   future study could investigate score-level finite-cluster theory or alternative
   inference on new prospective seeds. Do not choose a post-hoc winner here.
2. GROUPING BENEFIT. Neither focal comparison meets the prespecified material
   benefit rule. This is a legitimate completed result, not equivalence or proof
   grouping can never help. Avoid a superiority claim in the presentation.
3. H4 MATCHES. Pair probability and exposure are separate matching quantities.
   Neither equalizes shock-loading strengths, marginal variance or full covariance.
   A fully covariance-matched extension would need a new registered design.
4. GENERALIZATION. One DGP family and six selected firms do not establish a
   universal finance-market or causal result. The common 2016–2021 window provides
   adequate aligned data for this descriptive analysis, so the older calm-support
   shortage is resolved. Six vs seven is not an automatic validity criterion.
5. MARKET RESIDUALS. The raw correlation contrast attenuates strongly after
   prior market adjustment; the residual interval crosses zero. Report both.
   The residual sample has 491 turbulent dates vs 510 raw dates due to ETSY's
   limited prior fitting history. The bootstrap treats the derived label sequence
   as given and does not model label-estimation uncertainty.
6. ORIGINAL HISTORICAL INPUTS. An 84-ZIP/Git search did not recover the original
   combined-price file or missing original replication archives. A verified ADS/BFH
   crosswalk and close fresh numbers cannot authenticate the missing bytes or
   original adjustment vintage. Final claims use the fresh saved evidence.
7. PROVIDER VINTAGE. Fresh adjusted prices reflect the acquisition snapshot,
   not a guaranteed point-in-time historical adjustment vintage. Missing holiday
   VIX rows were calendar-verified and excluded; no trading-day value was filled.
8. CALENDAR FACTORS. Primary component CR2 assumes independent regime components.
   Factor-on stress adds dependence outside that covariance scope. Its observed
   finite-grid coverage is not a theorem validating arbitrary common factors.
9. ENGINEERING WARNING. The 439-test run reports seven Python 3.13 warnings about
   forking a multithreaded test process. Tests pass; the record does not falsely
   claim warnings-as-errors success. A future runner-only change can adopt spawn
   after preserving the frozen producer/source evidence and rerunning its checks.
10. PAPER EXTENSION. A course-ready empirical result is not automatic journal
    acceptance. A paper would need a stronger positioning/novelty argument,
    independent peer feedback and broader evidence for the intended claims.

INTENTIONAL TEAM HANDOFF: team name/sections, video recording and Drive/Form.
EXCLUDED: Synthetic Control. No donor or synthetic treatment effects fabricated.
''')
    (STAGE/'03_Dataset/README.md').write_text('''# Dataset and evidence inventory

`simulation/core.zip` contains 28,000 scenario-replication records across 38
conditions. `simulation/robustness.zip` contains 15,200 across 40. Each archive
has its full manifest, completion file and checksums. Four primary cells share
the same world/config/seed per block; legacy reference cells are separately
labelled. These are 43,200 scenario-replication blocks, not 43,200 mutually
independent conditions pooled across reused seeds.

`derived_daily_panel/aligned_returns.csv`: 1,511 common XNYS dates (2016-01-04
through 2021-12-31), six firms CRM/FAST/MHK/SWKS/ETSY/TER, fractional adjusted-close
simple returns and one common prior-only regime label. There are no missing panel
returns. The calendar is explicit; missing source sessions are not bridged.

`daily_labels_and_thresholds.csv`: strictly prior 20-observation VIX mean,
earlier rolling-mean quartiles within a five-calendar-year history, and calm /
mixed / turbulent label. Equality is mixed. Counts are 332 / 669 / 510.
`derived_vix20_history.csv` supplies rolling mean windows to independently
regenerate every threshold/label without distributing provider price histories.

`derived_returns_full.csv`: six stock returns and SPY/^GSPC market returns over
the wider acquisition window, preserving initial/missing observations.
`prior_market_residuals.csv`: residuals of each stock after a 252-session,
minimum-200 strictly earlier paired OLS fit against ^GSPC. Initial ETSY fitting
history yields 491 valid turbulent dates; calm count remains 332.

`reacquired_event_returns.csv` additionally contains ADS under the SEC-verified
BFH issuer crosswalk. Fresh classical CAR/model output and the 42-field comparison
with legacy printed values are supplied. These seven event cases are distinct
from the six-firm common panel and the original eight-event candidate roster.
CTLT remains an unfilled original missing-data case.

`configs/` contains the frozen design, analysis addendum, development design and
panel/uncertainty conventions. `tables/` contains all-grid metrics and canonical
facts. `figures/` contains publication figures and underlying data are in CSV/JSON.
`source/` contains the immutable producer snapshot, current project source and
self-contained notebook bundle. Original source/provider metadata, timestamps,
byte hashes, external-reference and independent-audit records are in
`../07_Audit_and_Reproducibility/`.

Acquisition uses yfinance/Yahoo Finance with explicit adjusted-close options,
and ^VIX for volatility labels. ADS/BFH identity source:
https://www.sec.gov/Archives/edgar/data/1101215/000110121522000058/form_8-k.htm .
Provider price-level histories are not redistributed. Derived returns, indicator
windows and frozen raw synthetic records support offline notebook reproduction.
No secret token is required for the packaged analysis. The acquisition scripts
are optional online provenance/reacquisition tools, not an offline dependency.
''')
    (STAGE/'03_Dataset/DATA_DICTIONARY.md').write_text('''# Data dictionary

| Field | Meaning / units |
|---|---|
| date | ISO-8601 common exchange-session date |
| CRM, FAST, MHK, SWKS, ETSY, TER | Fractional adjacent-session adjusted-close simple return |
| ^GSPC / SPY | Fractional market-index / ETF return, kept distinct |
| ADS | Fresh BFH-symbol adjusted return for the historical ADS issuer |
| regime_label | calm, mixed or turbulent from strictly earlier VIX observations |
| pre_event_vix20 | Strictly prior 20-observation VIX mean, VIX index points |
| vix_p25, vix_p75 | Quartiles of earlier rolling means in trailing five calendar years |
| window_first_date / vix20 | First included observation date and derived 20-observation mean ending on date |
| prior_market_residuals firm columns | Fractional return minus prediction from strictly earlier OLS |
| aligned_sessions | Complete paired dates in the stated label, not a pooled firm count |
| pearson / spearman | Descriptive same-date correlation / rank correlation |
| car_primary / car_short / car_wide | Sum of abnormal fractional returns in [-1,1] / [0,1] / [-5,5] |
| scenario / replication / seed | Frozen condition identity, within-condition integer ID and root RNG entropy |
| world_sha256 / block_id | Exact scientific-world bytes hash / shared four-cell identity |
| estimate / lower / upper / se | Scalar simulated treatment-effect estimate, interval bounds and SE |
| truth | Evaluation-only known τ, excluded from nuisance fitting inputs |
| df / critical | CR2 Satterthwaite degrees of freedom / t critical value |
| status / error | ok or failed, with explicit retained failure reason |
| coverage95 / empirical_size / power | Known-truth interval hit / null rejection / nonnull rejection rate |
| valid / failed / missing / planned | Explicit per-cell denominators; never silently drop failures |
| coverage_mcse / Wilson intervals | Monte Carlo uncertainty of a coverage rate |

Dates/labels are shared across firm vectors. Joint calendar blocks preserve the
contemporaneous dependence. No independent-pair IID p-value or causal regime
effect is reported. Dataset counts, missingness and definitions differ by table;
do not substitute the seven-event sample for the common daily panel.
''')
    (STAGE/'02_Code/README.md').write_text('''# Executable code

Open `ADA_Project_Final.ipynb` and Run All, keeping the sibling dataset folder.
It authenticates its bundle, audits every primary interval and re-executes real
components/analyses in 48 explained stages. CPU only; no internet needed.
Python 3.13 with NumPy, SciPy, scikit-learn, pandas and Matplotlib is recorded in
the matching clean-run receipt. The original campaign used NumPy 2.1.3,
SciPy 1.16.3 and scikit-learn 1.6.1; a newer local runtime also passed.
The full campaign is not silently launched by Run All. Source/configs and
re-execution commands are included in the project-source snapshot.
''')
    (STAGE/'04_Presentation/README.md').write_text('''# Final course-template deck

Use `ADA_Project_Final.pptx` for presenting and editing, and the matching PDF
for a portable preview. The 11-slide course template's branding, theme and
master/layout structure are preserved. Tables, process diagram and the two
coverage charts/embedded workbooks remain editable. AFML labels/instructions
and placeholder memes have been replaced with the ADA study content.
Team name and sections are intentionally blank. Sources and interpretation
details appear in speaker notes and the accompanying report/notebook.
''')
    (STAGE/'05_Video/README.md').write_text('''# Video handoff

The team will record the 3–5-minute final presentation separately. No video was
rendered in this task. Older rehearsal material is preserved in the pre-validation
backup outside this package and is not represented as the updated final video.
Use the current deck/report results when recording.
''')
    (STAGE/'06_IEEE_Report/README.md').write_text('''# IEEE report

The final PDF uses the IEEEtran conference class and includes the methods,
registered design, complete campaign audit, H1–H4 results, sensitivities,
real-panel evidence and material scope. Editable LaTeX source, the class and
figure PDFs are included. Compile with Tectonic or a compatible LaTeX installation.
The separate issues TXT records further research extensions; the report retains
the limitations that materially affect its conclusions.
''')
    (AUDIT/'REPRODUCIBILITY.md').write_text('''# Evidence and reproduction

The canonical facts/interpretation JSON and all-grid CSV are the numerical
authority. `campaign_audit.json` independently audits all 172,800 primary
intervals from both frozen archives. `source_replay.json` records 12 exact
scientific-record replays in the original Kaggle package versions. R reference
fixtures and outputs check the established CR2 specialization independently.

`real_audit.json` records source hashes, labels and all joint-block sensitivities.
`real_independent_audit.json` checks 39,377 numerical entries using separate
direct return, least-squares, block-resampling and CAR calculations.
`historical_forensics.json` records the missing-original search outcome.

`notebook_build.json` identifies the exact bundle and semantic source digest.
`clean_run.json` must match those values and cover all 48 code stages. The
executed notebook is the actual submission source with outputs, not a shorter
substitute demonstration. `verification_run.json` records 439 passing tests and
the seven Python 3.13 fork deprecation warnings, rather than claiming a warning-
free run. `FINAL_RESULTS_AND_TECHNICAL_REVIEW.md` records delegated acceptance.

`templates/` preserves the supplied one-pager/PPT and IEEE class for editable
artifact rebuilding. Set ADA_TEMPLATES_DIR to that folder if rebuilding outside
the original workspace. Artifact build scripts are in the source ZIP. No original
historical price archive, teammate approval or mentor endorsement is invented.

The final package checksum manifest covers every included file except itself.
The sibling ZIP checksum is recorded separately, avoiding circular hashes.
''')
    print('Stage documentation and supplied template inputs prepared.')


def install():
    build=json.loads((AUDIT/'notebook_build.json').read_text());clean=json.loads((AUDIT/'clean_run.json').read_text())
    nb=json.loads((STAGE/'02_Code/ADA_Project_Final.ipynb').read_text())
    source_digest=hashlib.sha256(json.dumps([''.join(c['source']) if isinstance(c['source'],list) else c['source'] for c in nb['cells']]).encode()).hexdigest()
    assert clean['status']=='PASS' and clean['code_cells']==48
    assert source_digest==build['semantic_source_sha256']==clean['source_digest']
    assert clean['reproduction']['bundle_sha256']==build['bundle_sha256']
    assert all(c['execution_count'] is not None and not any(o.get('output_type')=='error' for o in c['outputs']) for c in nb['cells'] if c['cell_type']=='code')
    assert sha(STAGE/'03_Dataset/source/notebook_bundle.zip')==build['bundle_sha256']
    for required in ['01_One_Pager/ADA_Final_One_Pager.docx','01_One_Pager/ADA_Final_One_Pager.pdf','04_Presentation/ADA_Project_Final.pptx','04_Presentation/ADA_Project_Final.pdf','06_IEEE_Report/ADA_IEEE_Report.pdf']:
        assert (STAGE/required).stat().st_size>1000,required
    # Compile logs belong with evidence rather than beside the final report.
    for p in (STAGE/'06_IEEE_Report').glob('*.log'):shutil.move(p,AUDIT/('report_'+p.name))
    manifest={str(p.relative_to(STAGE)):sha(p) for p in sorted(STAGE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'}
    (STAGE/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in manifest.items()))
    final=ROOT.parent/'ADA PROJECT DELIVERABLES'
    backup=BASE/'prior_deliverables_before_install'
    if final.exists():
        if backup.exists():raise FileExistsError('A prior install backup already exists; inspect before replacing again')
        final.rename(backup)
    shutil.copytree(STAGE,final)
    archive=ROOT.parent/'ADA_PROJECT_DELIVERABLES.zip'
    if archive.exists():archive.rename(BASE/'prior_deliverables_before_install.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(final.rglob('*')):
            if p.is_file():z.write(p,str(Path(final.name)/p.relative_to(final)))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    for name,digest in manifest.items():assert sha(final/name)==digest
    receipt={'status':'PASS','installed_utc':datetime.now(timezone.utc).isoformat(),'files':len(manifest)+1,
             'zip_bytes':archive.stat().st_size,'zip_sha256':sha(archive),'notebook_source_digest':source_digest,
             'bundle_sha256':build['bundle_sha256'],'technical_scope':'Completed registered finite-grid study; video/Drive/Form and team-name/sections remain with team','git_publication':'New research branch remains local, not committed/pushed/merged without instruction'}
    (BASE/'installed_release.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (ROOT.parent/'ADA_PROJECT_DELIVERABLES.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--install',action='store_true');a=p.parse_args()
    prepare() if a.prepare else install()
