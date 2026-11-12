"""Independent, standard-library audit of exploratory four-cell blocks.

Retains missing/failed denominators; paired contrasts require complete FOUR-cell
blocks. Source/manifest hashes are checked before any headline metric is reported.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path
from src.evaluation.verification import CELLS,audit_results,finite,mean_mcse
from src.evaluation.week3_audit import read_json,write_json,provenance,save_source_snapshot


def audit(plan_path,run_dirs,source_root=None):
    plan=read_json(plan_path);n=plan['replications'];specs={s['id']:s for s in plan['scenarios']}
    paths=[Path(plan_path)];rows=[];sens=[];blocks={};source_checks=[];diags=[]
    source_root=Path(source_root or Path(__file__).resolve().parents[1])
    reference_sources=None
    selected=set()
    for directory in map(Path,run_dirs):
        manifest_path=directory/'manifest.json';manifest=read_json(manifest_path);paths.append(manifest_path)
        if manifest['plan']!=plan or manifest['plan_sha256']!=hashlib.sha256(Path(plan_path).read_bytes()).hexdigest():
            raise ValueError('Run manifest plan differs from registered plan')
        sources=manifest['source_sha256']
        if reference_sources is not None and sources!=reference_sources:
            raise ValueError('Mixed producer source versions')
        reference_sources=sources
        for name,digest in sources.items():
            p=source_root/('compute-tools/final-validation/validation_driver.py' if name=='validation_driver.py' else name)
            if not p.resolve().is_relative_to(source_root.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
                raise ValueError('Producer source fingerprint mismatch')
        if len(manifest['selected_scenarios'])!=len(set(manifest['selected_scenarios'])) or selected.intersection(manifest['selected_scenarios']):
            raise ValueError('Duplicate selected scenario')
        selected.update(manifest['selected_scenarios'])
        completion=read_json(directory/'completion.json')
        paths.append(directory/'completion.json')
        listed=set(completion['files_sha256'])
        actual={str(p.relative_to(directory)) for p in directory.rglob('*.json') if p.name!='completion.json'}
        if listed!=actual:raise ValueError('Completion fingerprint file set mismatch')
        expected={'manifest.json'}|{str(p.relative_to(directory)) for name in manifest['selected_scenarios'] for p in (directory/name).glob('rep_*.json')}
        if actual!=expected:raise ValueError('Unexpected file outside selected scenarios')
        count_before=len(blocks)
        if not completion['complete']:raise ValueError('Incomplete producer completion marker')
        for name,digest in completion['files_sha256'].items():
            p=(directory/name).resolve()
            if not p.is_relative_to(directory.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
                raise ValueError('Completion fingerprint mismatch')
        for name in manifest['selected_scenarios']:
            spec=specs[name]
            for path in sorted((directory/name).glob('rep_*.json')):
                r=read_json(path);rep=r['replication'];seed=spec['seed0']+rep
                if type(rep) is not int or not 0<=rep<n or path.name!=f'rep_{rep:06d}.json':raise ValueError('Unplanned replication')
                if (r['scenario']!=name or r['seed']!=seed or r['config']!={**spec['config'],'seed':seed}
                    or r['truth']!=spec['config']['tau'] or r['evidence_class']!='EXPLORATORY' or r['confidence_level']!=.95):raise ValueError('Block config/identity mismatch')
                if any(c['status']=='ok' for c in r['cells']) and (not isinstance(r['world_sha256'],str) or len(r['world_sha256'])!=64 or any(ch not in '0123456789abcdef' for ch in r['world_sha256'])):
                    raise ValueError('Missing world fingerprint for successful block')
                key=name,str(rep)
                if key in blocks:raise ValueError('Duplicate block across inputs')
                if len(r['cells'])!=4 or {c['cell'] for c in r['cells']}!=set(CELLS):raise ValueError('Expected four unique cells')
                blocks[key]=r
                for c in r['cells']:
                    rows.append(dict(scenario=name,replication=str(rep),cell=c['cell'],panel_id=r['world_sha256'] or f'failed:{name}:{rep}',truth=r['truth'],confidence_level=.95,status=c['status'],estimate=c['estimate'],lower=c['lower'],upper=c['upper'],error=c['error']))
                if len({s['scheme'] for s in r['sensitivity']})!=len(r['sensitivity']):raise ValueError('Duplicate sensitivity scheme')
                for s in r['sensitivity']:
                    if s['scheme'] not in ('random','grouped'):raise ValueError('Unknown sensitivity scheme')
                    for variant,v in s['variants'].items():
                        if variant not in ('cr0_t','cr1reg_t'):continue
                        valid=v is not None and v['se'] is not None and v['crit'] is not None
                        if valid:
                            estimate,se,crit=(finite(x) for x in (s['estimate'],v['se'],v['crit']))
                            valid=se>0 and crit>0
                        sens.append({'scenario':name,'replication':str(rep),'scheme':s['scheme'],'variant':variant,'valid':valid,'estimate':s['estimate'],'se':v['se'] if valid else None,'critical':v['crit'] if valid else None,'truth':r['truth']})
                diags.append({'scenario':name,'replication':rep,**r['diagnostics']})
                paths.append(path)
        if completion['blocks']!=len(blocks)-count_before:raise ValueError('Completion block count mismatch')
        source_checks.append({'directory':str(directory),'source_sha256':manifest['source_sha256'],'packages':manifest['packages'],'completion_blocks':completion['blocks']})
    canonical_plan={'schema_version':1,'evidence_kind':'simulation','failure_policy':'report','confidence_level':.95,'scenarios':[{'id':s['id'],'truth':s['config']['tau'],'role':'primary','replication_ids':list(range(n))} for s in specs.values()]}
    report=audit_results(rows,canonical_plan)
    # This final-week audit reports paired contrasts only from complete four-cell blocks.
    report.pop('comparisons',None)
    by={(r['scenario'],r['cell']):r for r in report['summaries']}
    for s in report['summaries']:
        cellrows=[r for r in rows if r['scenario']==s['scenario'] and r['cell']==s['cell'] and r['status']=='ok']
        s['covered']=sum(r['lower']<=s['truth']<=r['upper'] for r in cellrows)
        s['rejected_zero']=sum(r['upper']<0 or r['lower']>0 for r in cellrows)
        s['independent_unit']=f'whole simulated world; {n} planned seeds within scenario, not firms'
    comparisons=[]
    for name,spec in specs.items():
        complete=[b for (case,_),b in blocks.items() if case==name and all(c['status']=='ok' for c in b['cells'])]
        for outcome in ['coverage','empirical_size' if spec['config']['tau']==0 else 'power']:
            differences=[]
            for b in complete:
                cells={c['cell']:c for c in b['cells']}
                def hit(c):return c['lower']<=b['truth']<=c['upper'] if outcome=='coverage' else c['upper']<0 or c['lower']>0
                differences.append(int(hit(cells[CELLS[3]]))-int(hit(cells[CELLS[1]])))
            d,se=mean_mcse(differences)
            comparisons.append({'scenario':name,'outcome':outcome,'direction':'grouped robust minus random robust','difference':d,'mcse':se,'complete_four_cell_blocks':len(complete),'planned_blocks':n,'excluded_blocks':n-len(complete)})
    sensitivity=[]
    for name in specs:
        for scheme in ('random','grouped'):
            for variant in ('cr0_t','cr1reg_t'):
                valid=[s for s in sens if s['scenario']==name and s['scheme']==scheme and s['variant']==variant and s['valid']]
                coverage=[abs(s['estimate']-s['truth'])<=s['critical']*s['se'] for s in valid]
                rejects=[abs(s['estimate'])>s['critical']*s['se'] for s in valid]
                def rate(hits):
                    if not hits:return None,None
                    p=sum(hits)/len(hits);return p,math.sqrt(p*(1-p)/len(hits))
                p,se=rate(coverage);q,qse=rate(rejects)
                sensitivity.append({'scenario':name,'scheme':scheme,'variant':variant,'planned':n,'valid':len(valid),'undefined_or_missing':n-len(valid),'coverage':p,'coverage_mcse':se,'rejection_rate':q,'rejection_mcse':qse,'rejection_kind':'size' if specs[name]['config']['tau']==0 else 'power','scope':'EXPLORATORY heuristic, never replaces reference method'})
    report.update(evidence_class='EXPLORATORY',registered_plan=plan,complete_block_comparisons=comparisons,sensitivity=sensitivity,source_checks=source_checks,diagnostics=diags,
        audit_limitations=['No production approval or primary-method selection from results.','Cross-scenario outcomes reuse seeds and must not be pooled as independent replicates.','Reconstructed controls do not authenticate the missing original archive.','Intervals describe one DGP family; four-cell runs do not settle all-source dependence or dense asymptotic validity.'])
    report['provenance']=provenance(paths,extra_sources=[__file__])
    return report,rows,canonical_plan


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--run-dir',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    report,rows,plan=audit(a.plan,a.run_dir);a.output.mkdir(parents=True,exist_ok=False)
    write_json(a.output/'audit.json',report);write_json(a.output/'plan.json',plan)
    for filename,data in [('intervals.csv',rows),('summaries.csv',report['summaries']),('paired_complete_blocks.csv',report['complete_block_comparisons']),('sensitivity.csv',report['sensitivity'])]:
        with (a.output/filename).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    report['verifier_source_archive']=save_source_snapshot(a.output,report['provenance'],extra_sources=[__file__]);write_json(a.output/'audit.json',report)
    print(json.dumps({'raw_rows':len(rows),'complete':report['all_records_successful'],'cells':len(report['summaries'])}))
    return 0 if report['all_records_successful'] else 2

if __name__=='__main__':raise SystemExit(main())
