"""Execute the actual staged notebook with an isolated project-local kernel."""
from pathlib import Path
import hashlib,json,os,time
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/raw/final_research_20261112'
notebook=BASE/'release_stage/ADA PROJECT DELIVERABLES/02_Code/ADA_Project_Final.ipynb'
kernel_root=BASE/'jupyter';kernel=kernel_root/'kernels/ada-final-local';kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[str(ROOT/'.venv/bin/python'),'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'ADA final local','language':'python'}))
os.environ['JUPYTER_PATH']=str(kernel_root)
nb=nbformat.read(notebook,as_version=4);digest=hashlib.sha256(json.dumps([c.source for c in nb.cells]).encode()).hexdigest()
start=time.perf_counter()
try:
    NotebookClient(nb,timeout=900,kernel_name='ada-final-local',allow_errors=False).execute(cwd=notebook.parent)
finally:
    nbformat.write(nb,BASE/'local_executed.ipynb')
report={'status':'PASS','source_digest':digest,'code_cells':sum(c.cell_type=='code' for c in nb.cells),'elapsed_seconds':time.perf_counter()-start,'execution':'Fresh project-local Jupyter kernel, actual staged source and frozen bundle'}
(BASE/'local_clean_run.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
