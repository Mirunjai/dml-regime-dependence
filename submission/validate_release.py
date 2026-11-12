"""Cross-artifact integrity and scope checks for the final course package."""
from pathlib import Path
import hashlib,json,re,subprocess,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent/'ADA PROJECT DELIVERABLES'

def pdf_info(p):
 text=subprocess.check_output(['pdfinfo',str(p)],text=True)
 return {'pages':int(re.search(r'^Pages:\s+(\d+)',text,re.M).group(1)),'bytes':p.stat().st_size}

def source_digest(n):
 return hashlib.sha256(json.dumps([''.join(c['source']) if isinstance(c['source'],list) else c['source'] for c in n['cells']]).encode()).hexdigest()

nb=json.loads((DEST/'02_Code/ADA_Project_Final.ipynb').read_text());source=json.loads((DEST/'02_Code/ADA_Project_Final_Source.ipynb').read_text());record=json.loads((DEST/'07_Audit_and_Reproducibility/clean_run.json').read_text())
assert source_digest(nb)==source_digest(source)==record['source_digest']
assert record['status']=='PASS' and record['code_cells']==38
assert all(c['execution_count'] is not None and all(o['output_type']!='error' for o in c['outputs']) for c in nb['cells'] if c['cell_type']=='code')
bundle=DEST/'03_Dataset/source/notebook_bundle.zip';assert hashlib.sha256(bundle.read_bytes()).hexdigest()==nb['metadata']['ada_bundle_sha256']==record['reproduction']['environment']['bundle_sha256']
a=json.loads((DEST/'03_Dataset/tables/audit.json').read_text());assert a['all_records_successful'] and a['all_planned_records_present']
assert len(a['summaries'])==64 and sum(r['attempted'] for r in a['summaries'])==12800
assert sum(r['failed']+r['missing'] for r in a['summaries'])==0
assert all(r['complete_four_cell_blocks']==200 for r in a['complete_block_comparisons'])
xml=ET.parse(DEST/'07_Audit_and_Reproducibility/pytest.xml');suites=xml.getroot().findall('testsuite');assert sum(int(x.attrib['tests']) for x in suites)==427 and all(int(x.attrib['failures'])==int(x.attrib['errors'])==0 for x in suites)
with zipfile.ZipFile(DEST/'04_Presentation/ADA_Project_Final_Content.pptx') as z:
 slides=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)];assert len(slides)==10
 text=''.join(z.read(n).decode() for n in slides)
 for value in ('1,872','12,800','404'):assert value in text,value
 chart=ET.fromstring(z.read('ppt/charts/chart1.xml'));ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
 vals=[float(x.text) for x in chart.findall('.//c:ser/c:val/c:numRef/c:numCache/c:pt/c:v',ns)]
 expected=[r['coverage95'] for r in a['summaries'] if r['scenario']=='independent_tau1']
 assert vals==expected,(vals,expected)
 for srn in ('PES1UG24AM357','PES1UG24AM161','PES1UG24AM907','PES1UG24AM450'):assert srn in text
with zipfile.ZipFile(DEST/'01_One_Pager/ADA_Final_One_Pager.docx') as z:
 assert 'AFML' not in ''.join(z.read(n).decode() for n in z.namelist() if n.startswith(('word/header','word/footer')) and n.endswith('.xml'))
proof=json.loads((DEST/'05_Video/video_validation.json').read_text());duration=float(proof['format']['duration']);assert 180<=duration<=300
assert any(s['codec_type']=='audio' for s in proof['streams']) and any(s['codec_type']=='video' for s in proof['streams'])
report=DEST/'06_IEEE_Report/ADA_IEEE_Report.pdf';onepager=DEST/'01_One_Pager/ADA_Final_One_Pager.pdf';pptpdf=DEST/'04_Presentation/ADA_Project_Final_Content.pdf';memo=DEST/'07_Audit_and_Reproducibility/Decision_and_Audit_Summary.pdf'
assert pdf_info(onepager)['pages']==1 and pdf_info(pptpdf)['pages']==10 and pdf_info(memo)['pages']==1
pdftext=subprocess.check_output(['pdftotext',str(report),'-'],text=True)
assert '87.0%' in pdftext and '87.5%' in pdftext and '12,800' in pdftext and '404' in pdftext
assert not re.search(r'Overfull|Citation.*undefined|Reference.*undefined',(DEST/'06_IEEE_Report/ADA_IEEE_Report.log').read_text())
# Every released ZIP is inspected, including nested source ZIPs; no credential or price file.
for p in DEST.rglob('*'):
 if not p.is_file() or 'WORKING' in p.parts:continue
 if p.suffix in ('.json','.txt','.md','.ipynb','.tex','.cjs','.py'):
  assert not re.search(rb'KGAT_[0-9a-fA-F]{32}',p.read_bytes()),str(p)
 if p.suffix=='.zip':
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None
   for name in z.namelist():
    assert not any(token in name.lower() for token in ('access_token','kaggle.json','treated_prices.csv','spy_market_prices.csv','vix_history.csv','candidate_prices_exploratory.csv')),name
    if name.endswith(('.py','.md','.json','.ipynb','.txt','.yaml','.cjs')):assert not re.search(rb'KGAT_[0-9a-fA-F]{32}',z.read(name)),name
result={'status':'PASS','notebook_code_cells':38,'source_digest':record['source_digest'],'bundle_sha256':nb['metadata']['ada_bundle_sha256'],'worlds':3200,'intervals':12800,'tests':427,'frozen_report_tests':404,'pdfs':{'report':pdf_info(report),'one_pager':pdf_info(onepager),'presentation':pdf_info(pptpdf),'internal_memo':pdf_info(memo)},'video_seconds':duration,'video_is_automated_rehearsal':True,'human_recordings_present':False,'provider_prices_or_credentials_included':False,'new_commit_or_push':False,'drive_submission_performed':False}
(DEST/'07_Audit_and_Reproducibility/release_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
