"""Session 5 exploratory checks (calendar DGP unmodified; conditions below change only documented Config PARAMETERS).
  garch    : canonical (src/dgp/volatility.py) vs calendar (week2_completion) GARCH, theory + simulation.
  overlap  : reproduce multi-regime event counts and calendar-window overlap share.
  controls : run/summarize control conditions (independent control, factor-only, variance-matched factor-off).
Never overwrites existing outputs.
"""
import argparse, json, time
from dataclasses import replace, asdict
from pathlib import Path
import numpy as np
from research.week2_completion import dgp as W
from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import run_dml
from src.dgp import volatility as C

def acf(x, lags):
    x = x - x.mean(); d = (x * x).sum()
    return [float((x[:-k] * x[k:]).sum() / d) for k in lags]

def theory(alpha, rho):
    m4 = 3 * alpha**2 + 2 * alpha * (rho - alpha) + (rho - alpha)**2
    kurt = 3 * (1 - rho**2) / (1 - rho**2 - 2 * alpha**2) if m4 < 1 else None
    return {"alpha": alpha, "beta": rho - alpha, "omega": 1 - rho, "fourth_moment_factor": m4, "kurtosis": kurt}

def pooled_stats(sig, z):
    r = sig * z
    r2 = r ** 2
    return {"var": float(r.var()), "kurtosis": float((r**4).mean() / r.var()**2),
            "acf_r2_lag1_5": [float(np.mean([acf(row, [k])[0] for row in r2[:400]])) for k in (1, 2, 3, 4, 5)]}

def garch(out):
    res = {"purpose": "canonical vs calendar GARCH; exploratory", "rho_grid": {}}
    for rho in (.5, .9, .95):
        a_cal, a_can = .10, .1 * rho
        row = {"theory_calendar": theory(a_cal, rho), "theory_canonical": theory(a_can, rho)}
        if rho < .95:
            sc, zc = W.simulate_volatility(2000, 1500, rho, np.random.default_rng(1))
            sk, zk = C.simulate_volatility(2000, 1500, rho, np.random.default_rng(1))
            row["sim_calendar"], row["sim_canonical"] = pooled_stats(sc, zc), pooled_stats(sk, zk)
            row["same_seed_same_path"] = bool(np.allclose(sc[:, :50], sk[:, :50]))
        res["rho_grid"][str(rho)] = row
    # draw-order check: first innovation matrices for same seed
    zc = np.random.default_rng(7).standard_normal((3, 4))                    # calendar: row-major (firm, time)
    zk = np.stack([np.random.default_rng(7).standard_normal(3)])             # canonical first step only
    res["draw_order"] = {"calendar_first_firm_first_draw": float(zc[0, 0]),
                         "canonical_first_step_firm_draws_first": float(zk[0, 0]),
                         "note": "calendar draws a (firms x periods+burn) matrix row-major; canonical draws one vector per time step"}
    Path(out).write_text(json.dumps(res, indent=1))

def overlap(out):
    res = {}
    for K in (4, 16):
        multi = tot = pairs = allp = 0
        for s in range(200):
            d = build_world(replace(Config(), n_regimes=K, seed=20000 + s))
            m = d["cluster_memberships"]; t0 = np.asarray(d["t0"])
            multi += sum(len(x) > 1 for x in m); tot += len(m)
            dt = np.abs(t0[:, None] - t0[None, :]); u = np.triu(np.ones_like(dt, bool), 1)
            pairs += int(((dt <= Config().H - 1) & u).sum()); allp += int(u.sum())
        res[f"K{K}"] = {"worlds": 200, "events": tot, "multi_regime_events": multi, "calendar_overlap_pair_share": pairs / allp}
    Path(out).write_text(json.dumps({"purpose": "reproduce Session-1 overlap observations (seeds 20000-20199, default Config, density .5)", **res}, indent=1))

def noise_var(cfg, seeds=range(60)):
    v = []
    for s in seeds:
        d = build_world(replace(cfg, seed=80000 + s))
        g = .5 * d["X"][:, 0] + .3 * d["X"][:, 1] ** 2 + .2 * d["X"][:, 0] * d["X"][:, 2]
        v.append(np.var(d["Y"] - cfg.tau * d["D"] - g))
    return float(np.mean(v))

