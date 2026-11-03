"""Reproducible Gate 2 diagnostics for the Week 2 comparison DGP."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from .dgp import Config, build_world

def overlap_density(d):
    return float(np.mean(d["exposed"]))

def pair_density(memberships):
    n=len(memberships); pairs=0
    sets=[set(m) for m in memberships]
    for i in range(n):
        for j in range(i+1,n):
            if sets[i] and sets[j] and sets[i].intersection(sets[j]): pairs+=1
    return pairs/(n*(n-1)/2) if n>1 else 0.

def one_seed(seed, density=.5, K=4, gamma=1., persistence=.9, tau=1.):
    d=build_world(Config(seed=seed,density=density,n_regimes=K,gamma=gamma,persistence=persistence,tau=tau))
    r=d["sig"]*d["z"]
    return {
        "seed":seed,"gamma":gamma,"density_setting":density,"K":K,
        "realized_overlap_density":overlap_density(d),
        "pair_density":pair_density(d["cluster_memberships"]),
        "mean_r2":float(np.mean(r*r)),
        "max_abs_return":float(np.max(np.abs(r))),
        "n_nan":int(np.isnan(r).sum()),"n_inf":int(np.isinf(r).sum()),
        "n_regime_memberships":int(sum(len(m) for m in d["cluster_memberships"])),
        "n_events_multi_regime":int(sum(len(m)>1 for m in d["cluster_memberships"])),
        "n_exposed":int(d["exposed"].sum()),
        "treatment_rate":float(d["D"].mean()),
        "corr_D_Uwin":float(np.corrcoef(d["D"],d["U_win"])[0,1]) if np.std(d["U_win"])>0 else None,
        "corr_sigma_abs_U":float(spearmanr(d["sig_event"][d["exposed"]],np.abs(d["U_win"][d["exposed"]])).statistic) if d["exposed"].sum()>2 else None,
        "true_tau":tau,
    }

def run_gate2(seeds=range(50), out_path="results/week2_gate2.json"):
    records=[one_seed(int(s)) for s in seeds]
    # Paired same-seed comparison makes the gamma ablation reproducible.
    gamma_pairs=[]
    for s in range(30):
        a=build_world(Config(seed=s,gamma=0.))
        b=build_world(Config(seed=s,gamma=1.))
        gamma_pairs.append({"seed":s,"same_X":bool(np.array_equal(a["X"],b["X"])),
                            "same_dates":bool(np.array_equal(a["t0"],b["t0"])),
                            "same_U":bool(np.array_equal(a["U_t"],b["U_t"])),
                            "treatment_rate_gamma0":float(a["D"].mean()),
                            "treatment_rate_gamma1":float(b["D"].mean())})
    result={"schema_version":1,"purpose":"diagnostic evidence; not a Gate 2 pass decision",
            "default_gamma_records":records,"gamma_ablation":gamma_pairs,
            "summary":{"mean_overlap":float(np.mean([r["realized_overlap_density"] for r in records])),
                       "mean_pair_density":float(np.mean([r["pair_density"] for r in records])),
                       "mean_r2":float(np.mean([r["mean_r2"] for r in records])),
                       "events_touching_multiple_regimes":int(sum(r["n_events_multi_regime"] for r in records))}}
    path=Path(out_path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,allow_nan=False))
    return result
