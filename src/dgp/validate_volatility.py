"""Reproducible standalone Week 1/2 volatility and Monte Carlo diagnostics.

Run ``python -m src.dgp.validate_volatility --quick`` for a smoke run. The default
config runs independent-panel validation and an actual pinned teammate component.
This is a diagnostic harness, not a DML experiment runner or a team gate decision.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import copy
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import time
import zipfile

import numpy as np

from src.dgp.independence import conditional_randomization_check, positive_control, regime_reference
from src.dgp.volatility import _count, _finite_real, garch_parameters, simulate_volatility
from src.evaluation.metrics import binomial_summary, paired_binary_difference, summarize_intervals

REPO = Path(__file__).resolve().parents[2]


def component_rng(seed: int, domain: int, replication: int, substream: int = 0) -> np.random.Generator:
    """Address streams by fixed identities, independent of iteration/scheduling order."""
    for name, value in (("seed", seed), ("domain", domain), ("replication", replication), ("substream", substream)):
        _count(name, value, 0)
    return np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(domain, replication, substream)))


def squared_return_acf(returns: np.ndarray, max_lag: int) -> np.ndarray:
    """Average within-firm biased sample ACF; never join unrelated firm boundaries.

    Returns lags 0..max_lag. Constant squared paths have undefined ACF (NaN),
    not an asserted zero association. Population interpretation needs finite e^4.
    """
    values = np.asarray(returns, dtype=float)
    max_lag = _count("max_lag", max_lag, 0)
    if values.ndim != 2 or min(values.shape) < 1 or max_lag >= values.shape[1]:
        raise ValueError("Require nonempty returns[firm,time] and max_lag < n_periods")
    if not np.isfinite(values).all():
        raise ValueError("Returns must be finite")
    with np.errstate(over="raise", invalid="raise"):
        squares = values**2
        centered = squares - squares.mean(axis=1, keepdims=True)
        denominator = np.sum(centered**2, axis=1)
        usable = denominator > 0
        if not usable.any():
            return np.full(max_lag + 1, np.nan)
        result = np.ones(max_lag + 1)
        for lag in range(1, max_lag + 1):
            numerator = np.sum(centered[:, lag:] * centered[:, :-lag], axis=1)
            result[lag] = np.mean(numerator[usable] / denominator[usable])
    return result


def _mean_mcse(values: Sequence[float]) -> dict:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return {"n": 0, "mean": None, "mcse": None}
    if not np.isfinite(values).all():
        raise ValueError("Cannot summarize nonfinite observations")
    return {"n": int(values.size), "mean": float(values.mean()),
            "mcse": float(values.std(ddof=1) / np.sqrt(values.size)) if values.size > 1 else None}


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Refusing to write an empty result table")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(value, (dict, list, tuple)) else value for key, value in row.items()})


def validate_config(config: dict) -> None:
    """Fail before simulation on misspelled, invalid or impossible settings."""
    required = {"label", "seed", "stability", "independence", "runtime"}
    if set(config) != required:
        raise ValueError(f"Configuration keys must be {sorted(required)}")
    if not isinstance(config["label"], str) or not config["label"].strip():
        raise ValueError("Configuration label must be a nonempty string")
    _count("seed", config["seed"], 0)
    stability = config["stability"]
    expected = {"n_firms", "n_periods", "burn_in", "long_burn_in", "replications", "persistence", "arch_share", "unconditional_variance", "acf_lags", "extreme_threshold_sd"}
    if set(stability) != expected:
        raise ValueError(f"Stability keys must be {sorted(expected)}")
    for name in ("n_firms", "n_periods", "replications"):
        _count(name, stability[name], 2 if name == "replications" else 1)
    for name in ("burn_in", "long_burn_in", "acf_lags"):
        _count(name, stability[name], 0)
    if stability["acf_lags"] >= stability["n_periods"] or stability["long_burn_in"] <= stability["burn_in"]:
        raise ValueError("Require acf_lags<n_periods and long_burn_in>burn_in")
    if _finite_real("extreme_threshold_sd", stability["extreme_threshold_sd"]) <= 0:
        raise ValueError("extreme_threshold_sd must be positive")
    if not isinstance(stability["persistence"], list) or not stability["persistence"]:
        raise ValueError("persistence must be a nonempty list")
    if len(set(stability["persistence"])) != len(stability["persistence"]):
        raise ValueError("Duplicate persistence settings")
    for rho in stability["persistence"]:
        garch_parameters(rho, arch_share=stability["arch_share"], unconditional_variance=stability["unconditional_variance"])
    independence = config["independence"]
    expected = {"replications", "n_firms", "n_periods", "persistence", "burn_in", "density", "n_regimes", "randomizations", "diagnostic_alpha", "positive_control_strength", "regime_ref"}
    if set(independence) != expected:
        raise ValueError(f"Independence keys must be {sorted(expected)}")
    for name in ("replications", "n_firms", "n_periods", "n_regimes", "randomizations"):
        _count(name, independence[name], 2 if name in ("replications", "n_periods") else 1)
    _count("burn_in", independence["burn_in"], 0)
    garch_parameters(independence["persistence"], arch_share=stability["arch_share"], unconditional_variance=stability["unconditional_variance"])
    density = _finite_real("density", independence["density"])
    if not 0 < density < 1 or round(independence["n_periods"] * density) < independence["n_regimes"]:
        raise ValueError("Independence diagnostics need 0<density<1 and enough active windows")
    if not 0 < _finite_real("diagnostic_alpha", independence["diagnostic_alpha"]) < 1:
        raise ValueError("diagnostic_alpha must be between zero and one")
    if _finite_real("positive_control_strength", independence["positive_control_strength"]) <= 0:
        raise ValueError("positive_control_strength must be positive")
    if not isinstance(independence["regime_ref"], str) or not independence["regime_ref"]:
        raise ValueError("regime_ref is required")
    runtime = config["runtime"]
    if set(runtime) != {"n_firms", "n_periods", "repeats"}:
        raise ValueError("Runtime keys must be n_firms, n_periods, repeats")
    _count("repeats", runtime["repeats"])
    for name in ("n_firms", "n_periods"):
        if not isinstance(runtime[name], list) or not runtime[name]:
            raise ValueError(f"Runtime {name} must be a nonempty list")
        for value in runtime[name]:
            _count(name, value)


def run_stability(config: dict, seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    """Stream one panel at a time; retain only summaries and two example firms."""
    rows, summaries, examples = [], [], []
    for rho in config["persistence"]:
        params = garch_parameters(rho, arch_share=config["arch_share"], unconditional_variance=config["unconditional_variance"])
        for burn in (config["burn_in"], config["long_burn_in"]):
            for replication in range(config["replications"]):
                row = {"persistence": rho, "burn_in": burn, "replication": replication,
                       "seed": seed, "spawn_key": [0, replication, 0], **asdict(params),
                       "fourth_moment_factor": params.fourth_moment_factor,
                       "fourth_moment_margin": params.fourth_moment_margin,
                       "finite_fourth_moment": params.has_finite_fourth_moment}
                try:
                    sigma, eps = simulate_volatility(
                        config["n_firms"], config["n_periods"], rho, component_rng(seed, 0, replication),
                        arch_share=config["arch_share"], unconditional_variance=config["unconditional_variance"], burn_in=burn,
                    )
                    h, returns = sigma**2, sigma * eps
                    with np.errstate(over="raise", invalid="raise"):
                        acf = squared_return_acf(returns, config["acf_lags"]) if params.has_finite_fourth_moment else None
                        if acf is not None and not np.isfinite(acf).all():
                            acf = None
                        extreme = np.argwhere(np.abs(returns) > config["extreme_threshold_sd"] * np.sqrt(params.unconditional_variance))
                        row.update(status="ok", mean_h=float(h.mean()), mean_e2=float(np.mean(returns**2)),
                                   min_h=float(h.min()), max_h=float(h.max()),
                                   max_abs_return=float(np.max(np.abs(returns))),
                                   abs_return_q999=float(np.quantile(np.abs(returns), 0.999)),
                                   extreme_return_count=int(len(extreme)),
                                   extreme_examples=[{"firm": int(i), "time": int(t), "return": float(returns[i, t]),
                                                      "sigma": float(sigma[i, t]), "eps": float(eps[i, t])} for i, t in extreme[:100]],
                                   extreme_examples_truncated=bool(len(extreme) > 100),
                                   nonfinite_count=int(np.sum(~np.isfinite(returns))),
                                   acf_status="evaluated" if acf is not None else "undefined: fourth moment or sample variation unavailable",
                                   acf=None if acf is None else acf.tolist())
                    if replication == 0 and burn == config["burn_in"] and rho in (config["persistence"][0], config["persistence"][-1]):
                        for t in range(min(1024, config["n_periods"])):
                            examples.append({"persistence": rho, "time": t, "firm": 0,
                                             "sigma": float(sigma[0, t]), "eps": float(eps[0, t]), "return": float(returns[0, t])})
                except (FloatingPointError, ValueError) as error:
                    row.update(status="failed", error=f"{type(error).__name__}: {error}")
                rows.append(row)
            subset = [r for r in rows if r["persistence"] == rho and r["burn_in"] == burn]
            valid = [r for r in subset if r["status"] == "ok"]
            acf_rows = [r["acf"] for r in valid if r["acf"] is not None]
            summaries.append({
                "persistence": rho, "burn_in": burn, "attempted": len(subset), "valid": len(valid),
                "failed": len(subset) - len(valid), "parameters": asdict(params),
                "fourth_moment_factor": params.fourth_moment_factor,
                "fourth_moment_margin": params.fourth_moment_margin,
                "finite_fourth_moment": params.has_finite_fourth_moment,
                "mean_h": _mean_mcse([r["mean_h"] for r in valid]),
                "mean_e2": _mean_mcse([r["mean_e2"] for r in valid]),
                "max_abs_return": max((r["max_abs_return"] for r in valid), default=None),
                "max_h": max((r["max_h"] for r in valid), default=None),
                "extreme_return_count": sum(r["extreme_return_count"] for r in valid),
                "nonfinite_count": sum(r["nonfinite_count"] for r in valid),
                "mean_acf": np.mean(acf_rows, axis=0).tolist() if acf_rows else None,
                "acf_mcse": (np.std(acf_rows, axis=0, ddof=1) / np.sqrt(len(acf_rows))).tolist() if len(acf_rows) > 1 else None,
                "population_acf": params.squared_return_acf(config["acf_lags"]).tolist() if params.has_finite_fourth_moment else None,
            })
            print(f"stability rho={rho:g}, burn={burn}: {len(valid)}/{len(subset)} usable", flush=True)
    # Paired burn-in contrasts reuse the same innovations and replication IDs.
    for summary in summaries:
        rho = summary["persistence"]
        base = {r["replication"]: r for r in rows if r["persistence"] == rho and r["burn_in"] == config["burn_in"] and r["status"] == "ok"}
        longer = {r["replication"]: r for r in rows if r["persistence"] == rho and r["burn_in"] == config["long_burn_in"] and r["status"] == "ok"}
        summary["long_minus_short_burn_mean_e2"] = _mean_mcse([longer[k]["mean_e2"] - base[k]["mean_e2"] for k in sorted(base.keys() & longer.keys())])
    return rows, summaries, examples


def run_independence(config: dict, stability: dict, seed: int, simulator) -> tuple[list[dict], dict]:
    rows = []
    for replication in range(config["replications"]):
        row = {"replication": replication, "seed": seed, "volatility_spawn_key": [1, replication, 0],
               "observed_regime_spawn_key": [2, replication, 0], "null_regime_spawn_key": [3, replication, 0]}
        try:
            kwargs = dict(arch_share=stability["arch_share"], unconditional_variance=stability["unconditional_variance"], burn_in=config["burn_in"])
            sigma, eps = simulate_volatility(config["n_firms"], config["n_periods"], config["persistence"], component_rng(seed, 1, replication), **kwargs)
            ids, shocks = simulator(config["n_periods"], config["density"], config["n_regimes"], component_rng(seed, 2, replication))
            # Different regime settings consume only the regime stream.
            simulator(config["n_periods"], 1.0, config["n_regimes"], component_rng(seed, 2, replication, 1))
            replay_sigma, replay_eps = simulate_volatility(config["n_firms"], config["n_periods"], config["persistence"], component_rng(seed, 1, replication), **kwargs)
            invariant = np.array_equal(sigma, replay_sigma) and np.array_equal(eps, replay_eps)
            control = positive_control(sigma**2, shocks, config["positive_control_strength"])
            check_kwargs = dict(density=config["density"], n_regimes=config["n_regimes"], randomizations=config["randomizations"])
            independent = conditional_randomization_check(sigma**2, ids, shocks, simulator, rng=component_rng(seed, 3, replication), **check_kwargs)
            dependent = conditional_randomization_check(control, ids, shocks, simulator, rng=component_rng(seed, 3, replication), **check_kwargs)
            row.update(status="ok", independent=independent, positive_control=dependent, stream_invariance=invariant)
        except (FloatingPointError, ValueError, TypeError) as error:
            row.update(status="failed", error=f"{type(error).__name__}: {error}")
        rows.append(row)
        if (replication + 1) % 10 == 0:
            print(f"independence: {replication + 1}/{config['replications']} panels", flush=True)
    summary = {"attempted": len(rows), "failed": sum(r["status"] != "ok" for r in rows),
               "diagnostic_alpha": config["diagnostic_alpha"],
               "stream_invariance_failures": sum(not r["stream_invariance"] for r in rows if r["status"] == "ok")}
    for key, label in (("independent", "false_detection_rate"), ("positive_control", "control_detection_rate")):
        pvalues = [r[key]["p_value"] for r in rows if r["status"] == "ok" and r[key]["p_value"] is not None]
        summary[label] = asdict(binomial_summary(sum(p <= config["diagnostic_alpha"] for p in pvalues), len(pvalues))) if pvalues else None
        summary[f"{key}_undefined"] = sum(r[key]["p_value"] is None for r in rows if r["status"] == "ok")
    summary["interpretation"] = "Component diagnostic with a pinned unmerged module; no proof of independence or integrated DGP/gate approval."
    summary["status"] = "incomplete" if (
        summary["failed"] or summary["stream_invariance_failures"]
        or summary["independent_undefined"] or summary["positive_control_undefined"]
    ) else "evaluated"
    return rows, summary


def run_runtime(config: dict, seed: int) -> list[dict]:
    rows = []
    for firms in config["n_firms"]:
        for periods in config["n_periods"]:
            for repetition in range(config["repeats"]):
                started = time.perf_counter()
                simulate_volatility(firms, periods, 0.9, component_rng(seed, 4, repetition), burn_in=1000)
                rows.append({"n_firms": firms, "n_periods": periods, "burn_in": 1000,
                             "repetition": repetition, "elapsed_seconds": time.perf_counter() - started,
                             "returned_array_bytes": 2 * firms * periods * 8})
    return rows


def mock_metrics() -> tuple[list[dict], dict]:
    rows = [{"replication": r, "truth": 0.0, "lower": -1.0 if r < 95 else 0.1,
             "upper": 1.0, "success": True, "source": "known-outcome mock"} for r in range(100)]
    summary = asdict(summarize_intervals([r["lower"] for r in rows], [r["upper"] for r in rows], 0.0))
    paired = asdict(paired_binary_difference({"r1": True, "r2": False, "r3": True, "r4": False},
                                           {"r4": False, "r3": False, "r2": True, "r1": True}))
    return rows, {"label": "Mock arithmetic only; not estimator coverage evidence", "intervals": summary, "paired_hand_example": paired}


def _provenance(config: dict, raw: Path) -> dict:
    sources = sorted([*REPO.glob("src/**/*.py"), *REPO.glob("tests/*.py"), *REPO.glob("scripts/*.py"),
                      *REPO.glob("configs/experiments/deeptanshu_*.json"), REPO / "docs/DECISIONS.md",
                      REPO / "requirements.txt", REPO / "requirements-dev.txt", REPO / "pyproject.toml"])
    hashes = {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    with zipfile.ZipFile(raw / "source_snapshot.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sources:
            archive.write(p, p.relative_to(REPO))
        archive.writestr("resolved_config.json", json.dumps(config, indent=2))
    return {"created_utc": datetime.now(timezone.utc).isoformat(), "config": config,
            "python": platform.python_version(), "platform": platform.platform(),
            "numpy": np.__version__, "matplotlib": version("matplotlib"),
            "git_head": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
            "git_dirty": bool(subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain"], text=True).strip()),
            "source_sha256": hashes,
            "seed_protocol": "PCG64; SeedSequence(seed, spawn_key=(domain, replication, substream)); domains 0=stability,1=independence volatility,2=observed regimes,3=null regimes,4=runtime. Stability uses common random numbers across rho/burn; independent replication IDs within each setting."}


def _clear_run_outputs(raw: Path, tables: Path, figures: Path, name: str) -> None:
    """Remove only this harness's named files after explicit overwrite consent.

    Optional outputs must not survive a replacement run that skips or fails their
    generating check. Preserve unrelated/user-created files and caches.
    """
    files = [raw / filename for filename in (
        "provenance.json", "source_snapshot.zip", "stability_replications.csv",
        "selected_series.csv", "independence_replications.json", "runtime.csv",
        "mock_intervals.csv", "reference/regime_shocks.py",
    )]
    files += [tables / f"{name}.json", tables / f"{name}_stability.csv"]
    files += [figures / f"{name}_{suffix}.png" for suffix in ("stability", "paths", "independence")]
    for path in files:
        path.unlink(missing_ok=True)


def plot_results(summary: dict, examples: list[dict], figures: Path, name: str, cache: Path) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures.mkdir(parents=True, exist_ok=True)
    base_burn = summary["config"]["stability"]["burn_in"]
    stability = [r for r in summary["stability"] if r["burn_in"] == base_burn]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for row in stability:
        if row["mean_acf"] is None:
            continue
        lags = np.arange(len(row["mean_acf"]))
        line, = axes[0].plot(lags[1:], row["mean_acf"][1:], label=f"rho={row['persistence']:g}")
        axes[0].plot(lags[1:], row["population_acf"][1:], "--", color=line.get_color(), alpha=0.6)
    axes[0].set(xlabel="Lag", ylabel="Squared-return ACF", title="Within-firm ACF: sample (solid), population (dashed)")
    if axes[0].get_legend_handles_labels()[0]:
        axes[0].legend(fontsize=8)
    for burn, marker in ((base_burn, "o"), (summary["config"]["stability"]["long_burn_in"], "s")):
        rows = [r for r in summary["stability"] if r["burn_in"] == burn and r["mean_e2"]["mean"] is not None]
        with_se = [r for r in rows if r["mean_e2"]["mcse"] is not None]
        without_se = [r for r in rows if r["mean_e2"]["mcse"] is None]
        if with_se:
            axes[1].errorbar([r["persistence"] for r in with_se], [r["mean_e2"]["mean"] for r in with_se],
                             yerr=[1.96 * r["mean_e2"]["mcse"] for r in with_se], fmt=marker + "-", capsize=3, label=f"burn={burn}")
        if without_se:
            axes[1].scatter([r["persistence"] for r in without_se], [r["mean_e2"]["mean"] for r in without_se],
                            marker=marker, label=f"burn={burn}; MCSE unavailable")
    if any(row["valid"] for row in stability):
        axes[1].axhline(summary["config"]["stability"]["unconditional_variance"], color="black", linestyle="--", label="Intended variance")
    else:
        axes[1].text(0.5, 0.5, "No numerically usable panels; see failure table", ha="center", transform=axes[1].transAxes)
    axes[1].set(xlabel="Persistence rho", ylabel="Mean squared idiosyncratic return", title="Mean ± 1.96 MCSE across independent panels")
    if axes[1].get_legend_handles_labels()[0]:
        axes[1].legend(fontsize=8)
    fig.suptitle("Standalone volatility validation; diagnostic settings, not Gate 2 sign-off", fontsize=10)
    fig.savefig(figures / f"{name}_stability.png", dpi=160); plt.close(fig)
    if examples:
        rhos = sorted(set(r["persistence"] for r in examples))
        fig, axes = plt.subplots(len(rhos), 2, figsize=(11, 2.6 * len(rhos)), squeeze=False, layout="constrained")
        for index, rho in enumerate(rhos):
            rows = [r for r in examples if r["persistence"] == rho]
            axes[index, 0].plot([r["time"] for r in rows], [r["sigma"] for r in rows], linewidth=0.8)
            axes[index, 1].plot([r["time"] for r in rows], [r["return"] for r in rows], linewidth=0.6)
            axes[index, 0].set(ylabel=f"rho={rho:g}\nConditional SD", xlabel="Time")
            axes[index, 1].set(ylabel="Idiosyncratic return", xlabel="Time")
        fig.suptitle("One example firm; inference uses repeated independent panels", fontsize=10)
        fig.savefig(figures / f"{name}_paths.png", dpi=160); plt.close(fig)
    independence = summary["independence"]
    if independence.get("false_detection_rate") and independence.get("control_detection_rate"):
        measures = [independence["false_detection_rate"], independence["control_detection_rate"]]
        rates = np.array([r["rate"] for r in measures])
        bounds = np.array([r["wilson95"] for r in measures])
        fig, axis = plt.subplots(figsize=(7, 4), layout="constrained")
        axis.errorbar([0, 1], rates, yerr=np.maximum(0, np.array([rates - bounds[:, 0], bounds[:, 1] - rates])), fmt="o", capsize=5)
        axis.axhline(independence["diagnostic_alpha"], linestyle="--", color="gray", label="Diagnostic alpha")
        axis.set(xticks=[0, 1], xticklabels=["Independent construction", "Deliberately dependent control"],
                 ylabel="Detection rate (Wilson 95% intervals)", ylim=(-0.04, 1.04), title="Actual pinned regime component; independent panels")
        axis.legend()
        fig.savefig(figures / f"{name}_independence.png", dpi=160); plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/deeptanshu_validation.json"))
    parser.add_argument("--output-root", type=Path, default=Path("results"))
    parser.add_argument("--run-name", default="deeptanshu_validation")
    parser.add_argument("--quick", action="store_true", help="Toy pipeline smoke; not substantive validation")
    parser.add_argument("--overwrite", action="store_true", help="Replace this named run's generated output files")
    parser.add_argument("--skip-independence", action="store_true", help="Explicitly mark the actual-component check skipped")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_name):
        parser.error("run-name must contain only letters, digits, underscores, hyphens")
    config = copy.deepcopy(json.loads(args.config.read_text(encoding="utf-8")))
    if args.quick:
        config["label"] = "TOY PIPELINE SMOKE ONLY; not Gate 2 evidence"
        config["stability"].update(n_firms=8, n_periods=256, burn_in=100, long_burn_in=300, replications=3, persistence=[0.0, 0.9], acf_lags=10)
        config["independence"].update(replications=6, n_firms=8, n_periods=128, burn_in=100, randomizations=19)
        config["runtime"].update(n_firms=[8], n_periods=[128], repeats=1)
    validate_config(config)
    name = args.run_name + ("_quick" if args.quick else "")
    raw, tables, figures = (args.output_root / folder for folder in ("raw", "tables", "figures"))
    raw = raw / name
    if not args.overwrite and (raw.exists() or (tables / f"{name}.json").exists()):
        parser.error("Named run already exists; choose a new --run-name or use --overwrite")
    if args.overwrite:
        _clear_run_outputs(raw, tables, figures, name)
    raw.mkdir(parents=True, exist_ok=True)
    provenance = _provenance(config, raw)
    _json(raw / "provenance.json", provenance)
    started = time.perf_counter()
    stability_rows, stability, examples = run_stability(config["stability"], config["seed"])
    _csv(raw / "stability_replications.csv", stability_rows)
    if examples:
        _csv(raw / "selected_series.csv", examples)
    independence = {"status": "skipped by explicit CLI option"}
    if not args.skip_independence:
        try:
            with regime_reference(REPO, config["independence"]["regime_ref"], snapshot_dir=raw / "reference") as (simulator, metadata):
                independence_rows, independence = run_independence(config["independence"], config["stability"], config["seed"], simulator)
                independence["reference"] = metadata
                _json(raw / "independence_replications.json", independence_rows)
        except (subprocess.CalledProcessError, FileNotFoundError, ImportError, AttributeError) as error:
            independence = {"status": "blocked", "reason": str(error)}
    runtime = run_runtime(config["runtime"], config["seed"])
    _csv(raw / "runtime.csv", runtime)
    mock_rows, metrics = mock_metrics()
    _csv(raw / "mock_intervals.csv", mock_rows)
    summary = {"config": config, "stability": stability, "independence": independence,
               "mock_metrics": metrics, "runtime": runtime, "elapsed_seconds": time.perf_counter() - started,
               "source_sha256": provenance["source_sha256"], "git_head": provenance["git_head"],
               "environment": {key: provenance[key] for key in ("python", "numpy", "matplotlib", "platform")},
               "gate_status": "Not a team gate decision; validation configuration is provisional"}
    _json(tables / f"{name}.json", summary)
    _csv(tables / f"{name}_stability.csv", [{k: v for k, v in row.items() if k not in ("mean_acf", "acf_mcse", "population_acf")} for row in stability])
    plot_results(summary, examples, figures, name, raw / "mpl-cache")
    print(f"Saved summary: {tables / (name + '.json')}", flush=True)
    if independence.get("status") in ("blocked", "incomplete") or any(row["failed"] for row in stability):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
