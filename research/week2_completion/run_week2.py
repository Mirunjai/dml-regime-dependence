"""Exploratory DML runner with per-attempt raw records and explicit failures.

This command supplies implementation/diagnostic evidence. It does not choose a
primary scientific model, approve Gate 2/3, or launch an approved full campaign.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np

from src.evaluation.metrics import summarize_intervals
from src.infra.reproducibility import save_json_atomic
from .dgp import Config, STREAMS, build_world
from .dml import CELLS, run_dml
from .validation import run_gate2


def numeric_diagnostics(data):
    """Producer screens; raw replay permits the verifier to recompute them."""
    sigma = data["sig"]
    with np.errstate(over="raise", invalid="raise"):
        returns = sigma * data["z"]
        variance = sigma ** 2
        mean_r2 = float(np.mean(returns ** 2))
    return {"nonfinite_sigma": int((~np.isfinite(sigma)).sum()),
            "nonpositive_sigma": int((sigma <= 0).sum()),
            "nonfinite_variance": int((~np.isfinite(variance)).sum()),
            "nonpositive_variance": int((variance <= 0).sum()),
            "nonfinite_idiosyncratic_return": int((~np.isfinite(returns)).sum()),
            "max_abs_idiosyncratic_return": float(np.max(np.abs(returns))),
            "mean_squared_idiosyncratic_return": mean_r2,
            "nonfinite_outcome": int((~np.isfinite(data["Y"])).sum()),
            "interpretation": "Producer numeric summaries; no clipping and no implicit extreme-value cutoff"}


def _mean_mcse(values):
    if not values:
        return None, None
    values = np.asarray(values, dtype=float)
    return float(values.mean()), float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else None


def monte_carlo(reps, gamma, tau, density, K, n=400, T=260, H=5, folds=5, seed0=20000, *, raw_dir=None):
    if isinstance(reps, bool) or not isinstance(reps, int) or reps < 1:
        raise ValueError("reps must be a positive integer")
    base = Config(n=n, T=T, H=H, density=density, n_regimes=K, gamma=gamma, tau=tau, seed=seed0)
    base.validate()
    if isinstance(folds, bool) or not isinstance(folds, int) or not 2 <= folds <= n:
        raise ValueError("folds must be between 2 and n")
    if seed0 + reps - 1 >= 2**32 - 101 - folds:
        raise ValueError("Replication estimator seeds exceed supported sklearn seed range")
    if raw_dir is not None:
        raw_dir = Path(raw_dir)
        raw_dir.mkdir(parents=True, exist_ok=False)
        save_json_atomic(raw_dir / "config.json", {"config": asdict(base), "reps": reps,
            "folds": folds, "seed0": seed0, "seed_rule": "seed0 + replication",
            "estimator_variant": "full-regime-membership overlap sandwich; regime-only",
            "design_status": "Exploratory; no Gate 3 approval granted"})
    records, failures, attempts = [], [], []
    started = time.perf_counter()
    for replication in range(reps):
        seed = seed0 + replication
        cfg = Config(**{**asdict(base), "seed": seed})
        one_started, diagnostics = time.perf_counter(), None
        try:
            data = build_world(cfg)
            diagnostics = numeric_diagnostics(data)
            rows, runtime = run_dml(data, n_folds=folds, seed=seed)
        except Exception as exc:
            rows = [{"folds": fold, "variance": variance, "status": "failed", "tau": None,
                     "se": None, "lo": None, "hi": None, "error": f"{type(exc).__name__}: {exc}",
                     "fold_ids": None, "fold_diagnostics": None} for fold, variance in CELLS]
            runtime = {}
        attempt = {"schema_version": 1, "replication": replication, "seed": seed,
                   "config": asdict(cfg), "estimator": {"n_folds": folds, "seed": seed,
                       "learner": "RandomForestRegressor", "n_estimators": 40,
                       "min_samples_leaf": 8, "max_features": .5, "n_jobs": 1},
                   "confidence_level": .95, "rng_streams": {
                       name: {"entropy": seed, "spawn_key": [i]} for i, name in enumerate(STREAMS)},
                   "cells": rows, "numeric_diagnostics": diagnostics,
                   "runtime_by_scheme": runtime, "total_seconds": time.perf_counter() - one_started}
        attempts.append(attempt)
        for row in rows:
            key = f"{row['folds']}/{row['variance']}"
            records.append({**row, "replication": replication, "seed": seed,
                            "truth": tau, "config": asdict(cfg), "cell": key})
            if row["status"] != "ok":
                failures.append({"replication": replication, "seed": seed,
                                 "cell": key, "message": row["error"]})
        if raw_dir is not None:
            save_json_atomic(raw_dir / f"rep_{replication:06d}.json", attempt)
    summaries = {}
    for fold, variance in CELLS:
        name = f"{fold}/{variance}"
        cells = [row for row in records if row["cell"] == name]
        success = np.array([row["status"] == "ok" for row in cells], dtype=bool)
        lower = [row["lo"] if ok else np.nan for row, ok in zip(cells, success)]
        upper = [row["hi"] if ok else np.nan for row, ok in zip(cells, success)]
        summary = summarize_intervals(lower, upper, tau, success=success, failure_policy="report", expected_replications=reps)
        valid_estimates = [row["tau"] for row, ok in zip(cells, success) if ok]
        bias, bias_mcse = _mean_mcse([value - tau for value in valid_estimates])
        point_estimates = [row["tau"] for row in cells if row["tau"] is not None and np.isfinite(row["tau"])]
        point_bias, point_bias_mcse = _mean_mcse([value - tau for value in point_estimates])
        summaries[name] = {"attempted_reps": reps, "successful_reps": summary.valid,
            "failed_reps": summary.failed, "conditional_on_success": summary.conditional_on_success,
            "coverage": summary.coverage.rate if summary.coverage else None,
            "mc_se_coverage": summary.coverage.mcse if summary.coverage else None,
            "coverage_wilson95": summary.coverage.wilson95 if summary.coverage else None,
            "coverage_bounds_all_attempted": summary.coverage_bounds_all_attempted,
            "bias": bias, "mc_se_bias": bias_mcse,
            "rmse": float(np.sqrt(np.mean((np.array(valid_estimates) - tau) ** 2))) if valid_estimates else None,
            "mean_interval_width": summary.mean_width, "mc_se_width": summary.width_mcse,
            "empirical_size": summary.size.rate if summary.size else None,
            "mc_se_size": summary.size.mcse if summary.size else None,
            "power": summary.power.rate if summary.power else None,
            "mc_se_power": summary.power.mcse if summary.power else None,
            "point_estimates_available": len(point_estimates),
            "bias_all_available_point_estimates": point_bias,
            "mc_se_bias_all_available_point_estimates": point_bias_mcse}
    failed_replications = {row["replication"] for row in failures}
    return {"reps_requested": reps, "reps_failed": len(failed_replications),
            "failure_rate": len(failed_replications) / reps, "failed_cell_count": len(failures),
            "gamma": gamma, "tau": tau, "density_setting": density, "K": K,
            "config": asdict(base), "estimator": {"n_folds": folds, "seed0": seed0},
            "seconds": time.perf_counter() - started, "results": summaries,
            "records": records, "attempts": attempts, "failures": failures,
            "raw_directory": str(raw_dir) if raw_dir else None}


def _provenance():
    import hashlib
    root = Path(__file__).resolve().parents[2]
    paths = sorted(Path(__file__).parent.glob("*.py"))
    return {"git_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
            "git_dirty": bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip()),
            "python": platform.python_version(),
            "packages": {name: version(name) for name in ("numpy", "scipy", "scikit-learn")},
            "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=20)
    parser.add_argument("--gamma-values", type=float, nargs="+", default=[0., 1.])
    parser.add_argument("--tau-values", type=float, nargs="+", default=[1., 0.])
    parser.add_argument("--density", type=float, default=.5)
    parser.add_argument("--K", type=int, default=4)
    parser.add_argument("--n", type=int, default=400)
    parser.add_argument("--T", type=int, default=260)
    parser.add_argument("--H", type=int, default=5)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20000)
    parser.add_argument("--gate2-seeds", type=int, default=50)
    parser.add_argument("--out", type=Path, default=Path("results/raw/week2_exploratory/run.json"))
    args = parser.parse_args(argv)
    if args.reps < 1 or args.gate2_seeds < 1:
        parser.error("--reps and --gate2-seeds must be positive")
    if len(set(args.gamma_values)) != len(args.gamma_values) or len(set(args.tau_values)) != len(args.tau_values):
        parser.error("Gamma and tau lists must not contain duplicates")
    try:
        for gamma in args.gamma_values:
            for tau in args.tau_values:
                Config(n=args.n, T=args.T, H=args.H, density=args.density, n_regimes=args.K,
                       gamma=gamma, tau=tau, seed=args.seed).validate()
        args.out.parent.mkdir(parents=True, exist_ok=False)
    except (ValueError, TypeError, OSError) as exc:
        parser.error(str(exc) + "; choose a new output directory")
    provenance = _provenance()
    base = Config(n=args.n, T=args.T, H=args.H, density=args.density, n_regimes=args.K,
                  gamma=args.gamma_values[0], tau=args.tau_values[0], seed=args.seed)
    save_json_atomic(args.out.parent / "manifest.json", {"schema_version": 2, "provenance": provenance,
        "purpose": "Exploratory comparison; Gate 2/3 approval not granted", "arguments": {
            **vars(args), "out": str(args.out)}})
    run_gate2(range(args.seed, args.seed + args.gate2_seeds), args.out.parent / "gate2.json", config=base,
              gamma_values=args.gamma_values)
    runs = []
    for gamma in args.gamma_values:
        for tau in args.tau_values:
            name = f"gamma{gamma:g}_tau{tau:g}"
            result = monte_carlo(args.reps, gamma, tau, args.density, args.K, args.n, args.T,
                                 args.H, args.folds, args.seed, raw_dir=args.out.parent / name)
            runs.append(result)
            save_json_atomic(args.out, {"schema_version": 2, "provenance": provenance,
                "note": "Exploratory results; all cells/attempts retained; not a Gate 2/3 decision", "runs": runs})
    if _provenance()["source_sha256"] != provenance["source_sha256"]:
        save_json_atomic(args.out.parent / "source_changed.json", {"invalidated": True})
        raise ValueError("Source changed while running; do not interpret this mixed-version run")
    failures = sum(run["failed_cell_count"] for run in runs)
    print(json.dumps({"output": str(args.out), "runs": len(runs), "failed_cells": failures}, indent=2))
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
