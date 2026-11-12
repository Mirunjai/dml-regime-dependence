"""Registered exploratory reconstruction and sensitivity checks; never production.

One world per condition/replication; all four cells and labelled sensitivity
variants reuse that world's cross-fitted residuals. Truth only scores intervals.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,sys,time
from dataclasses import asdict
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from importlib.metadata import version
import numpy as np
from research.week2_completion.dgp import Config,build_world,STREAMS
from research.week2_completion.dml import make_folds,crossfit,estimate,audit_folds
from research.mirun_proposals.variance_alternatives import alternatives


def digest_world(d):
    h=hashlib.sha256()
    for name in ('X','D','Y','t0','sig','z','U_t','rid_t'):
        a=np.ascontiguousarray(d[name]);h.update(name.encode());h.update(str(a.shape).encode());h.update(a.dtype.str.encode());h.update(a.tobytes())
    h.update(json.dumps(d['cluster_memberships']).encode())
    return h.hexdigest()


def run_one(job):
    spec,rep=job;cfg=Config(**{**spec['config'],'seed':spec['seed0']+rep})
    started=time.perf_counter();cells=[];sens=[];diagnostics={};world=None
    try:
        d=build_world(cfg);world=digest_world(d)
        memberships=d['cluster_memberships']
        diagnostics={'exposed_event_share':float(np.mean(d['exposed'])),
          'multi_membership_events':sum(len(m)>1 for m in memberships),
          'mean_idiosyncratic_squared_return':float(np.mean((d['sig']*d['z'])**2)),
          'max_abs_idiosyncratic_return':float(np.max(np.abs(d['sig']*d['z']))),
          'nonfinite_sigma':int((~np.isfinite(d['sig'])).sum()),'nonpositive_sigma':int((d['sig']<=0).sum())}
        for scheme in ('random','grouped'):
            try:
                fold=make_folds(scheme,memberships,spec['folds'],np.random.default_rng(cfg.seed+(scheme=='grouped')))
                yt,dt=crossfit(d['Y'],d['D'],d['X'],fold,spec['folds'],cfg.seed)
                fit=estimate(yt,dt,memberships,allow_invalid_multiway=True)
                for variance,key in [('naive','se_naive'),('robust','se_multiway')]:
                    se=fit[key];err=fit['multiway_error'] if variance=='robust' else None
                    cells.append({'cell':f'{scheme}_xfit__{variance}_var','status':'failed' if err else 'ok',
                       'estimate':fit['tau'],'lower':fit['tau']-fit['critical_value']*se if se is not None else None,
                       'upper':fit['tau']+fit['critical_value']*se if se is not None else None,'se':se,'error':err,
                       'fold_ids':fold.tolist(),'fold_diagnostics':audit_folds(d,fold)})
                a=alternatives(yt,dt,memberships)
                sens.append({'scheme':scheme,'estimate':a['tau'],'variants':a['variants'],'decomposition':a['decomposition'],
                    'scope':'Secondary heuristic critical values/variance; not approved replacements for primary inference'})
            except Exception as exc:
                for variance in ('naive','robust'):
                    if not any(c['cell']==f'{scheme}_xfit__{variance}_var' for c in cells):
                        cells.append({'cell':f'{scheme}_xfit__{variance}_var','status':'failed','estimate':None,'lower':None,'upper':None,'se':None,'error':repr(exc)})
    except Exception as exc:
        cells=[{'cell':f'{s}_xfit__{v}_var','status':'failed','estimate':None,'lower':None,'upper':None,'se':None,'error':repr(exc)} for s in ('random','grouped') for v in ('naive','robust')]
    return {'schema_version':1,'evidence_class':'EXPLORATORY','scenario':spec['id'],'replication':rep,
      'seed':cfg.seed,'world_sha256':world,'config':asdict(cfg),'truth':cfg.tau,'confidence_level':.95,
      'rng_addresses':{name:{'entropy':cfg.seed,'spawn_key':[i]} for i,name in enumerate(STREAMS)},
      'cells':cells,'sensitivity':sens,'diagnostics':diagnostics,'seconds':time.perf_counter()-started}


def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,sort_keys=True,allow_nan=False)+'\n');tmp.replace(path)


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--effect',type=float,required=True);p.add_argument('--workers',type=int,default=2);a=p.parse_args(argv)
    plan=json.loads(a.plan.read_text());assert plan['evidence_class']=='EXPLORATORY'
    a.output.mkdir(parents=True,exist_ok=False)
    scenarios=[s for s in plan['scenarios'] if s['config']['tau']==a.effect]
    sources={}
    for directory in ('research/week2_completion','research/mirun_proposals'):
        for f in sorted(Path(directory).glob('*.py')):sources[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    sources['validation_driver.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    atomic(a.output/'manifest.json',{'plan':plan,'selected_scenarios':[s['id'] for s in scenarios],
       'effect':a.effect,'source_sha256':sources,'plan_sha256':hashlib.sha256(a.plan.read_bytes()).hexdigest(),
       'python':sys.version,'platform':platform.platform(),'packages':{n:version(n) for n in ('numpy','scipy','scikit-learn')},
       'purpose':'Fresh reviewer reconstruction and exploratory validation; no production approval'})
    jobs=[(s,r) for s in scenarios for r in range(plan['replications'])]
    started=time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for count,record in enumerate(pool.map(run_one,jobs,chunksize=1),1):
            atomic(a.output/record['scenario']/f"rep_{record['replication']:06d}.json",record)
            if count%25==0:print(json.dumps({'saved':count,'planned':len(jobs),'elapsed':time.perf_counter()-started}),flush=True)
    files={str(f.relative_to(a.output)):hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output.rglob('*.json')}
    atomic(a.output/'completion.json',{'complete':True,'blocks':len(jobs),'elapsed_seconds':time.perf_counter()-started,'files_sha256':files})

if __name__=='__main__':main()
