"""Run Week 2 Gate 2 diagnostics and the gamma ablation Monte Carlo."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
from .dgp import Config, build_world
from .dml import run_dml, CELLS
from .validation import run_gate2

def monte_carlo(reps, gamma, tau, density, K, n=400, T=260, H=5, folds=5, seed0=20000):
    cells={f"{f}/{v}":[] for f,v in CELLS}; failures=[]
    started=time.perf_counter()
    for r in range(reps):
        seed=seed0+r
        try:
            d=build_world(Config(n=n,T=T,H=H,density=density,n_regimes=K,gamma=gamma,tau=tau,seed=seed))
            rows,_=run_dml(d,n_folds=folds,seed=seed)
            for row in rows: cells[f"{row['folds']}/{row['variance']}"].append(row)
        except Exception as exc:
            failures.append({"replication":r,"seed":seed,"error_type":type(exc).__name__,"message":str(exc)})
    summaries={}
    for name,rs in cells.items():
        if not rs: summaries[name]={"successful_reps":0}; continue
        est=np.array([x["tau"] for x in rs]); lo=np.array([x["lo"] for x in rs]); hi=np.array([x["hi"] for x in rs])
        cover=(lo<=tau)&(tau<=hi); size=((lo>0)|(hi<0)) if tau==0 else None
        p=float(cover.mean())
        summaries[name]={"successful_reps":len(rs),"coverage":p,
            "mc_se_coverage":float(np.sqrt(p*(1-p)/len(rs))),
            "bias":float(est.mean()-tau),"rmse":float(np.sqrt(np.mean((est-tau)**2))),
            "mean_interval_width":float(np.mean(hi-lo)),
            "empirical_size":float(size.mean()) if size is not None else None,
            "mc_se_size":float(np.sqrt(size.mean()*(1-size.mean())/len(rs))) if size is not None else None}
    return {"reps_requested":reps,"reps_failed":len(failures),"failure_rate":len(failures)/reps,
            "gamma":gamma,"tau":tau,"density_setting":density,"K":K,"seconds":time.perf_counter()-started,
            "results":summaries,"failures":failures}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reps",type=int,default=20)
    ap.add_argument("--gamma-values",type=float,nargs="+",default=[0.,1.])
    ap.add_argument("--tau-values",type=float,nargs="+",default=[1.,0.])
    ap.add_argument("--density",type=float,default=.5)
    ap.add_argument("--K",type=int,default=4)
    ap.add_argument("--n",type=int,default=400)
    ap.add_argument("--T",type=int,default=260)
    ap.add_argument("--H",type=int,default=5)
    ap.add_argument("--folds",type=int,default=5)
    ap.add_argument("--seed",type=int,default=20000)
    ap.add_argument("--out",default="results/week2_mc.json")
    args=ap.parse_args()
    if args.reps<1: ap.error("--reps must be >=1")
    run_gate2(range(50), "results/week2_gate2.json")
    all_runs=[]
    for gamma in args.gamma_values:
        for tau in args.tau_values:
            all_runs.append(monte_carlo(args.reps,gamma,tau,args.density,args.K,args.n,args.T,args.H,args.folds,args.seed))
    payload={"schema_version":1,"note":"Pilot unless reps and design are team-approved; grouped-fold failures are retained.",
             "runs":all_runs}
    p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,indent=2,allow_nan=False))
    print(json.dumps({"output":str(p),"runs":len(all_runs),
                      "total_failures":sum(x["reps_failed"] for x in all_runs)},indent=2))
if __name__=="__main__": main()
