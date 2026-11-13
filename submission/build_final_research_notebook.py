"""Package the final audited research evidence and granular offline notebook.

Outputs are staged until notebook execution and document QA have completed.
Provider price histories stay outside the submission; derived returns and
regime indicators support offline regeneration of every reported data result.
"""
from pathlib import Path
import hashlib, io, json, re, shutil, zipfile
import pandas as pd
from final_notebook_sections import make_cells

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/raw/final_research_20261112'
DEST=BASE/'release_stage/ADA PROJECT DELIVERABLES'
for name in ['01_One_Pager','02_Code','03_Dataset','04_Presentation','05_Video','06_IEEE_Report','07_Audit_and_Reproducibility']:
    (DEST/name).mkdir(parents=True,exist_ok=True)
DATA=DEST/'03_Dataset'
for name in ['simulation','derived_daily_panel','configs','source','tables','figures','real_data_metadata']:(DATA/name).mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
interpretation=json.loads((BASE/'final_interpretation/interpretation.json').read_text())
real=json.loads((BASE/'real_analysis_v3/audit.json').read_text())
tests=json.loads((BASE/'verification_run.json').read_text())
facts={'schema':'ada_final_research_facts_v1','evidence_date':'2026-11-13',
       'team_name':'','sections':'','members':[{'name':n,'SRN':s} for n,s in [('Deeptanshu Kumar','PES1UG24AM357'),('Mirunjai Suresh Kumar','PES1UG24AM161'),('Preksha K','PES1UG24AM907'),('Sudarshan G','PES1UG24AM450')]],
       'scenarios':interpretation['scenarios'],'planned_blocks':interpretation['planned_blocks'],'complete_blocks':interpretation['complete_blocks'],
       'interval_rows':interpretation['interval_rows'],'failed_primary_cells':0,'missing_primary_cells':0,
       'controls_passed':interpretation['controls_all_passed'],'control_cells':len(interpretation['control_cells']),
       'control_coverage_range':[min(c['coverage'] for c in interpretation['control_cells']),max(c['coverage'] for c in interpretation['control_cells'])],
       'focal_H3':interpretation['focal_H3'],'panel_dates':real['panel_sessions'],'panel_returns':real['valid_returns'],'label_counts':real['label_counts'],
       'raw_correlation':real['block_bootstrap']['raw_returns'][0],
       'residual_correlation':real['block_bootstrap']['prior_market_residuals'][0],
       'tests':tests,'notebook_code_cells':sum(c['cell_type']=='code' for c in make_cells('PENDING')),
       'producer_source_zip_sha256':sha(BASE/'final_campaign_source.zip'),
       'campaign_archive_sha256':{k:sha(BASE/(k+'_download')/'campaign.zip') for k in ['core','robustness']},
       'historical_original_inputs_authenticated':False,
       'technical_authorization':'User-delegated final design and technical acceptance; no invented teammate signatures or mentor approval.',
       'scope':'Registered finite-grid study using established methods; no general theorem, universal validity or estimator novelty claimed.',
       'excluded':['Synthetic Control','video production','Drive sharing','Google Form submission']}
(BASE/'final_assets/facts.json').write_text(json.dumps(facts,indent=2,allow_nan=False)+'\n')
# Derived VIX indicators permit a genuinely independent daily-label regeneration
# without publishing provider price-level histories.
raw=BASE/'panel_download_v1/extracted'
manifest=json.loads((raw/'manifest.json').read_text());vix_record=next(r for r in manifest['requests'] if r['symbol']=='^VIX')
vix=pd.read_csv(raw/vix_record['file'],parse_dates=['date']).dropna(subset=['Close'])
vix['window_first_date']=vix.date.shift(19);vix['vix20']=vix.Close.rolling(20).mean()
vix=vix[['date','window_first_date','vix20']].dropna()
vix.to_csv(BASE/'real_analysis_v3/derived_vix20_history.csv',index=False,float_format='%.17g')
for p in (BASE/'real_analysis_v3').glob('*.csv'):shutil.copy2(p,DATA/'derived_daily_panel'/p.name)
for name in ['week3_benchmark_candidates.csv','sp500_events_verified.csv','week3_event_day_zero.csv','week3_membership_evidence.csv']:
    shutil.copy2(ROOT/'data/processed'/name,DATA/'real_data_metadata'/name)
