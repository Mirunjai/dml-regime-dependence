"""Apply the frozen acceptance and comparison rules to independently audited rows.

Uses no estimator/DGP. Reused seeds are paired within a condition or a declared
matched contrast, never pooled as independent Monte Carlo observations.
"""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
from statistics import NormalDist
import numpy as np
from scipy.stats import binomtest


def wilson(k,n,confidence=.95):
    if not n:return [None,None]
    z=NormalDist().inv_cdf((1+confidence)/2); p=k/n; d=1+z*z/n
    mid=(p+z*z/(2*n))/d; half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [mid-half,mid+half]


def paired(a,b,seed):
    d=np.asarray(b,float)-np.asarray(a,float); n=len(d)
    if n<2:return {'n':n,'difference':None,'mcse':None,'percentile95':None}
    rng=np.random.default_rng(seed)
    # World-level paired resampling, fixed budget. Never resample cells separately.
    boot=d[rng.integers(0,n,size=(4000,n))].mean(axis=1)
    return {'n':n,'difference':float(d.mean()),'mcse':float(d.std(ddof=1)/np.sqrt(n)),
            'percentile95':np.quantile(boot,[.025,.975]).tolist()}


def summarize(plan_path,audit_path,interval_path,structure_path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    plan=json.loads(Path(plan_path).read_text()); audit=json.loads(Path(audit_path).read_text())
    structure=json.loads(Path(structure_path).read_text()); specs={s['id']:s for s in plan['scenarios']}
    by={}
    with Path(interval_path).open() as f:
        for r in csv.DictReader(f):
            for field in ('estimate','lower','upper','truth'):
                r[field]=float(r[field]) if r[field] not in ('','None') else None
            r['replication']=int(r['replication']);by.setdefault((r['scenario'],r['cell']),{})[r['replication']]=r
    summaries=[]; controls=[]
    for frozen in audit['primary']['summaries']:
        r=dict(frozen);case=r['scenario']; rows=list(by[case,r['cell']].values()); valid=[v for v in rows if v['status']=='ok']
        estimates=np.array([v['estimate'] for v in valid]); n=len(valid)
        sd=float(estimates.std(ddof=1)) if n>1 else None
        r['estimate_sd']=sd; r['coverage_wilson90']=wilson(r['covered'],n,.9)
        r['rejection_wilson90']=wilson(r['rejected_zero'],n,.9)
        r.update(K=specs[case]['config']['n_regimes'],density=specs[case]['config']['density'],gamma=specs[case]['config']['gamma'])
        if specs[case]['role']=='independent_control':
            band=plan['control_acceptance']['coverage_band'];ci=r['coverage_wilson90']
            tests={'complete':r['failed']==r['missing']==0,'coverage_equivalence':n>0 and ci[0]>=band[0] and ci[1]<=band[1],
                   'bias':sd is not None and abs(r['bias'])<=.1*sd}
            if r['truth']==0:
                band=plan['control_acceptance']['null_size_band'];ci=r['rejection_wilson90']
                tests['size_equivalence']=n>0 and ci[0]>=band[0] and ci[1]<=band[1]
            controls.append({'scenario':case,'cell':r['cell'],'tests':tests,'passed':all(tests.values()),
                             'coverage':r['coverage95'],'coverage_wilson90':r['coverage_wilson90'],
                             'rejection_wilson90':r['rejection_wilson90'],'bias_over_sd':r['bias']/sd if sd else None})
        summaries.append(r)
    summary_by={(r['scenario'],r['cell']):r for r in summaries}
    random='random_xfit__robust_var';grouped='grouped_xfit__robust_var';focal=[]
    for index,K in enumerate((4,16)):
        case=f'main_K{K}_d0.5_g1_tau1'; null=case[:-1]+'0';aa=by[case,random];bb=by[case,grouped]
        ids=[i for i in sorted(aa.keys()&bb.keys()) if all(by[case,c][i]['status']=='ok' for c in ('random_xfit__naive_var',random,'grouped_xfit__naive_var',grouped))]
        def covered(r):return int(r['lower']<=r['truth']<=r['upper'])
        a=[covered(aa[i]) for i in ids]; b=[covered(bb[i]) for i in ids]
        plus=sum(y>x for x,y in zip(a,b));minus=sum(y<x for x,y in zip(a,b));discordant=plus+minus
        p=float(binomtest(plus,discordant,.5).pvalue) if discordant else 1.
        ra=summary_by[case,random]['coverage95'];rb=summary_by[case,grouped]['coverage95']
        na=summary_by[null,random]['empirical_size'];nb=summary_by[null,grouped]['empirical_size']
        focal.append({'scenario':case,'K':K,'paired_coverage':paired(a,b,2026111200+index),
                      'discordant_grouped_only':plus,'discordant_random_only':minus,'exact_p':p,
                      'coverage_calibration_improvement':abs(ra-.95)-abs(rb-.95),
                      'null_size_loss_worsening':abs(nb-.05)-abs(na-.05)})
    order=sorted(range(2),key=lambda i:focal[i]['exact_p']);previous=0.
    for rank,i in enumerate(order):
        previous=max(previous,min(1.,focal[i]['exact_p']*(2-rank)));focal[i]['holm_p']=previous
        focal[i]['registered_material_benefit']=(focal[i]['coverage_calibration_improvement']>=.02 and previous<.05 and focal[i]['null_size_loss_worsening']<=.01)
    matches=[]
    for kind in ['pair_density','exposed_share']:
        for gamma in (0,1):
            for tau in (0,1):
                left=f'h4_pair_density_K4_g{gamma}_tau{tau}' if kind=='pair_density' else f'main_K4_d0.5_g{gamma}_tau{tau}'
                right=f'main_K16_d0.5_g{gamma}_tau{tau}' if kind=='pair_density' else f'h4_exposed_share_K16_g{gamma}_tau{tau}'
                for cell in (random,grouped):
                    aa=by[left,cell];bb=by[right,cell];ids=[i for i in sorted(aa.keys()&bb.keys()) if aa[i]['status']==bb[i]['status']=='ok']
                    a=[int(aa[i]['lower']<=tau<=aa[i]['upper']) for i in ids];b=[int(bb[i]['lower']<=tau<=bb[i]['upper']) for i in ids]
                    matches.append({'match':kind,'gamma':gamma,'tau':tau,'cell':cell,'left':left,'right':right,
                                    'direction':'K16 minus K4 coverage','paired':paired(a,b,2026111300+len(matches))})
    slopes={}
    for K in (4,16):
        grid=[r for r in structure['scaling'] if r['K']==K]
        slopes[str(K)]=float(np.polyfit(np.log([r['n'] for r in grid]),np.log([r['shared_pairs']['mean'] for r in grid]),1)[0])
    monotone={}
    for K in (4,16):
        grid=sorted([r for r in structure['grid'] if r['K']==K and r['density'] in (.25,.5,.75)],key=lambda r:r['density'])
        monotone[str(K)]=all(all(b[key]['mean']>a[key]['mean'] for a,b in zip(grid,grid[1:])) for key in ['pair_density','average_common_shock_correlation'])
    result={'schema':'registered_final_interpretation_v1','planned_blocks':audit['planned_blocks'],'saved_blocks':audit['saved_blocks'],
            'complete_blocks':audit['complete_blocks'],'interval_rows':len(summaries) and sum(r['planned'] for r in summaries),
            'scenarios':len(specs),'control_cells':controls,'controls_all_passed':all(c['passed'] for c in controls),
            'focal_H3':focal,'H4':matches,'structural_scaling_slopes':slopes,'density_ordering_passed':monotone,
            'structure_matches':structure['matches'],'summaries':summaries,
            'scope':'Finite registered grid; primary component-CR2 assumption excludes calendar common factors. Factor-on stress reported separately. No new theorem or estimator novelty.',
            'inference_rule':'Coverage closer to .95 and null size closer to .05 define calibration; interval width/power alone never establish benefit.'}
    (out/'interpretation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    with (out/'summaries.csv').open('w') as f:
        fields=list(summaries[0]); w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(summaries)
    print(json.dumps({k:result[k] for k in ['scenarios','saved_blocks','complete_blocks','controls_all_passed','focal_H3']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--audit',required=True);p.add_argument('--intervals',required=True);p.add_argument('--structure',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();summarize(a.plan,a.audit,a.intervals,a.structure,a.out)
