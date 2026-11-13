"""Build two private CPU campaign scripts from one immutable own-source archive."""
from pathlib import Path
import base64,hashlib,io,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'configs/experiments/final-validation/final_design_20261112.json'
payload=io.BytesIO()
with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as z:
    for directory in ('research/week2_completion','research/final_validation','src'):
        for p in sorted((ROOT/directory).rglob('*.py')):
            if '__pycache__' not in p.parts and 'original' not in p.parts:z.write(p,p.relative_to(ROOT))
    for name in ('research/__init__.py','scripts/audit_final_campaign.py'):z.write(ROOT/name,name)
    z.write(PLAN,PLAN.relative_to(ROOT))
blob=payload.getvalue();sha=hashlib.sha256(blob).hexdigest()
(ROOT/'results/raw/final_research_20261112/final_campaign_source.zip').write_bytes(blob)
for kind in ('core','robustness'):
    p=ROOT/('compute-tools/kaggle-final-validation-'+kind);p.mkdir(exist_ok=True)
    code='''from pathlib import Path
import base64,hashlib,io,json,os,subprocess,sys,time,zipfile
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
blob=base64.b64decode(__BLOB__)
assert hashlib.sha256(blob).hexdigest()==__SHA__
root=Path('/kaggle/working/source');root.mkdir(exist_ok=False)
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    assert all((root/n).resolve().is_relative_to(root) for n in z.namelist());z.extractall(root)
Path('/kaggle/working/final_campaign_source.zip').write_bytes(blob)
os.chdir(root)
plan_path=Path('configs/experiments/final-validation/final_design_20261112.json');plan=json.loads(plan_path.read_text())
selected=[s['id'] for s in plan['scenarios'] if (s['role'].startswith('robustness_') or s['role'].startswith('stress_'))==__ROBUST__]
print('PARTITION',__KIND__,'SCENARIOS',len(selected),'SOURCE',__SHA__,flush=True)
args=[sys.executable,'-m','research.final_validation.campaign','--plan',str(plan_path),'--out','/kaggle/working/raw','--workers','4']
for name in selected:args.extend(['--scenario',name])
subprocess.run(args,check=True)
with zipfile.ZipFile('/kaggle/working/campaign.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in Path('/kaggle/working/raw').rglob('*'):
        if f.is_file():z.write(f,str(f.relative_to('/kaggle/working/raw')))
print('COMPLETE',__KIND__,flush=True)
'''
    for token,value in {'__BLOB__':repr(base64.b64encode(blob).decode()),'__SHA__':repr(sha),'__ROBUST__':str(kind=='robustness'),'__KIND__':repr(kind)}.items():code=code.replace(token,value)
    compile(code,str(p/'run.py'),'exec');(p/'run.py').write_text(code)
    meta={'id':'deeptanshukumar/ada-final-validation-'+kind,'title':'ADA final validation '+kind,'code_file':'run.py','language':'python','kernel_type':'script','is_private':True,'enable_gpu':False,'enable_tpu':False,'enable_internet':False,'dataset_sources':[],'kernel_sources':[],'competition_sources':[]}
    (p/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Immutable producer SHA256:',sha)
