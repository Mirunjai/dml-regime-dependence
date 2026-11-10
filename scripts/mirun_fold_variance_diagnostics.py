"""Structural diagnostics for the week2_completion DGP/DML (EXPLORATORY, not Gate 2).

Everything here is computed from the simulated *structure* only (memberships,
window dates, fold labels); no nuisance model is fit and no truth value is used.
Measures, per (K, density) cell over a seed range:

* connected components of the regime-overlap graph and feasibility of 5 grouped folds
* grouped-fold size balance (largest/smallest fold)
* whether the overlap adjacency A (A_ij = 1 if events share a regime) is PSD.
  A non-PSD A is *necessary* for a negative sandwich meat psi'A psi.
* cross-fold leakage of regime pairs (should be 0 for grouped) and of pairs whose
  H-day windows share a calendar date (shared factor F), under random vs grouped folds.

Writes a JSON table; never overwrites an existing file.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import _components, make_folds


def overlap_matrix(memberships):
    """Dense A with A_ij = 1 iff events i and j share >=1 regime (diagonal 1)."""
    n = len(memberships)
    A = np.eye(n)
    owners = {}
    for i, m in enumerate(memberships):
        for r in m:
            owners.setdefault(r, []).append(i)
    for members in owners.values():
        idx = np.asarray(members)
        A[np.ix_(idx, idx)] = 1.0
    return A


def min_eigenvalue(memberships):
    return float(np.linalg.eigvalsh(overlap_matrix(memberships))[0])


def calendar_share_matrix(t0, H):
    """True where two distinct events' H-day windows share a calendar date."""
    d = np.abs(np.asarray(t0)[:, None] - np.asarray(t0)[None, :])
    share = d <= H - 1
    np.fill_diagonal(share, False)
    return share


def leakage(share, fold):
    """(cross-fold pairs, all pairs) among unordered pairs where `share` is True."""
    upper = np.triu(share, 1)
    cross = upper & (fold[:, None] != fold[None, :])
    return int(cross.sum()), int(upper.sum())


def one_world(cfg, n_folds=5, tol=1e-9):
    data = build_world(cfg)
    memberships = data["cluster_memberships"]
    n = len(memberships)
    labels = _components(memberships)
    sizes = np.bincount(labels)
    out = {"n_components": int(len(sizes)), "largest_component": int(sizes.max()),
           "n_exposed": int(data["exposed"].sum()),
           "n_multi_regime": int(sum(len(m) > 1 for m in memberships)),
           "min_eig_A": min_eigenvalue(memberships)}
    out["A_not_psd"] = bool(out["min_eig_A"] < -tol)
    out["grouped_feasible"] = bool(len(sizes) >= n_folds)
    cal = calendar_share_matrix(data["t0"], cfg.H)
    reg = overlap_matrix(memberships) > 0
    np.fill_diagonal(reg, False)
    rng = np.random.default_rng(cfg.seed)
    rf = make_folds("random", memberships, n_folds, rng)
    out["random_regime_cross"], out["regime_pairs"] = leakage(reg, rf)
    out["random_calendar_cross"], out["calendar_pairs"] = leakage(cal, rf)
    if out["grouped_feasible"]:
        gf = make_folds("grouped", memberships, n_folds, np.random.default_rng(cfg.seed + 1))
        fs = np.bincount(gf, minlength=n_folds)
        out["grouped_fold_max_over_min"] = float(fs.max() / max(fs.min(), 1))
        out["grouped_fold_max_share"] = float(fs.max() / n)
        out["grouped_regime_cross"], _ = leakage(reg, gf)
        out["grouped_calendar_cross"], _ = leakage(cal, gf)
    return out


def summarize(rows):
    def mean(key):
        vals = [r[key] for r in rows if key in r]
        return float(np.mean(vals)) if vals else None
    feas = [r for r in rows if r["grouped_feasible"]]
    return {"worlds": len(rows),
            "mean_components": mean("n_components"),
            "mean_largest_component": mean("largest_component"),
            "mean_exposed": mean("n_exposed"),
            "share_worlds_with_multi_regime": float(np.mean([r["n_multi_regime"] > 0 for r in rows])),
            "mean_multi_regime_events": mean("n_multi_regime"),
            "share_worlds_A_not_psd": float(np.mean([r["A_not_psd"] for r in rows])),
            "share_grouped_infeasible": float(1 - len(feas) / len(rows)),
            "grouped_fold_max_over_min_median": float(np.median([r["grouped_fold_max_over_min"] for r in feas])) if feas else None,
            "grouped_fold_max_share_mean": mean("grouped_fold_max_share"),
            "calendar_pairs_mean": mean("calendar_pairs"),
            "frac_calendar_pairs_cross_fold_random": float(np.mean([r["random_calendar_cross"] / max(r["calendar_pairs"], 1) for r in rows])),
            "frac_calendar_pairs_cross_fold_grouped": float(np.mean([r["grouped_calendar_cross"] / max(r["calendar_pairs"], 1) for r in feas])) if feas else None,
            "grouped_regime_cross_pairs_total": int(sum(r.get("grouped_regime_cross", 0) for r in feas)),
            "random_regime_cross_over_regime_pairs": float(np.mean([r["random_regime_cross"] / max(r["regime_pairs"], 1) for r in rows if r["regime_pairs"]])) if any(r["regime_pairs"] for r in rows) else None}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=20000)
    ap.add_argument("--K", type=int, nargs="+", default=[2, 4, 8, 16])
    ap.add_argument("--density", type=float, nargs="+", default=[.1, .25, .5, .75])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.out.exists():
        ap.error(f"{args.out} exists; refusing to overwrite")
    table = {}
    base = Config()
    for K in args.K:
        for dens in args.density:
            rows = [one_world(replace(base, seed=args.seed0 + s, n_regimes=K, density=dens))
                    for s in range(args.seeds)]
            table[f"K{K}_density{dens:g}"] = summarize(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"purpose": "exploratory structural diagnostics; not a Gate 2 decision",
                                    "seeds": [args.seed0, args.seed0 + args.seeds - 1],
                                    "base_config": base.__dict__, "cells": table}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
