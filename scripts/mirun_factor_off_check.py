"""EXPLORATORY: does the shared calendar factor (sd_factor=.5) explain undercoverage? Same seeds as the
failure scan (30000+rep), gamma=1, tau=1, d=.5; ONLY sd_factor differs (0 vs .5 from the scan). Unmodified pipeline."""
import json, sys, time
from dataclasses import replace
import numpy as np
from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import run_dml

def main(out, K, reps, budget):
    t0, res = time.perf_counter(), []
    for rep in range(reps):
        if time.perf_counter() - t0 > budget: break
        cfg = replace(Config(), n_regimes=K, density=.5, gamma=1.0, tau=1.0, sd_factor=0.0, seed=30000 + rep)
        rows, _ = run_dml(build_world(cfg), n_folds=5, seed=cfg.seed)
        res.append({(r["folds"], r["variance"]): (r["status"], r["tau"], r["lo"], r["hi"]) for r in rows})
    keys = [("random","naive"),("random","multiway"),("grouped","naive"),("grouped","multiway")]
    table = {}
    for k in keys:
        ok = [r[k] for r in res if r[k][0] == "ok"]
        hit = np.array([a[2] <= 1 <= a[3] for a in ok]); t = np.array([a[1] for a in ok])
        table[f"{k[0]}/{k[1]}"] = {"valid": len(ok), "failed": len(res) - len(ok), "coverage": float(hit.mean()),
                                   "mcse": float(np.sqrt(hit.mean()*(1-hit.mean())/len(hit))), "sd_tau": float(t.std(ddof=1))}
    open(out, "x").write(json.dumps({"purpose": "exploratory factor-off check", "K": K, "reps": len(res), "table": table}, indent=1))
    print(K, len(res), {k: (round(v["coverage"],3), round(v["sd_tau"],3)) for k, v in table.items()})

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]))
