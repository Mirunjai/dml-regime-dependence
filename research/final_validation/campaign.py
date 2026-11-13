"""Source-pinned, separately labelled DML validation with raw four-cell worlds."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import time

import numpy as np

from research.week2_completion.dgp import Config, build_world, STREAMS
from research.week2_completion.dml import make_folds, estimate, audit_folds
from research.final_validation.inference import component_cr2
from research.final_validation.learners import residualize


def atomic(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,sort_keys=True,allow_nan=False)+'\n')
    temporary.replace(path)


def world_digest(world):
    digest=hashlib.sha256()
    for name in ('X','D','Y','t0','idx','sig','z','rid_t','U_t'):
        value=np.ascontiguousarray(world[name])
        digest.update(name.encode());digest.update(value.dtype.str.encode())
        digest.update(str(value.shape).encode());digest.update(value.tobytes())
    digest.update(json.dumps(world['cluster_memberships']).encode())
    return digest.hexdigest()


def failed_cell(scheme, variance, error):
    return {'cell':f'{scheme}_xfit__{variance}_var','status':'failed',
            'estimate':None,'lower':None,'upper':None,'se':None,'error':str(error)}


def run_one(job):
    spec,rep=job;seed=int(spec['seed0'])+rep
    config=Config(**{**spec['config'],'seed':seed})
    started=time.perf_counter();cells=[];reference=[];fingerprint=None;diagnostics={}
    try:
        world=build_world(config);fingerprint=world_digest(world)
        memberships=world['cluster_memberships']
        diagnostics={'exposed_event_share':float(np.mean(world['exposed'])),
                     'multiple_membership_events':sum(len(m)>1 for m in memberships),
                     'nonfinite_sigma':int((~np.isfinite(world['sig'])).sum()),
                     'nonpositive_sigma':int((world['sig']<=0).sum())}
        for scheme in ('random','grouped'):
            try:
                fold=make_folds(scheme,memberships,spec['folds'],np.random.default_rng(seed+(scheme=='grouped')))
                yt,dt=residualize(world,fold,spec['folds'],seed,learner=spec['learner'])
                fit=estimate(yt,dt,memberships,allow_invalid_multiway=True)
                naive={'cell':f'{scheme}_xfit__naive_var','status':'ok','estimate':fit['tau'],
                       'lower':fit['tau']-fit['critical_value']*fit['se_naive'],
                       'upper':fit['tau']+fit['critical_value']*fit['se_naive'],
                       'se':fit['se_naive'],'error':None,'method':'HC0_normal',
                       'fold_ids':fold.tolist(),'fold_audit':audit_folds(world,fold)}
                cells.append(naive)
                error=fit['multiway_error'];se=fit['se_multiway']
                reference.append({'cell':f'{scheme}_xfit__robust_var',
                    'status':'failed' if error else 'ok','estimate':fit['tau'],
                    'lower':fit['tau']-fit['critical_value']*se if se is not None else None,
                    'upper':fit['tau']+fit['critical_value']*se if se is not None else None,
                    'se':se,'error':error,'method':'legacy_overlap_CR0_normal'})
                try:
                    corrected=component_cr2(yt,dt,memberships)
                    np.testing.assert_allclose(corrected['estimate'],fit['tau'],rtol=1e-13,atol=1e-13)
                    cells.append({'cell':f'{scheme}_xfit__robust_var','status':'ok','error':None,
                                  'fold_ids':fold.tolist(),'fold_audit':audit_folds(world,fold),**corrected})
                except Exception as exc:
                    cells.append(failed_cell(scheme,'robust',repr(exc)))
            except Exception as exc:
                for variance in ('naive','robust'):
                    if not any(c['cell']==f'{scheme}_xfit__{variance}_var' for c in cells):
                        cells.append(failed_cell(scheme,variance,repr(exc)))
    except Exception as exc:
        cells=[failed_cell(s,v,repr(exc)) for s in ('random','grouped') for v in ('naive','robust')]
    block=f"{spec['id']}::rep_{rep:06d}"
    for cell in cells+reference:
        cell['world_sha256']=fingerprint;cell['block_id']=block
    return {'schema':'final_validation_v1','scenario':spec['id'],'replication':rep,
            'seed':seed,'config':asdict(config),'learner':spec['learner'],'folds':spec['folds'],
            'truth':config.tau,'confidence_level':.95,'world_sha256':fingerprint,
            'block_id':block,'complete_block':len(cells)==4 and all(c['status']=='ok' for c in cells),
            'cells':cells,'reference_cells':reference,'diagnostics':diagnostics,
            'rng_addresses':{name:{'entropy':seed,'spawn_key':[i]} for i,name in enumerate(STREAMS)},
            'elapsed_seconds':time.perf_counter()-started}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=2);parser.add_argument('--scenario',action='append')
    args=parser.parse_args(argv)
    if args.workers<1:parser.error('workers must be positive')
    plan=json.loads(args.plan.read_text());selected=[s for s in plan['scenarios'] if not args.scenario or s['id'] in args.scenario]
    if not selected or (args.scenario and set(args.scenario)!={s['id'] for s in selected}):parser.error('Unknown or empty scenario selection')
    args.out.mkdir(parents=True,exist_ok=False)
    source_root=Path(__file__).resolve().parents[2]
    paths=list((source_root/'research/final_validation').glob('*.py'))+list((source_root/'research/week2_completion').glob('*.py'))
    manifest={'plan':plan,'plan_sha256':hashlib.sha256(args.plan.read_bytes()).hexdigest(),
              'selected_scenarios':[s['id'] for s in selected],
              'source_sha256':{str(p.relative_to(source_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'python':platform.python_version(),'packages':{n:version(n) for n in ('numpy','scipy','scikit-learn')},
              'evidence_class':plan['phase']}
    atomic(args.out/'manifest.json',manifest)
    jobs=[(s,rep) for s in selected for rep in range(s.get('replications',plan['replications']))]
    started=time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i,record in enumerate(pool.map(run_one,jobs,chunksize=1),1):
            atomic(args.out/record['scenario']/f"rep_{record['replication']:06d}.json",record)
            if i%20==0:print(json.dumps({'saved':i,'planned':len(jobs),'seconds':time.perf_counter()-started}),flush=True)
    hashes={str(p.relative_to(args.out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.rglob('*.json')}
    atomic(args.out/'completion.json',{'complete':True,'worlds':len(jobs),'files_sha256':hashes,'seconds':time.perf_counter()-started})


if __name__=='__main__':
    main()
