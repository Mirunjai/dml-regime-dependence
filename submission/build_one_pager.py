"""Populate the supplied course template, preserving its fields and tables."""
from pathlib import Path
import json
from docx import Document
from docx.shared import Pt

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'ADA PROJECT DELIVERABLES'
h=json.loads((ROOT/'results/raw/final_submission_assets_20261112/headline.json').read_text())
d=Document('/home/deeptanshukumar/Downloads/DefaultCourseProject_OnePager.docx')
text={0:'Team Name: ',1:'Project Title:',2:'Auditing DML Confidence Intervals under Regime-Level Dependence',
3:'Extension(s):',4:'A reproducible 2 x 2 comparison of random/grouped cross-fitting and naive/overlap-sandwich variance, supported by independent known-truth controls, complete raw archives and paired uncertainty. The study delivers EXPLORATORY calibration evidence using established methods.',
5:'Possible Dataset(s) and Source(s):',6:f"Generated simulation archive: {h['scenarios']} scenarios x {h['replications']} worlds; {h['interval_rows']:,} interval records. Dataset folder: 03_Dataset. An illustrative six-firm S&P 500 event-history case study adds financial context. Real-data metadata, label rules and extraction scripts are supplied; provider prices are excluded. VIX source: cboe.com/tradable-products/vix/vix-historical-data.",
7:'Evaluation Criteria:',8:'95% interval coverage is primary; zero-effect rejection is size and nonzero-effect rejection is power. Report counts, MCSE, Wilson intervals and complete-four-cell paired contrasts. Better calibration means closer to .95 coverage and .05 size; greater coverage alone is not a positive result.',
9:'Our Learning Goal:',10:'Separate nuisance fitting, fold construction and interval calibration; build an auditable simulation and explain what its evidence supports. The completed workflow includes independent recomputation, sensitivity outputs and a fresh-kernel notebook run. Results are exploratory within one DGP family; the six-firm case study is descriptive. Synthetic Control is not executed.',11:'Reference Papers/Sources:'}
text[8]+=' Fresh independent-control robust coverage: 87.0% / 87.5% (R=200); this demonstrates the value of explicit calibration checks.'
for i,t in text.items():d.paragraphs[i].text=t
for section in d.sections:
 for para in section.header.paragraphs:
  if 'Course Project One Pager' in para.text:
   para.runs[0].text='ADA Course Project One Pager: Finance Track'
   for run in para.runs[1:]:run.text=''
 for para in section.footer.paragraphs:
  if 'Machine Learning' in para.text:
   para.runs[0].text='Advanced Data Analytics | Project A'
   for run in para.runs[1:]:run.text=''
members=[('Deeptanshu Kumar','PES1UG24AM357'),('Mirunjai Suresh Kumar','PES1UG24AM161'),('Preksha K','PES1UG24AM907'),('Sudarshan G','PES1UG24AM450')]
for row,(name,srn) in zip(d.tables[0].rows[1:],members):
 row.cells[0].text=name;row.cells[1].text='';row.cells[2].text=srn
refs=[('Chernozhukov et al. (2018). Double/debiased machine learning.','doi.org/10.1111/ectj.12097'),('Chiang, Kato, Ma, Sasaki (2022). Multiway cluster robust DML.','arxiv.org/abs/1909.03489'),('Balkus, Laith, Hejazi (2026). Cross-fitting with correlated units (preprint).','arxiv.org/abs/2601.10899v3')]
for row,(title,url) in zip(d.tables[1].rows[1:],refs):row.cells[1].text=title;row.cells[2].text=url
for p in d.paragraphs:
 p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=1.0
 for r in p.runs:r.font.name='Calibri';r.font.size=Pt(9.5)
for i in (0,1,3,5,7,9,11):
 for r in d.paragraphs[i].runs:r.bold=True;r.font.size=Pt(10)
for table in d.tables:
 for row in table.rows:
  for c in row.cells:
   for p in c.paragraphs:
    p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
    for r in p.runs:r.font.name='Calibri';r.font.size=Pt(9)
d.core_properties.title='ADA Project A - Final One Pager'
d.core_properties.author='Deeptanshu Kumar; Mirunjai Suresh Kumar; Preksha K; Sudarshan G'
d.core_properties.subject='Exploratory final submission; team name and sections intentionally blank'
p=DEST/'01_One_Pager/ADA_Final_One_Pager.docx';d.save(p);print(p)
