"""Fill the actual 11-slide course PPTX while retaining masters, branding and theme.

Native tables, diagram objects, chart caches and embedded workbooks stay editable.
The course's placeholder memes/instructions are removed; no full-slide screenshots
replace its content. XML is edited with namespace-preserving DOM operations.
"""
from pathlib import Path
import base64,io,json,re,zipfile
from artifact_inputs import template
from xml.dom import minidom as M
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/raw/final_research_20261112'
DEST=BASE/'release_stage/ADA PROJECT DELIVERABLES/04_Presentation'
facts=json.loads((BASE/'final_assets/facts.json').read_text());study=json.loads((BASE/'final_interpretation/interpretation.json').read_text())
source=template('AFML-ppt-template.pptx')
with zipfile.ZipFile(source) as z:parts={n:z.read(n) for n in z.namelist()}
A='http://schemas.openxmlformats.org/drawingml/2006/main';P='http://schemas.openxmlformats.org/presentationml/2006/main';R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
def parse(body):return M.parseString(body)
def nodes(parent,tag):return list(parent.getElementsByTagName(tag))
def direct(parent,tag):return [n for n in parent.childNodes if n.nodeType==n.ELEMENT_NODE and n.tagName==tag]
def text(parent):return ''.join(n.firstChild.data for n in nodes(parent,'a:t') if n.firstChild)
def fragment(xml):return parse(f'<root xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}">{xml}</root>').documentElement
def append_xml(parent,xml):
    for n in list(fragment(xml).childNodes):parent.appendChild(parent.ownerDocument.importNode(n,True))
def paragraph(s,size=2400,color='0000FF',bold=False,align='l'):
    return f'<a:p><a:pPr algn="{align}" marL="0" indent="0"><a:spcAft><a:spcPts val="1000"/></a:spcAft></a:pPr><a:r><a:rPr lang="en-US" sz="{size}" b="{int(bold)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Trebuchet MS"/></a:rPr><a:t>{escape(s)}</a:t></a:r><a:endParaRPr lang="en-US" sz="{size}"/></a:p>'
def set_text(parent,lines,size=2400,color='0000FF',bold=False,align='l'):
    body=nodes(parent,'p:txBody') or nodes(parent,'a:txBody')
    body=body[0] if body else parent
    for n in direct(body,'a:p'):body.removeChild(n)
    for line in lines:append_xml(body,paragraph(line,size,color,bold,align))
def shape(doc,id):return next(s for s in nodes(doc,'p:sp') if nodes(s,'p:cNvPr')[0].getAttribute('id')==str(id))
def position(parent,x,y,w,h):
    xfrm=nodes(parent,'a:xfrm') or nodes(parent,'p:xfrm');xf=xfrm[0]
    off=nodes(xf,'a:off');ext=nodes(xf,'a:ext')
    for key,v in [('x',x),('y',y)]:off[0].setAttribute(key,str(round(v*914400)))
    for key,v in [('cx',w),('cy',h)]:ext[0].setAttribute(key,str(round(v*914400)))
def remove(parent):parent.parentNode.removeChild(parent)
def textbox(doc,id,lines,x,y,w,h,size=1800,color='0000FF',bold=False,fill=None):
    spTree=nodes(doc,'p:spTree')[0]
    fillxml=f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
    append_xml(spTree,f'<p:sp><p:nvSpPr><p:cNvPr id="{id}" name="ADA content {id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{round(x*914400)}" y="{round(y*914400)}"/><a:ext cx="{round(w*914400)}" cy="{round(h*914400)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fillxml}<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="91440" rIns="91440" tIns="45720" bIns="45720"/><a:lstStyle/>'+''.join(paragraph(s,size,color,bold) for s in lines)+'</p:txBody></p:sp>')
