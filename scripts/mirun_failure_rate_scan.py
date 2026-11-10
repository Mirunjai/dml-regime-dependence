"""EXPLORATORY: empirical failure rate of the week2_completion overlap sandwich with real fitted DML scores.

Runs the unmodified `run_dml` on the unmodified calendar DGP. One JSON per (setting, replication),
written atomically; existing files are skipped (resumable); time-boxed because the sandbox kills long jobs.
Seeds are SEED0 + replication (SEED0=30000, disjoint from the 10000/20000 pilot seeds).
Not an approved design; no estimator or DGP is changed.

  python -m scripts.mirun_failure_rate_scan --out results/raw/mirun_session3/failure_scan --reps 60 --budget-seconds 220
  python -m scripts.mirun_failure_rate_scan --out ... --summarize results/tables/mirun_failure_rate_scan.json
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import run_dml

SEED0 = 30000
SETTINGS = [(4, .5), (8, .5), (8, .75), (16, .5), (16, .75)]  # (K, density); gamma=1, tau=1


def name(K, d):
    return f"K{K}_d{d:g}"


def run_one(K, d, rep, gamma=1.0, tau=1.0):
    cfg = replace(Config(), n_regimes=K, density=d, gamma=gamma, tau=tau, seed=SEED0 + rep)
    data = build_world(cfg)
    rows, runtime = run_dml(data, n_folds=5, seed=cfg.seed)
    mem = data["cluster_memberships"]
    return {"setting": name(K, d), "K": K, "density": d, "gamma": gamma, "tau": tau, "replication": rep,
            "seed": cfg.seed, "n_multi_regime": int(sum(len(m) > 1 for m in mem)),
            "n_exposed": int(data["exposed"].sum()),
            "cells": [{k: r[k] for k in ("folds", "variance", "status", "error", "tau", "se", "lo", "hi",
                                         "n_dependency_pairs")} for r in rows],
            "runtime": runtime}


def summarize(out):
    res = {}
    for f in sorted(Path(out).glob("*/rep_*.json")):
        rec = json.loads(f.read_text())
        res.setdefault(rec["setting"], []).append(rec)
    table = {}
    for s, recs in res.items():
        row = {"reps": len(recs), "K": recs[0]["K"], "density": recs[0]["density"],
               "share_reps_with_multi_regime": float(np.mean([r["n_multi_regime"] > 0 for r in recs])), "cells": {}}
        for scheme in ("random", "grouped"):
            cs = [c for r in recs for c in r["cells"] if c["folds"] == scheme and c["variance"] == "multiway"]
            ns = [c for r in recs for c in r["cells"] if c["folds"] == scheme and c["variance"] == "naive"]
            fails = [c for c in cs if c["status"] != "ok"]
            nonpos = [c for c in fails if c["error"] and "nonpositive" in c["error"]]
            ratio = [c["se"] / n["se"] for c, n in zip(cs, ns) if c["status"] == "ok" and n["se"]]
            k = len(fails)
            n = len(cs)
            p = k / n
            z = 1.959964
            lo = (p + z * z / (2 * n) - z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
            hi = (p + z * z / (2 * n) + z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
            row["cells"][scheme] = {"n": n, "failed": k, "failed_nonpositive_meat": len(nonpos),
                                    "failure_rate": p, "wilson95": [float(lo), float(hi)],
                                    "other_error_types": sorted({c["error"].split(":")[0] for c in fails if c not in nonpos}),
                                    "median_se_ratio_multiway_over_naive": float(np.median(ratio)) if ratio else None}
        table[s] = row
    return table


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=60)
    ap.add_argument("--budget-seconds", type=float, default=220)
    ap.add_argument("--summarize", type=Path)
    args = ap.parse_args(argv)
    if args.summarize:
        args.summarize.write_text(json.dumps({
            "purpose": "exploratory failure-rate scan; calendar DGP; seeds 30000+rep; gamma=1,tau=1; not approved",
            "table": summarize(args.out)}, indent=1))
        return 0
    started, done = time.perf_counter(), 0
    for rep in range(args.reps):                      # interleave settings so partial runs stay balanced
        for K, d in SETTINGS:
            path = args.out / name(K, d) / f"rep_{rep:05d}.json"
            if path.exists():
                continue
            if time.perf_counter() - started > args.budget_seconds:
                print(json.dumps({"saved_this_call": done, "complete": False}))
                return 3
            rec = run_one(K, d, rep)
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(rec))
            tmp.replace(path)
            done += 1
    print(json.dumps({"saved_this_call": done, "complete": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
