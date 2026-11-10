"""EXPLORATORY: diagnose robust-variance undercoverage. Calendar DGP unmodified; seeds 30000+rep (same worlds as the
failure scan); gamma=1, tau=1. Per replication, for each nuisance route, compute the repo estimator AND separately
labelled alternatives (research/mirun_proposals). Oracle routes use simulation truth: diagnostic only.
Routes: rf_random, rf_grouped, gbr_random, gbr_grouped, oracle (no cross-fitting).
  python -m scripts.mirun_undercoverage_study run --out DIR --K 4 --n 400 --reps 200 --routes rf_random rf_grouped gbr_random oracle
  python -m scripts.mirun_undercoverage_study summarize --out DIR --json results/tables/X.json
"""
import argparse, json, time
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.stats import norm
from research.mirun_proposals.nuisance import generic_crossfit, gbr_learner, oracle_residuals, rf_learner
from research.mirun_proposals.variance_alternatives import alternatives
from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import make_folds

SEED0 = 30000

def run_rep(cfg, routes):
    data = build_world(cfg)
    Y, D, X, mem, seed = data["Y"], data["D"], data["X"], data["cluster_memberships"], cfg.seed
    folds = {"random": make_folds("random", mem, 5, np.random.default_rng(seed)),
             "grouped": make_folds("grouped", mem, 5, np.random.default_rng(seed + 1))}
    out = {"n_multi_regime": int(sum(len(m) > 1 for m in mem))}
    for r in routes:
        if r == "oracle":
            Yt, Dt = oracle_residuals(data, cfg)
        else:
            learner, scheme = r.split("_")
            Yt, Dt = generic_crossfit(Y, D, X, folds[scheme], 5, seed, {"rf": rf_learner, "gbr": gbr_learner}[learner])
        a = alternatives(Yt, Dt, mem)
        out[r] = {"tau": a["tau"], "variants": a["variants"], "G_reg": a["decomposition"]["G_reg"],
                  "G_all": a["decomposition"]["G_all"]}
    return out

def summarize(d, truth=1.0):
    recs = [json.loads(f.read_text()) for f in sorted(Path(d).glob("rep_*.json"))]
    routes = [k for k in recs[0] if isinstance(recs[0][k], dict) and "tau" in recs[0][k]]
    table = {}
    for r in routes:
        tau = np.array([x[r]["tau"] for x in recs]); sd = tau.std(ddof=1)
        row = {"reps": len(recs), "sd_tau": float(sd), "bias_over_sd": float((tau.mean() - truth) / sd),
               "mean_G_reg": float(np.mean([x[r]["G_reg"] for x in recs])), "variants": {}}
        for v in recs[0][r]["variants"]:
            items = [x[r]["variants"][v] for x in recs]
            ok = [(t, i) for t, i in zip(tau, items) if i and i["se"]]
            if not ok: row["variants"][v] = None; continue
            hit = np.array([abs(t - truth) <= i["crit"] * i["se"] for t, i in ok])
            row["variants"][v] = {"valid": len(ok), "undefined": len(items) - len(ok), "coverage": float(hit.mean()),
                "mcse": float(np.sqrt(hit.mean() * (1 - hit.mean()) / len(hit))),
                "mean_se_over_sd": float(np.mean([i["se"] for _, i in ok]) / sd),
                "mean_halfwidth_over_sd": float(np.mean([i["crit"] * i["se"] for _, i in ok]) / sd)}
        table[r] = row
    return table

def paired(d, truth):
    """Paired (by replication) rejection-rate difference grouped - random for each variant, both routes needed."""
    recs = [json.loads(f.read_text()) for f in sorted(Path(d).glob("rep_*.json"))]
    if not all("rf_random" in r and "rf_grouped" in r for r in recs): return None
    out = {}
    for v in recs[0]["rf_random"]["variants"]:
        diffs = []
        for r in recs:
            a, b = r["rf_random"], r["rf_grouped"]
            ia, ib = a["variants"][v], b["variants"][v]
            if ia and ib and ia["se"] and ib["se"]:
                diffs.append(float(abs(b["tau"] - truth) > ib["crit"] * ib["se"]) - float(abs(a["tau"] - truth) > ia["crit"] * ia["se"]))
        if len(diffs) > 1:
            x = np.array(diffs); out[v] = {"n": len(x), "grouped_minus_random_rejection": float(x.mean()), "mcse": float(x.std(ddof=1) / np.sqrt(len(x)))}
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("action", choices=["run", "summarize"])
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--K", type=int, default=4)
    ap.add_argument("--n", type=int, default=400); ap.add_argument("--density", type=float, default=.5)
    ap.add_argument("--reps", type=int, default=200); ap.add_argument("--routes", nargs="+", default=["rf_random"])
    ap.add_argument("--budget-seconds", type=float, default=225); ap.add_argument("--json", type=Path)
    ap.add_argument("--tau", type=float, default=1.0); ap.add_argument("--gamma", type=float, default=1.0); ap.add_argument("--seed0", type=int, default=SEED0)
    a = ap.parse_args()
    if a.action == "summarize":
        a.json.write_text(json.dumps({"purpose": "exploratory undercoverage diagnosis; alternatives are proposals; oracle uses truth",
                                      "args": {"K": a.K, "n": a.n, "density": a.density, "tau": a.tau, "gamma": a.gamma, "seed0": a.seed0}, "table": summarize(a.out, a.tau), "paired_size_random_vs_grouped": paired(a.out, a.tau)}, indent=1)); return 0
    t0, done = time.perf_counter(), 0
    for rep in range(a.reps):
        p = a.out / f"rep_{rep:05d}.json"
        if p.exists(): continue
        if time.perf_counter() - t0 > a.budget_seconds:
            print(json.dumps({"saved": done, "complete": False})); return 3
        cfg = replace(Config(), n=a.n, n_regimes=a.K, density=a.density, gamma=a.gamma, tau=a.tau, seed=a.seed0 + rep)
        rec = run_rep(cfg, a.routes); p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(rec)); tmp.replace(p); done += 1
    print(json.dumps({"saved": done, "complete": True})); return 0

if __name__ == "__main__":
    raise SystemExit(main())
