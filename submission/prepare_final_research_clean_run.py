"""Build a private Kaggle wrapper that executes the actual submission notebook."""
from pathlib import Path
import base64,json,zlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/raw/final_research_20261112'
nb_path=BASE/'release_stage/ADA PROJECT DELIVERABLES/02_Code/ADA_Project_Final.ipynb'
target=ROOT/'compute-tools/kaggle-final-research-clean-run';target.mkdir(exist_ok=True)
payload=base64.b64encode(zlib.compress(nb_path.read_bytes(),9)).decode()
code='''from pathlib import Path
import base64,hashlib,json,os,tempfile,time,zipfile,zlib
import nbformat
from nbclient import NotebookClient
original=zlib.decompress(base64.b64decode(__PAYLOAD__))
nb=nbformat.reads(original.decode(),as_version=4)
source_digest=hashlib.sha256(json.dumps([c.source for c in nb.cells]).encode()).hexdigest()
started=time.perf_counter()
with tempfile.TemporaryDirectory(prefix='ada-clean-final-') as work:
    os.environ['TMPDIR']=work
    nb=NotebookClient(nb,timeout=900,kernel_name='python3',allow_errors=False).execute(cwd=work)
    assert all(o.output_type!='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
    assert all(c.execution_count is not None for c in nb.cells if c.cell_type=='code')
    generated=list(Path(work).glob('ada-final-reproduction-*/generated'));assert len(generated)==1,str(generated)
    executed=Path(work)/'ADA_Project_Final_Executed.ipynb';nbformat.write(nb,executed)
    receipt=json.loads((generated[0]/'reproduction.json').read_text())
    summary={'status':'PASS','execution':'Fresh Jupyter kernel in fresh private Kaggle CPU session; matching checksummed final research bundle only; internet/GPU disabled','source_digest':source_digest,'code_cells':sum(c.cell_type=='code' for c in nb.cells),'elapsed_seconds':time.perf_counter()-started,'reproduction':receipt}
    with zipfile.ZipFile('/kaggle/working/final_notebook_release.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.write(executed,executed.name)
        for f in generated[0].rglob('*'):
            if f.is_file():z.write(f,'generated/'+str(f.relative_to(generated[0])))
        z.writestr('clean_run.json',json.dumps(summary,indent=2))
Path('/kaggle/working/clean_run.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
'''.replace('__PAYLOAD__',repr(payload))
compile(code,'clean_run.py','exec')
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},'cells':[{'cell_type':'markdown','id':'purpose','metadata':{},'source':'# Final submission notebook clean execution\nRuns the exact granular source with its checksummed bundle. Registered finite-grid evidence.'},{'cell_type':'code','id':'execute','metadata':{},'source':code,'execution_count':None,'outputs':[]}]}
(target/'reproduce.ipynb').write_text(json.dumps(nb))
meta={'id':'deeptanshukumar/ada-final-research-clean-run','title':'ADA final research clean run','code_file':'reproduce.ipynb','language':'python','kernel_type':'notebook','is_private':True,'enable_gpu':False,'enable_tpu':False,'enable_internet':False,'dataset_sources':['deeptanshukumar/ada-dml-final-research-bundle'],'kernel_sources':[],'competition_sources':[]}
(target/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
dataset=BASE/'kaggle_dataset';dataset.mkdir(exist_ok=True)
blob=(BASE/'release_stage/ADA PROJECT DELIVERABLES/03_Dataset/source/notebook_bundle.zip').read_bytes()
(dataset/'notebook_bundle.bin').write_bytes(blob)
(dataset/'dataset-metadata.json').write_text(json.dumps({'id':'deeptanshukumar/ada-dml-final-research-bundle','title':'ADA DML final research bundle','licenses':[{'name':'other'}]},indent=2)+'\n')
print('Private research bundle and clean-run wrapper prepared.')