def conditions():
    base = Config()
    v_def = noise_var(base)
    off1 = noise_var(replace(base, sd_factor=0.))
    off2 = noise_var(replace(base, sd_factor=0., sigma2_bar=2.))
    a = off2 - off1                       # slope per unit sigma2_bar (idiosyncratic part)
    s2 = 1 + (v_def - off1) / a           # match total outcome-noise variance of the default benchmark
    return ({"C0_default_benchmark": base,
             "C1_independent_control": replace(base, sd_factor=0., sd_shock=0., gamma=0.),
             "C2_factor_only": replace(base, sd_shock=0., gamma=0.),
             "C3_factor_off_unmatched": replace(base, sd_factor=0.),
             "C4_factor_off_variance_matched": replace(base, sd_factor=0., sigma2_bar=float(s2))},
            {"noise_var_default": v_def, "noise_var_factor_off": off1, "slope_per_sigma2_bar": a, "matched_sigma2_bar": float(s2)})

def run_controls(outdir, reps, budget):
    conds, calib = conditions(); outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    cal = outdir / "calibration.json"
    if not cal.exists(): cal.write_text(json.dumps({**calib, "configs": {k: asdict(v) for k, v in conds.items()}}, indent=1))
    t0, done = time.perf_counter(), 0
    for rep in range(reps):
        for name, cfg in conds.items():
            p = outdir / name / f"rep_{rep:05d}.json"
            if p.exists(): continue
            if time.perf_counter() - t0 > budget: print(json.dumps({"saved": done, "complete": False})); return
            c = replace(cfg, seed=70000 + rep, tau=1.0)
            rows, _ = run_dml(build_world(c), n_folds=5, seed=c.seed)
            rec = {"condition": name, "rep": rep, "seed": c.seed, "cells": [{k: r[k] for k in ("folds", "variance", "status", "error", "tau", "se", "lo", "hi")} for r in rows]}
            p.parent.mkdir(parents=True, exist_ok=True); tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(rec)); tmp.replace(p); done += 1
    print(json.dumps({"saved": done, "complete": True}))

def summarize_controls(outdir, out):
    res = {}
    for d in sorted(Path(outdir).iterdir()):
        if not d.is_dir(): continue
        recs = [json.loads(f.read_text()) for f in sorted(d.glob("rep_*.json"))]; row = {"reps": len(recs), "cells": {}}
        for sch in ("random", "grouped"):
            tau = np.array([[c["tau"] for c in r["cells"] if c["folds"] == sch and c["variance"] == "naive"][0] for r in recs]); sd = tau.std(ddof=1)
            for var in ("naive", "multiway"):
                cs = [[c for c in r["cells"] if c["folds"] == sch and c["variance"] == var][0] for r in recs]
                ok = [c for c in cs if c["status"] == "ok"]; hit = np.array([c["lo"] <= 1 <= c["hi"] for c in ok])
                row["cells"][f"{sch}/{var}"] = {"valid": len(ok), "failed": len(cs) - len(ok), "coverage": float(hit.mean()),
                    "mcse": float(np.sqrt(hit.mean() * (1 - hit.mean()) / len(hit))), "se_over_sd": float(np.mean([c["se"] for c in ok]) / sd), "sd_tau": float(sd), "bias": float(tau.mean() - 1)}
        res[d.name] = row
    Path(out).write_text(json.dumps({"purpose": "exploratory control conditions, tau=1, seeds 70000+rep, K=4 d=.5 n=400", "conditions": res}, indent=1))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("action"); ap.add_argument("--out", required=True)
    ap.add_argument("--dir"); ap.add_argument("--reps", type=int, default=200); ap.add_argument("--budget-seconds", type=float, default=225)
    a = ap.parse_args()
    if a.action in ("garch", "overlap", "summarize") and Path(a.out).exists(): ap.error("output exists")
    {"garch": lambda: garch(a.out), "overlap": lambda: overlap(a.out), "run": lambda: run_controls(a.out, a.reps, a.budget_seconds),
     "summarize": lambda: summarize_controls(a.dir, a.out)}[a.action]()
