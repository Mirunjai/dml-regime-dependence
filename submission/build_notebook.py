"""Create a standalone, offline notebook with an immutable exploratory bundle."""
from pathlib import Path
import hashlib,io,json,zipfile,shutil

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'ADA PROJECT DELIVERABLES'
DATA=DEST/'03_Dataset';DATA.mkdir(exist_ok=True)
for name in ('simulation','real_data_metadata','configs','source','tables','figures'):(DATA/name).mkdir(exist_ok=True)
for tau in (0,1):shutil.copy2(ROOT/f'results/raw/final_validation_collection_20261112/validation_tau{tau}.zip',DATA/f'simulation/validation_tau{tau}.zip')
for f in (ROOT/'results/raw/final_validation_audit_20261112').iterdir():
 if f.is_file():shutil.copy2(f,DATA/'tables'/f.name)
for f in (ROOT/'results/raw/final_submission_assets_20261112').iterdir():
 if f.suffix=='.png':shutil.copy2(f,DATA/'figures'/f.name)
 else:shutil.copy2(f,DATA/'tables'/f.name)
for f in (ROOT/'configs/experiments/final-review').glob('*.json'):shutil.copy2(f,DATA/'configs'/f.name)
for f in (ROOT/'results/raw/final_daily_panel_20261112').iterdir():
 if f.is_file():shutil.copy2(f,DATA/'real_data_metadata'/f.name)
for name in ('week3_benchmark_candidates.csv','sp500_events_verified.csv','week3_event_day_zero.csv','week3_membership_evidence.csv','week3_donor_candidates.csv'):
 shutil.copy2(ROOT/'data/processed'/name,DATA/'real_data_metadata'/name)
# Source snapshot contains code/configs only, never credentials, cached bytecode or prices.
source=io.BytesIO()
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for directory in ('src','research','scripts','tests','configs'):
  for f in sorted((ROOT/directory).rglob('*')):
   if f.is_file() and f.suffix in ('.py','.json','.yaml') and 'results' not in f.parts and '__pycache__' not in f.parts:
    z.write(f,f.relative_to(ROOT))
 for f in (ROOT/'compute-tools/final-validation').glob('*.py'):z.write(f,f.relative_to(ROOT))
 for name in ('README.md','CONTRIBUTING.md','AGENTS.md','requirements.txt','requirements-dev.txt','requirements-data.txt'):
  z.write(ROOT/name,name)
(DATA/'source/project_source.zip').write_bytes(source.getvalue())
# Notebook bundle layout is the source tree plus frozen producer records and audit inputs.
payload=io.BytesIO()
def frozen_write(z,name,body):
 info=zipfile.ZipInfo(name,date_time=(2026,11,12,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,body)

with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as z:
 with zipfile.ZipFile(io.BytesIO(source.getvalue())) as src:
  for name in src.namelist():frozen_write(z,name,src.read(name))
 for tau in (0,1):
  with zipfile.ZipFile(DATA/f'simulation/validation_tau{tau}.zip') as raw:
   for name in raw.namelist():
    if not name.endswith('/'):frozen_write(z,f'raw/validation_tau{tau}/{name}',raw.read(name))
 for source_path,dest in [(ROOT/'results/raw/final_validation_audit_20261112/audit.json','frozen/audit.json'),(ROOT/'results/raw/final_daily_panel_20261112/audit.json','frozen/daily.json'),(ROOT/'results/raw/final_daily_panel_20261112/daily_labels.csv','frozen/daily_labels.csv'),(ROOT/'results/raw/final_submission_assets_20261112/headline.json','frozen/headline.json')]:z.write(source_path,dest)
blob=payload.getvalue();digest=hashlib.sha256(blob).hexdigest();(DATA/'source/notebook_bundle.zip').write_bytes(blob)
from notebook_sections import make_cells
cells=make_cells(digest)
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.13'},'ada_evidence_class':'EXPLORATORY','ada_bundle_sha256':digest},'cells':cells}
p=DEST/'02_Code/ADA_Project_Final.ipynb';p.write_text(json.dumps(nb,indent=1)+'\n')
print(json.dumps({'notebook':str(p),'cells':len(cells),'bundle_bytes':len(blob),'bundle_sha256':digest}))
