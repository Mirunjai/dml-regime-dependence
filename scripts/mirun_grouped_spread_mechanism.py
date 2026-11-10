"""EXPLORATORY DIAGNOSTIC: why does grouped cross-fitting inflate sd(tau-hat) at K=4, gamma=1?

Calendar DGP (week2_completion), unmodified. Only FOLD assignment or nuisance INPUTS are varied;
the DGP and the variance formulas are untouched. Variance is always computed with the true memberships.

Variants (all use the same world and the same learner/seed rule as run_dml):
  random, grouped                      -- as in run_dml
  size_matched_random                  -- random assignment with fold sizes equal to the grouped folds
  grouped_permuted                     -- grouped folds from membership tuples shuffled across events
                                          (same block-size structure, unrelated to the real regimes)
  random_oracleD / grouped_oracleD     -- X augmented with the TRUE regime treatment effect
  random_oracleDY / grouped_oracleDY   -- X augmented with true regime effect and U_win
The ORACLE variants use simulation truth in nuisance fitting. They are diagnostic interventions for
mechanism only and must never be reported as an estimator or as one of the four experimental cells.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import crossfit, estimate, make_folds

SEED0 = 30000


def fit(Y, D, X, fold, seed, mem):
    Yt, Dt = crossfit(Y, D, X, fold, 5, seed)
    r = estimate(Yt, Dt, mem, allow_invalid_multiway=True)
    return {"tau": r["tau"], "se_naive": r["se_naive"], "se_multiway": r["se_multiway"]}


def fold_sets(data, seed):
    """Fold vectors for the fold-only variants; exposed for tests."""
    mem = data["cluster_memberships"]
    n = len(mem)
    rf = make_folds("random", mem, 5, np.random.default_rng(seed))
    gf = make_folds("grouped", mem, 5, np.random.default_rng(seed + 1))
    sizes = np.bincount(gf, minlength=5)
    perm = np.random.default_rng(seed + 2).permutation(n)
    smf = np.empty(n, dtype=int)
    smf[perm] = np.repeat(np.arange(5), sizes)
    shuffled = np.random.default_rng(seed + 3).permutation(n)
    gpf = make_folds("grouped", [mem[i] for i in shuffled], 5, np.random.default_rng(seed + 4))
    return rf, gf, smf, gpf


def run_rep(cfg):
    data = build_world(cfg)
    Y, D, X, mem = data["Y"], data["D"], data["X"], data["cluster_memberships"]
    n, seed = len(Y), cfg.seed
    regime_effect = np.array([np.mean(data["vk"][list(m)]) if m else 0. for m in mem])
    X_d = np.column_stack([X, regime_effect])
    X_dy = np.column_stack([X, regime_effect, data["U_win"]])
    rf, gf, smf, gpf = fold_sets(data, seed)
    sizes = np.bincount(gf, minlength=5)
    gp_fold = gpf   # event j is assigned the fold implied by ANOTHER event's membership: pseudo-blocks
    out = {}
    for name, (Xv, fold) in {"random": (X, rf), "grouped": (X, gf), "size_matched_random": (X, smf),
                             "grouped_permuted": (X, gp_fold), "random_oracleD": (X_d, rf),
                             "grouped_oracleD": (X_d, gf), "random_oracleDY": (X_dy, rf),
                             "grouped_oracleDY": (X_dy, gf)}.items():
        out[name] = fit(Y, D, Xv, fold, seed, mem)
    out["grouped_fold_sizes"] = sizes.tolist()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--K", type=int, default=4)
    ap.add_argument("--density", type=float, default=.5)
    ap.add_argument("--budget-seconds", type=float, default=220)
    ap.add_argument("--summarize", type=Path)
    a = ap.parse_args(argv)
    if a.summarize:
        recs = [json.loads(f.read_text()) for f in sorted(a.out.glob("rep_*.json"))]
        names = [k for k in recs[0] if isinstance(recs[0][k], dict) and "tau" in recs[0][k]]
        table = {}
        for nme in names:
            t = np.array([r[nme]["tau"] for r in recs])
            sn = np.array([r[nme]["se_naive"] for r in recs])
            sm = np.array([r[nme]["se_multiway"] if r[nme]["se_multiway"] is not None else np.nan for r in recs])
            cov = lambda se: float(np.nanmean((np.abs(t - 1.0) <= 1.959964 * se)[~np.isnan(se)]))
            table[nme] = {"sd_tau": float(t.std(ddof=1)), "bias": float((t - 1).mean()),
                          "rmse": float(np.sqrt(np.mean((t - 1) ** 2))), "mean_se_naive": float(sn.mean()),
                          "coverage_naive": cov(sn), "coverage_multiway": cov(sm), "n": len(t)}
        base = table["random"]["sd_tau"]
        for v in table.values():
            v["sd_ratio_vs_random"] = v["sd_tau"] / base
        # bootstrap CI (over replications) for the sd ratio grouped/random and other variants
        rng = np.random.default_rng(0)
        T = {nme: np.array([r[nme]["tau"] for r in recs]) for nme in names}
        idx = rng.integers(0, len(recs), size=(2000, len(recs)))
        for nme in names:
            ratios = np.std(T[nme][idx], axis=1, ddof=1) / np.std(T["random"][idx], axis=1, ddof=1)
            table[nme]["sd_ratio_vs_random_boot95"] = [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]
        a.summarize.write_text(json.dumps({"purpose": "exploratory mechanism diagnostic; ORACLE variants use truth; not an estimator",
            "setting": {"K": a.K, "density": a.density, "gamma": a.gamma, "seeds": f"{SEED0}+rep", "reps": len(recs)},
            "variants": table}, indent=1))
        return 0
    started, done = time.perf_counter(), 0
    for rep in range(a.reps):
        path = a.out / f"rep_{rep:05d}.json"
        if path.exists():
            continue
        if time.perf_counter() - started > a.budget_seconds:
            print(json.dumps({"saved_this_call": done, "complete": False}))
            return 3
        cfg = replace(Config(), n_regimes=a.K, density=a.density, gamma=a.gamma, tau=1.0, seed=SEED0 + rep)
        rec = run_rep(cfg)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec))
        tmp.replace(path)
        done += 1
    print(json.dumps({"saved_this_call": done, "complete": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
