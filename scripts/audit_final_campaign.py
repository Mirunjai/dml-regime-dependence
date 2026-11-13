"""Independent raw-record accounting for the registered final validation campaign.

This auditor imports neither the DGP nor the estimator. It checks byte hashes,
planned identities and interval arithmetic, then uses the independent standard-
library metric implementation. Paired contrasts require complete four-cell blocks.
"""
from __future__ import annotations
import argparse,hashlib,json,math,statistics
from pathlib import Path

from src.evaluation.verification import CELLS,audit_results
from scipy.stats import t as student_t


def read(path):return json.loads(Path(path).read_text())


def checksum(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mean_mcse(values):
    return (statistics.mean(values),statistics.stdev(values)/math.sqrt(len(values))) if len(values)>1 else (None,None)


def audit(plan_path, directories, source_root):
    plan=read(plan_path);specs={s['id']:s for s in plan['scenarios']}
    source_root=Path(source_root).resolve();blocks={};rows=[];references=[];selected=set();sources=None
    for directory in map(Path,directories):
        manifest=read(directory/'manifest.json');completion=read(directory/'completion.json')
        if manifest['plan']!=plan or manifest['plan_sha256']!=checksum(plan_path):raise ValueError('Registered plan mismatch')
        if not completion['complete']:raise ValueError('Campaign completion is not certified')
        if sources is not None and manifest['source_sha256']!=sources:raise ValueError('Mixed producer sources')
        sources=manifest['source_sha256']
        for name,digest in sources.items():
            p=(source_root/name).resolve()
            if not p.is_relative_to(source_root) or checksum(p)!=digest:raise ValueError('Producer source fingerprint mismatch')
        chosen=manifest['selected_scenarios']
        if len(chosen)!=len(set(chosen)) or selected.intersection(chosen) or not set(chosen)<=set(specs):raise ValueError('Duplicate or unknown scenario partition')
        selected.update(chosen)
        actual={str(p.relative_to(directory)) for p in directory.rglob('*.json') if p.name!='completion.json'}
        if set(completion['files_sha256'])!=actual:raise ValueError('Completion file set mismatch')
        expected={'manifest.json'}|{str(p.relative_to(directory)) for case in chosen for p in (directory/case).glob('rep_*.json')}
        if actual!=expected:raise ValueError('Unexpected raw JSON outside planned scenario records')
        for name,digest in completion['files_sha256'].items():
            p=(directory/name).resolve()
            if not p.is_relative_to(directory.resolve()) or checksum(p)!=digest:raise ValueError('Raw-file fingerprint mismatch')
        found=0
        for case in chosen:
            spec=specs[case];budget=spec.get('replications',plan['replications'])
            for p in sorted((directory/case).glob('rep_*.json')):
                r=read(p);rep=r['replication']
                if type(rep) is not int or not 0<=rep<budget or p.name!=f'rep_{rep:06d}.json':raise ValueError('Unplanned replication')
                if r['scenario']!=case or r['seed']!=spec['seed0']+rep or r['config']!={**spec['config'],'seed':spec['seed0']+rep}:raise ValueError('Block identity/config/seed mismatch')
                if r['truth']!=spec['config']['tau'] or r['learner']!=spec['learner'] or r['folds']!=spec['folds'] or r['confidence_level']!=.95:raise ValueError('Estimator/truth mismatch')
                if len(r['cells'])!=4 or {c['cell'] for c in r['cells']}!=set(CELLS):raise ValueError('Four unique cells required')
                expected_block=f'{case}::rep_{rep:06d}'
                if r['block_id']!=expected_block:raise ValueError('Block ID mismatch')
                fingerprint=r['world_sha256']
                if any(c['status']=='ok' for c in r['cells']) and (not isinstance(fingerprint,str) or len(fingerprint)!=64 or any(ch not in '0123456789abcdef' for ch in fingerprint)):raise ValueError('Invalid world fingerprint')
                is_complete=all(c['status']=='ok' for c in r['cells'])
                if type(r['complete_block']) is not bool or r['complete_block']!=is_complete:raise ValueError('Block completeness mismatch')
                for cell in r['cells']+r['reference_cells']:
                    if cell['world_sha256']!=fingerprint or cell['block_id']!=expected_block:raise ValueError('Cell/world pairing mismatch')
                    if cell['status']=='ok':
                        values=[cell.get(k) for k in ('estimate','lower','upper','se')]
                        if any(type(v) not in (int,float) or not math.isfinite(v) for v in values) or values[3]<=0 or values[1]>values[2]:raise ValueError('Invalid successful interval')
                        critical=float(student_t.ppf(.975,cell['df'])) if cell.get('method')=='component_CR2_Satterthwaite' else 1.959963984540054
                        if not math.isfinite(critical) or max(abs(values[1]-(values[0]-critical*values[3])),abs(values[2]-(values[0]+critical*values[3])))>1e-10*max(1.,abs(values[0])):raise ValueError('Interval differs from registered pivot and standard error')
                        if abs((values[1]+values[2])/2-values[0])>1e-10*max(1.,abs(values[0])):raise ValueError('Asymmetric or altered interval')
                    elif cell['status']!='failed' or not cell.get('error'):raise ValueError('Failure status/reason mismatch')
                key=(case,rep)
                if key in blocks:raise ValueError('Duplicate replication identity')
                blocks[key]=r;found+=1
                for cell in r['cells']:
                    rows.append({'scenario':case,'replication':rep,'cell':cell['cell'],'panel_id':fingerprint,
                                 'truth':r['truth'],'confidence_level':.95,**{k:cell.get(k) for k in ('status','estimate','lower','upper','error')}})
                reference_by={c['cell']:c for c in r['reference_cells']}
                for cell in r['cells']:
                    c=cell if 'naive_var' in cell['cell'] else reference_by.get(cell['cell'])
                    if c is None:c={'status':'failed','error':'Reference fit unavailable'}
                    references.append({'scenario':case,'replication':rep,'cell':cell['cell'],'panel_id':fingerprint,
                                       'truth':r['truth'],'confidence_level':.95,**{k:c.get(k) for k in ('status','estimate','lower','upper','error')}})
        if completion['worlds']!=found:raise ValueError('Completion world count mismatch')
    if selected!=set(specs):raise ValueError('Campaign scenario partition incomplete')
    metric_plan={'schema_version':1,'evidence_kind':'simulation','failure_policy':'report','confidence_level':.95,
                 'scenarios':[{'id':s['id'],'truth':s['config']['tau'],'role':'primary','replication_ids':list(range(s.get('replications',plan['replications'])))} for s in specs.values()]}
    result=audit_results(rows,metric_plan);reference=audit_results(references,metric_plan)
    result.pop('comparisons',None);reference.pop('comparisons',None)
    for report,records in ((result,rows),(reference,references)):
        for summary in report['summaries']:
            rr=[r for r in records if (r['scenario'],r['cell'])==(summary['scenario'],summary['cell']) and r['status']=='ok']
            summary['covered']=sum(r['lower']<=r['truth']<=r['upper'] for r in rr)
            summary['rejected_zero']=sum(not(r['lower']<=0<=r['upper']) for r in rr)
            summary['role']=specs[summary['scenario']]['role']
    paired=[]
    for case,spec in specs.items():
        complete=[r for (c,_),r in blocks.items() if c==case and r['complete_block']]
        for outcome in ('coverage','empirical_size' if spec['config']['tau']==0 else 'power'):
            differences=[]
            for r in complete:
                by={c['cell']:c for c in r['cells']}
                def hit(c):return int(c['lower']<=r['truth']<=c['upper']) if outcome=='coverage' else int(not(c['lower']<=0<=c['upper']))
                differences.append(hit(by['grouped_xfit__robust_var'])-hit(by['random_xfit__robust_var']))
            average,se=mean_mcse(differences)
            paired.append({'scenario':case,'outcome':outcome,'direction':'grouped robust minus random robust',
                           'difference':average,'mcse':se,'complete_blocks':len(complete),
                           'planned_blocks':spec.get('replications',plan['replications'])})
    return {'schema':'independent_final_campaign_audit_v1','phase':plan['phase'],
            'source_sha256':sources,'primary':result,'legacy_reference':reference,'paired_complete_blocks':paired,
            'planned_blocks':sum(s.get('replications',plan['replications']) for s in specs.values()),
            'saved_blocks':len(blocks),'complete_blocks':sum(r['complete_block'] for r in blocks.values())},rows


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--run-dir',action='append',required=True)
    p.add_argument('--source-root',default='.');p.add_argument('--out',required=True);a=p.parse_args(argv)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    report,rows=audit(a.plan,a.run_dir,a.source_root)
    (out/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    import csv
    with (out/'intervals.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:report[k] for k in ('planned_blocks','saved_blocks','complete_blocks')}))


if __name__=='__main__':main()
