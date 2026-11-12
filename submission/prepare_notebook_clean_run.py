from pathlib import Path
import base64,json,zlib
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'compute-tools/kaggle-ada-notebook-reproduction';p.mkdir(exist_ok=True)
notebook=ROOT.parent/'ADA PROJECT DELIVERABLES/02_Code/ADA_Project_Final.ipynb'
payload=base64.b64encode(zlib.compress(notebook.read_bytes(),9)).decode()
code='''from pathlib import Path
import base64,hashlib,json,os,tempfile,time,zipfile,zlib
import nbformat
from nbclient import NotebookClient
original=zlib.decompress(base64.b64decode(PAYLOAD))
nb=nbformat.reads(original.decode(),as_version=4)
source_digest=hashlib.sha256(json.dumps([c.source for c in nb.cells]).encode()).hexdigest()
started=time.perf_counter()
with tempfile.TemporaryDirectory(prefix='ada-clean-kernel-') as work:
    os.environ['TMPDIR']=work
    nb=NotebookClient(nb,timeout=600,kernel_name='python3',allow_errors=False).execute(cwd=work)
    assert all(o.output_type!='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
    assert all(c.execution_count is not None for c in nb.cells if c.cell_type=='code')
    generated=list(Path(work).glob('ada-final-reproduction-*/generated'));assert len(generated)==1,str(generated)
    executed=Path(work)/'ADA_Project_Final_Executed.ipynb';nbformat.write(nb,executed)
    repro=json.loads((generated[0]/'reproduction.json').read_text())
    summary={'status':'PASS','execution':'fresh Jupyter kernel in fresh Kaggle CPU session; only the declared checksummed bundle as input','source_digest':source_digest,'code_cells':sum(c.cell_type=='code' for c in nb.cells),'elapsed_seconds':time.perf_counter()-started,'reproduction':repro}
    with zipfile.ZipFile('/kaggle/working/ada_reproduction_release.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.write(executed,executed.name)
        for f in generated[0].rglob('*'):
            if f.is_file():z.write(f,'generated/'+str(f.relative_to(generated[0])))
        z.writestr('clean_run.json',json.dumps(summary,indent=2))
Path('/kaggle/working/clean_run.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
'''.replace('PAYLOAD',repr(payload))
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},'cells':[{'cell_type':'markdown','id':'purpose','metadata':{},'source':['# Clean execution of the actual submission notebook\nOnly the declared frozen bundle is required; no internet or GPU. EXPLORATORY evidence only.']},{'cell_type':'code','id':'execute','metadata':{},'source':code.splitlines(keepends=True),'execution_count':None,'outputs':[]}]}
(p/'reproduce.ipynb').write_text(json.dumps(nb))
meta={'id':'deeptanshukumar/ada-notebook-clean-reproduction','title':'ADA notebook clean reproduction','code_file':'reproduce.ipynb','language':'python','kernel_type':'notebook','is_private':True,'enable_gpu':False,'enable_tpu':False,'enable_internet':False,'dataset_sources':['deeptanshukumar/ada-dml-final-exploratory-bundle'],'kernel_sources':[],'competition_sources':[]}
(p/'kernel-metadata.json').write_text(json.dumps(meta,indent=2))
print('Wrapper bytes',(p/'reproduce.ipynb').stat().st_size)