def connector(doc,id,x1,y1,x2,y2):
    append_xml(nodes(doc,'p:spTree')[0],f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{id}" name="Process connector"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr><p:spPr><a:xfrm><a:off x="{round(x1*914400)}" y="{round(y1*914400)}"/><a:ext cx="{round((x2-x1)*914400)}" cy="{round((y2-y1)*914400)}"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="19050"><a:solidFill><a:srgbClr val="008BA3"/></a:solidFill><a:tailEnd type="triangle"/></a:ln></p:spPr></p:cxnSp>')
def fill_table(doc,rows,widths=None,size=1400):
    table=nodes(doc,'a:tbl')[0];tr=direct(table,'a:tr');assert len(rows)==len(tr)
    for i,(row,values) in enumerate(zip(tr,rows)):
        cells=direct(row,'a:tc');assert len(cells)==len(values)
        for cell,value in zip(cells,values):
            set_text(cell,str(value).split('\n'),size,'FFFFFF' if i==0 else '17395C',i==0)
            for ppr in nodes(cell,'a:pPr'):
                for sp in direct(ppr,'a:spcAft'):ppr.removeChild(sp)
            tcpr=nodes(cell,'a:tcPr')[0];tcpr.setAttribute('marL','65000');tcpr.setAttribute('marR','65000');tcpr.setAttribute('marT','40000');tcpr.setAttribute('marB','30000')
            if i==0:
                for n in list(tcpr.childNodes):
                    if n.nodeType==n.ELEMENT_NODE and n.tagName in ['a:noFill','a:solidFill','a:gradFill']:tcpr.removeChild(n)
                append_xml(tcpr,'<a:solidFill><a:srgbClr val="008BA3"/></a:solidFill>')
    if widths:
        for c,w in zip(nodes(table,'a:gridCol'),widths):c.setAttribute('w',str(round(w*914400)))
    return table

titles={2:'Research question',3:'Research contribution',4:'Dataset and evidence',5:'Overall design and approach',6:'Final simulation results',7:'Done and remaining handoff',8:'Quantity and quality of work',9:'Top learning points',10:'Scope and research challenges',11:'Reference papers'}
slides={i:parse(parts[f'ppt/slides/slide{i}.xml']) for i in range(1,12)}
for i,d in slides.items():
    # Body pictures in the supplied template are instructional memes. The PES
    # branding stays on the inherited master and repeated upper-right picture.
    for pic in nodes(d,'p:pic'):
        off=nodes(pic,'a:off')
        if off and int(off[0].getAttribute('y'))>1500000:remove(pic)
    for sp in nodes(d,'p:sp'):
        if 'UE24AM342AA1 Course Project' in text(sp):set_text(sp,['Advanced Data Analytics Course Project'],1400,'777777',False,'r')
    if i>1:
        title_id=14 if i<=7 else 3;set_text(shape(d,title_id),[titles[i]],2400,'FF0000',False,'r')
        position(shape(d,title_id),3.05,1.09,8.7,.58)
    parts[f'ppt/slides/slide{i}.xml']=d.toxml(encoding='UTF-8')
d=slides[1]
set_text(shape(d,2),['Advanced Data Analytics'],2800,'0000FF');position(shape(d,2),.8,.58,11.4,.65)
set_text(shape(d,4),['DML Confidence Intervals','under Regime-Level Dependence','']+[m['name']+'  '+m['SRN'] for m in facts['members']]+['Team name:                         Section(s):'],2200,'0000FF')
position(shape(d,4),.9,2.0,11.5,4.2)
bodies={2:[
'Financial events can share regime shocks, making conventional intervals unreliable.',
'Does robust variance restore DML coverage, or do grouped folds add benefit?',
'Compare random/grouped folds crossed with naive/CR2 inference on the same worlds.',
'Coverage and null size determine calibration. Real data provide descriptive context.'],
3:[
'A controlled assessment of fold choice and uncertainty under one explicit regime DGP.',
'Frozen final design: 78 scenarios, 43,200 complete four-cell blocks and paired comparisons.',
'External R reference verification plus an independent audit of every saved interval.',
'Executed H4 matching and a common-window financial panel. Established methods, no new theorem.'],
4:[
'Synthetic evidence: 43,200 scenario-replication blocks, 172,800 primary intervals and no missing or failed cells.',
'Common panel: six firms, 1,511 trading dates (2016–2021) and 9,066 adjusted-close returns.',
'Strictly prior VIX labels: 332 calm, 669 mixed and 510 turbulent dates.',
'Fresh classical benchmark: seven event cases with the actual S&P 500 index and a verified ADS/BFH crosswalk.']}
for i,lines in bodies.items():
    body=shape(slides[i],10);set_text(body,lines,2200);position(body,1.15,2.0,11.25,4.45)
    for ppr in nodes(body,'a:pPr'):
        ppr.setAttribute('marL','300000');ppr.setAttribute('indent','-260000')
        append_xml(ppr,'<a:buChar char="&#8226;"/>')
# Required architecture diagram: editable native process objects.
d=slides[5];remove(shape(d,8))
steps=[('Frozen design','Controls and budgets'),('Calendar DGP','Own-firm GARCH'),('Four DML cells','Held-out nuisances'),('Independent audit','Hashes and arithmetic'),('Reported evidence','Coverage and size')]
for j,(a,b) in enumerate(steps):
    x=.65+j*2.55;textbox(d,100+j,[a,b],x,2.35,2.23,1.25,1650,'17395C',False,'E7F4F8')
    if j<4:connector(d,120+j,x+2.23,2.95,x+2.50,2.95)
textbox(d,130,['Real-data path: common calendar, prior-only VIX labels, market residuals and joint block uncertainty'],.8,4.25,11.7,1.0,2050)
textbox(d,131,['Known simulation truth is evaluation metadata. It never enters nuisance fitting.'],.8,5.5,11.7,.8,1800,'17395C')
# Native editable charts, including synchronized embedded workbook values.
seed=json.loads((ROOT/'submission/chart_seed.json').read_text())
chart_template=seed['chart_xml'].encode();workbook=base64.b64decode(seed['workbook_base64']);chart_rels=seed['chart_rels'].encode()
d=slides[6];remove(shape(d,6));rels=parse(parts['ppt/slides/_rels/slide6.xml.rels'])
for index,K in enumerate([4,16],1):
    cells=['random_xfit__naive_var','random_xfit__robust_var','grouped_xfit__naive_var','grouped_xfit__robust_var']
    values=[next(r['coverage95'] for r in study['summaries'] if r['scenario']==f'main_K{K}_d0.5_g1_tau1' and r['cell']==c) for c in cells]
    c=parse(chart_template);title=nodes(c,'c:title')[0];nodes(title,'a:t')[0].firstChild.data=f'K={K}, R=500'
    for pt,value in zip(nodes(nodes(c,'c:numCache')[0],'c:pt'),values):nodes(pt,'c:v')[0].firstChild.data=str(value)
    for t in nodes(c,'c:v'):
        if t.firstChild:
            t.firstChild.data=t.firstChild.data.replace('Random + robust','Random CR2').replace('Grouped + robust','Grouped CR2').replace('Random + naive','Random naive').replace('Grouped + naive','Grouped naive')
    for numfmt in nodes(nodes(c,'c:valAx')[0],'c:numFmt'):numfmt.setAttribute('formatCode','0%')
    parts[f'ppt/charts/chart{index}.xml']=c.toxml(encoding='UTF-8')
    wb=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(workbook)) as w,zipfile.ZipFile(wb,'w',zipfile.ZIP_DEFLATED) as out:
        for name in w.namelist():
            data=w.read(name)
            if name=='xl/worksheets/sheet1.xml':
                wd=parse(data)
                for cell,value in zip([n for n in nodes(wd,'c') if n.getAttribute('r') in ['B2','B3','B4','B5']],values):nodes(cell,'v')[0].firstChild.data=str(value)
                data=wd.toxml(encoding='UTF-8')
            if name=='xl/sharedStrings.xml':data=data.replace(b'Random + robust',b'Random CR2').replace(b'Grouped + robust',b'Grouped CR2').replace(b'Random + naive',b'Random naive').replace(b'Grouped + naive',b'Grouped naive')
            out.writestr(name,data)
    parts[f'ppt/embeddings/Microsoft_Excel_Worksheet{index}.xlsx']=wb.getvalue()
    parts[f'ppt/charts/_rels/chart{index}.xml.rels']=chart_rels.replace(b'Worksheet1.xlsx',f'Worksheet{index}.xlsx'.encode())
    rel=rels.createElement('Relationship');rel.setAttribute('Id',f'rIdADAChart{index}');rel.setAttribute('Type',R+'/chart');rel.setAttribute('Target',f'../charts/chart{index}.xml');rels.documentElement.appendChild(rel)
    x=.45+(index-1)*6.25
    append_xml(nodes(d,'p:spTree')[0],f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{200+index}" name="Focal coverage K{K}"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="{round(x*914400)}" y="1828800"/><a:ext cx="5486400" cy="3200400"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" r:id="rIdADAChart{index}"/></a:graphicData></a:graphic></p:graphicFrame>')
parts['ppt/slides/_rels/slide6.xml.rels']=rels.toxml(encoding='UTF-8')
textbox(d,220,['CR2 improves coverage. Grouped folds add no material benefit in the registered focal comparisons.'],.8,5.6,11.8,.8,1800)
textbox(d,221,['Density=.5, γ=1, τ=1. Target coverage: 95%. Few-regime calibration remains imperfect.'],.8,6.35,11.8,.4,1400,'555555')
fill_table(slides[7],[['No','Description','Status'],['1','Final design, independent controls and external CR2 reference','Done'],['2','Full campaign, robustness conditions and independent raw audit','Done'],['3','H4 structural matches and paired coverage comparisons','Done'],['4','Common daily panel, diagnostics and fresh classical benchmark','Done'],['5','48-stage notebook, report, one-pager and course-template PPT','Done'],['6','Team name and section fields','Team entry'],['7','Video presentation and Drive/Form submission','Team handoff']],size=1400)
fill_table(slides[8],[['No','Functionality','Complete','Runs','Verification'],['1','Firm-level GARCH','100%','Yes','Recurrence, moments and RNG'],['2','Random/grouped folds','100%','Yes','Component integrity'],['3','CR2/Satterthwaite','100%','Yes','60 external R comparisons'],['4','Final simulations','100%','Yes','43,200 complete blocks'],['5','Independent audit','100%','Yes','172,800 primary intervals'],['6','Daily labelled panel','100%','Yes','1,511 aligned dates'],['7','Classical benchmark','100%','Yes','7 fresh event cases'],['8','Kaggle notebook','100%','Yes','48 explained code stages'],['9','Submission documents','100%','Yes','439 tests; linked evidence']],widths=[.45,3.5,1.15,.8,6.55],size=1250)
fill_table(slides[9],[['No','Learning point'],['1','Robust uncertainty substantially improves focal coverage, while few-regime calibration remains imperfect.'],['2','Grouped cross-fitting adds no material benefit in the two prespecified focal comparisons.'],['3','Rare multiple membership can coexist with dense O(n²) shared-pair dependence.'],['4','Market adjustment attenuates the turbulent-period raw correlation contrast.'],['5','Fresh reconstruction and authentication of missing historical files are different claims.']],size=1500)
fill_table(slides[10],[['No','Research challenge','Treatment in this study'],['1','Few-regime calibration','Report the observed undercoverage'],['2','Generalization beyond this design','One DGP family and selected six-firm panel'],['3','Matching the full dependence structure','H4 matches pair probability or exposure separately'],['4','Missing original historical inputs','Use fresh audited evidence; retain provenance distinction'],['5','Calendar-factor dependence theory','Prespecified stress test, without a universal validity claim']],size=1350)
fill_table(slides[11],[['No','Paper / source','Authors','Year'],['1','Double/debiased machine learning','Chernozhukov et al.','2018'],['2','Small-sample cluster-robust methods','Pustejovsky & Tipton','2018'],['3','Corrigendum to small-sample methods','Pustejovsky & Tipton','2023'],['4','Evaluating statistical methods by simulation','Morris, White & Crowther','2019'],['5','Multiway cluster-robust DML','Chiang, Kato, Ma & Sasaki','2022'],['6','Cross-fitting with correlated units (preprint)','Balkus, Laith & Hejazi','2026'],['7','Event studies with cross-sectional correlation','Kolari & Pynnönen','2010']],widths=[.55,6.0,4.8,1.1],size=1350)
# Record exact supporting sources in the course's existing speaker-note parts.
for i,d in slides.items():
    relpath=f'ppt/slides/_rels/slide{i}.xml.rels'
    rel=parse(parts[relpath]);note=next((n.getAttribute('Target') for n in nodes(rel,'Relationship') if n.getAttribute('Type')==R+'/notesSlide'),None)
    if note:
        path='ppt/'+note.replace('../','');nd=parse(parts[path]);body=next((s for s in nodes(nd,'p:sp') if any(p.getAttribute('type')=='body' for p in nodes(s,'p:ph'))),None)
        if body:
            note_text='Source: final audited interpretation.json, real_audit.json and registered final_design_20261112.json, packaged in 07_Audit_and_Reproducibility. All counts refer to the fresh final research campaign. '
            if i in [3,5,6,11]:note_text+='Method sources: https://doi.org/10.1111/ectj.12097 ; https://doi.org/10.1080/07350015.2016.1247004 ; corrigendum https://doi.org/10.1080/07350015.2023.2174123 ; https://jepusto.github.io/clubSandwich/articles/panel-data-CRVE.html . '
            if i==4:note_text+='Acquisition: Yahoo Finance via yfinance, explicit adjustment options. ADS/BFH identity: https://www.sec.gov/Archives/edgar/data/1101215/000110121522000058/form_8-k.htm . '
            if i==6:note_text+='Coverage point estimates at d=.5, gamma=1, tau=1, R=500. Wilson and paired intervals appear in the report/notebook. No equivalence claim follows from nonsignificant paired tests. '
            set_text(body,[note_text],1200,'000000');parts[path]=nd.toxml(encoding='UTF-8')
    parts[f'ppt/slides/slide{i}.xml']=d.toxml(encoding='UTF-8')
# Remove stale AFML labels in layouts/masters as well as visible slide text.
for name,data in list(parts.items()):
    if name.endswith('.xml'):
        data=data.replace(b'UE24AM342AA1',b'ADA').replace(b'Advanced Foundations in Machine Learning',b'Advanced Data Analytics')
        parts[name]=data
ct=parse(parts['[Content_Types].xml']);namespace=ct.documentElement.namespaceURI
for index in [1,2]:
    e=ct.createElementNS(namespace,'Override');e.setAttribute('PartName',f'/ppt/charts/chart{index}.xml');e.setAttribute('ContentType','application/vnd.openxmlformats-officedocument.drawingml.chart+xml');ct.documentElement.appendChild(e)
if not any(e.getAttribute('Extension')=='xlsx' for e in nodes(ct,'Default')):
    e=ct.createElementNS(namespace,'Default');e.setAttribute('Extension','xlsx');e.setAttribute('ContentType','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');ct.documentElement.insertBefore(e,nodes(ct,'Override')[0])
parts['[Content_Types].xml']=ct.toxml(encoding='UTF-8')
DEST.mkdir(parents=True,exist_ok=True)
output=DEST/'ADA_Project_Final.pptx'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in parts.items():z.writestr(name,data)
print(output)