for p in (ROOT/'configs/experiments/final-validation').glob('*.json'):shutil.copy2(p,DATA/'configs'/p.name)
for kind in ['core','robustness']:shutil.copy2(BASE/(kind+'_download')/'campaign.zip',DATA/'simulation'/(kind+'.zip'))
for p in (BASE/'final_assets').glob('*'):
    if p.suffix in ('.png','.pdf'):shutil.copy2(p,DATA/'figures'/p.name)
    elif p.name=='facts.json':shutil.copy2(p,DATA/'tables'/p.name)
shutil.copy2(BASE/'final_interpretation/summaries.csv',DATA/'tables/final_simulation_summary.csv')
shutil.copy2(BASE/'final_campaign_source.zip',DATA/'source/frozen_campaign_source.zip')
source=io.BytesIO()
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
    for directory in ['src','research','scripts','configs','submission','tests']:
        for p in sorted((ROOT/directory).rglob('*')):
            if p.is_file() and p.suffix in ('.py','.json','.yaml','.yml','.R','.tex','.md','.cjs') and 'results' not in p.parts and '__pycache__' not in p.parts:z.write(p,p.relative_to(ROOT))
    for n in ['README.md','CONTRIBUTING.md','AGENTS.md','requirements.txt','requirements-dev.txt','requirements-data.txt']:z.write(ROOT/n,n)
source_blob=source.getvalue();(DATA/'source/project_source.zip').write_bytes(source_blob)
frozen_map={'facts.json':BASE/'final_assets/facts.json','interpretation.json':BASE/'final_interpretation/interpretation.json',
            'campaign_audit.json':BASE/'independent_audit/audit.json','real_audit.json':BASE/'real_analysis_v3/audit.json',
            'real_independent_audit.json':BASE/'real_independent_audit/audit.json','structure.json':BASE/'structure/structure.json',
            'source_replay.json':BASE/'source_replay/replay.json','R_reference_verification.json':BASE/'official_R_reference/verification.json',
            'cr2_reference_expected.json':BASE/'cr2_reference_expected.json','clubSandwich_reference.csv':BASE/'official_R_reference/clubSandwich_reference.csv',
            'R_session_info.txt':BASE/'official_R_reference/R_session_info.txt'}
R=(ROOT/'research/final_validation/reference_check.R').read_text()
literal=re.search(r'd <- read.csv\(text = ("(?:[^"\\]|\\.)*")\)',R).group(1)
fixture=json.loads(literal)
(BASE/'cr2_reference_input.csv').write_text(fixture)
frozen_map['cr2_reference_input.csv']=BASE/'cr2_reference_input.csv'
bundle=io.BytesIO()
def write(z,name,body):
    info=zipfile.ZipInfo(name,(2026,11,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,body)
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    with zipfile.ZipFile(io.BytesIO(source_blob)) as s:
        for n in s.namelist():write(z,n,s.read(n))
    write(z,'producer_source.zip',(BASE/'final_campaign_source.zip').read_bytes())
    for k in ['core','robustness']:write(z,f'raw_archives/{k}.zip',(DATA/'simulation'/(k+'.zip')).read_bytes())
    for n,p in frozen_map.items():write(z,'frozen/'+n,p.read_bytes())
    for p in (DATA/'derived_daily_panel').glob('*.csv'):write(z,'real/'+p.name,p.read_bytes())
    for p in (DATA/'figures').glob('*.png'):write(z,'figures/'+p.name,p.read_bytes())
blob=bundle.getvalue();digest=hashlib.sha256(blob).hexdigest();(DATA/'source/notebook_bundle.zip').write_bytes(blob)
cells=make_cells(digest)
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.13'},'ada_bundle_sha256':digest,'ada_evidence_class':'REGISTERED_FINITE_GRID'},'cells':cells}
(DEST/'02_Code/ADA_Project_Final.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
audit_dir=DEST/'07_Audit_and_Reproducibility'
for name,p in frozen_map.items():shutil.copy2(p,audit_dir/name)
for name in ['execution_authorization.json','historical_forensics.json','verification_run.json']:shutil.copy2(BASE/name,audit_dir/name)
for p in (ROOT/'docs/final_validation').glob('*.md'):shutil.copy2(p,audit_dir/p.name)
record={'bundle_sha256':digest,'bundle_bytes':len(blob),'code_cells':facts['notebook_code_cells'],
        'semantic_source_sha256':hashlib.sha256(json.dumps([c['source'] for c in cells]).encode()).hexdigest(),
        'source_snapshot_sha256':hashlib.sha256(source_blob).hexdigest()}
(BASE/'notebook_build.json').write_text(json.dumps(record,indent=2)+'\n')
(audit_dir/'notebook_build.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
