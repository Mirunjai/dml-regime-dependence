"""(1) toy run of all four DML cells + runtime; (2) baseline sanity MC (no dependence); (3) small PIPELINE-CHECK MC under dependence
(manipulation check: does dependence bite?  NOT for tuning criteria).  usage: python mc_run.py REPS"""
import sys, json, time, numpy as np
from dgp import *; from dml import *
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
out = {}
# toy run
d = simulate_dgp(Config(seed=7, density=0.5, n_regimes=4))
t = time.perf_counter(); rows, rt = run_dml(d, seed=7); tot = time.perf_counter() - t
out["toy"] = dict(rows=[{k: (float(v) if not isinstance(v, str) else v) for k, v in r.items()} for r in rows], runtime_sec_total=tot, runtime_by_scheme=rt)
json.dump(out, open("results/mc_results.json", "w"), indent=1)

def mc(name, **kw):
    t0 = time.perf_counter(); recs = {c: [] for c in CELLS}; tm = []
    for s in range(REPS):
        d = simulate_dgp(Config(seed=10_000 + s, **kw)); a = time.perf_counter()
        rows, _ = run_dml(d, seed=10_000 + s); tm.append(time.perf_counter() - a)
        for r in rows: recs[(r["folds"], r["variance"])].append(r)
    res = {}
    for c, rs in recs.items():
        tau = np.array([r["tau"] for r in rs]); lo = np.array([r["lo"] for r in rs]); hi = np.array([r["hi"] for r in rs])
        cov = float(np.mean((lo <= kw.get("tau", 1.0)) & (kw.get("tau", 1.0) <= hi)))
        res["/".join(c)] = dict(coverage=cov, mc_se_cov=float(np.sqrt(cov * (1 - cov) / REPS)), bias=float(tau.mean() - kw.get("tau", 1.0)),
                                 width=float(np.mean(hi - lo)), sd_tau=float(tau.std(ddof=1)), mean_se=float(np.mean([r["se"] for r in rs])))
    out[name] = dict(config={k: v for k, v in kw.items()}, reps=REPS, sec_per_rep=float(np.mean(tm)), results=res)
    json.dump(out, open("results/mc_results.json", "w"), indent=1); print(name, "done", time.perf_counter() - t0, flush=True)

mc("baseline_no_dependence", density=0.0, n_regimes=0, gamma=0.0)
dens4 = density_for_overlap(0.5, 4); dens16 = density_for_overlap(0.5, 16)
mc("dependent_K4_overlap0.5", density=dens4, n_regimes=4)
mc("dependent_K16_overlap0.5", density=dens16, n_regimes=16)
print("ALL DONE")
