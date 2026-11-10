"""Separate `calendar_dml` engine hook for the four-cell study (NOT part of the mock runner).

* Runs the UNMODIFIED research.week2_completion DGP and DML; no estimator/DGP change.
* Emits the same per-cell record schema as src/infra/experiment_runner.py
  (cell, status, estimate, lower, upper, error) plus diagnostics, so existing readers can parse it.
* Production runs are refused unless the team approvals are recorded and no parameter's
  `approved` value is AWAITING_TEAM_APPROVAL. `smoke=True` may use `proposed` values, is limited to
  SMOKE_MAX_REPS replications, and every record is labelled exploratory.
* Per-replication atomic JSON, resumable, failures retained, deterministic seed = root_seed + replication_id.
* Aggregation uses src.evaluation.metrics (no new metric engine).
No production campaign is started by importing or testing this module.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import yaml

from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import run_dml
from src.evaluation.metrics import paired_binary_difference, summarize_intervals
from src.infra.reproducibility import config_hash, git_state, save_json_atomic, software_versions

AWAITING = "AWAITING_TEAM_APPROVAL"
APPROVED_AS_PROPOSED = "APPROVED_AS_PROPOSED"
SMOKE_MAX_REPS = 20
CELL_MAP = {"random_xfit__naive_var": ("random", "naive"),
            "random_xfit__robust_var": ("random", "multiway"),
            "grouped_xfit__naive_var": ("grouped", "naive"),
            "grouped_xfit__robust_var": ("grouped", "multiway")}


class ApprovalError(RuntimeError):
    """Raised when a production run is requested without recorded team approval."""


def load_proposal(path):
    return yaml.safe_load(Path(path).read_text())


def _iter_parameters(cfg):
    for section in ("dgp", "estimator"):
        for name, spec in cfg.get(section, {}).get("parameters", {}).items():
            yield f"{section}.{name}", spec
    for section in ("replications", "provenance", "failure_policy", "decision_rules"):
        for name, spec in cfg.get(section, {}).items():
            if isinstance(spec, dict) and "approved" in spec:
                yield f"{section}.{name}", spec
    if isinstance(cfg.get("robustness_subset"), dict) and "approved" in cfg["robustness_subset"]:
        yield "robustness_subset", cfg["robustness_subset"]


def awaiting_paths(node, path=""):
    """Every dotted path whose `approved` field is still AWAITING_TEAM_APPROVAL, anywhere in the config."""
    found = []
    if isinstance(node, dict):
        if node.get("approved") == AWAITING:
            found.append(path or "<root>")
        for key, value in node.items():
            if key != "approved":
                found += awaiting_paths(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found += awaiting_paths(value, f"{path}[{i}]")
    return found


def resolve_parameters(cfg, *, smoke=False):
    """Return {dotted_name: value}. Production requires approvals; smoke uses proposed values."""
    if not smoke:
        missing = [k for k in ("gate2", "gate3", "approved_by", "approval_date")
                   if cfg.get("approval", {}).get(k, AWAITING) == AWAITING]
        if missing:
            raise ApprovalError(f"Production run refused; approval fields not recorded: {missing}")
        pending = awaiting_paths(cfg)
        if pending:
            raise ApprovalError(f"Production run refused; {len(pending)} fields still {AWAITING}: {pending[:5]}")
    values = {}
    for name, spec in _iter_parameters(cfg):
        approved = spec["approved"]
        if smoke:
            values[name] = spec["proposed"]
        elif approved == AWAITING:
            raise ApprovalError(f"Production run refused; {name} is {AWAITING}")
        else:
            values[name] = spec["proposed"] if approved == APPROVED_AS_PROPOSED else approved
    return values


def make_conditions(cfg, values):
    """Cartesian grid over density x K x gamma, each at tau=coverage and a separate tau=null condition."""
    tau = values["dgp.tau"]
    conditions = []
    for d, K, g in itertools.product(values["dgp.density"], values["dgp.n_regimes"], values["dgp.gamma"]):
        for kind in ("coverage", "zero_effect"):
            conditions.append({"name": f"d{d:g}_K{K}_g{g:g}_{kind}", "density": float(d), "K": int(K),
                               "gamma": float(g), "tau": float(tau[kind]), "kind": kind})
    return conditions


def world_config(cfg, values, condition, seed, overrides=None):
    fixed = {**cfg["dgp"]["fixed"], **(overrides or {})}
    return Config(**fixed, persistence=float(values["dgp.persistence"]), sd_factor=float(values["dgp.sd_factor"]),
                  density=condition["density"], n_regimes=condition["K"], gamma=condition["gamma"],
                  tau=condition["tau"], seed=int(seed))


def failed_cells(message):
    return [{"cell": c, "status": "failed", "estimate": None, "lower": None, "upper": None,
             "error": message, "se": None} for c in CELL_MAP]


def run_replication(cfg, values, condition, replication_id, root_seed, *, label, overrides=None):
    seed = int(root_seed) + int(replication_id)
    wcfg = world_config(cfg, values, condition, seed, overrides)
    started = time.perf_counter()
    try:
        data = build_world(wcfg)
        rows, runtime = run_dml(data, n_folds=int(values["estimator.n_folds"]), seed=seed,
                                alpha=1 - float(values["estimator.confidence_level"]))
        by = {(r["folds"], r["variance"]): r for r in rows}
        cells = []
        for cell, key in CELL_MAP.items():
            r = by[key]
            ok = r["status"] == "ok"
            cells.append({"cell": cell, "status": "ok" if ok else "failed",
                          "estimate": r["tau"] if ok else None, "lower": r["lo"] if ok else None,
                          "upper": r["hi"] if ok else None, "error": None if ok else r["error"],
                          "se": r["se"] if ok else None, "point_estimate": r["tau"],
                          "n_dependency_pairs": r["n_dependency_pairs"]})
    except Exception as exc:                                  # retained, never dropped
        cells, runtime = failed_cells(f"{type(exc).__name__}: {exc}"), {}
    return {"schema": "calendar_dml_v1", "label": label, "condition": condition["name"],
            "replication_id": int(replication_id), "seed": seed, "root_seed": int(root_seed),
            "config_hash": config_hash({"cfg": _jsonable(cfg), "values": _jsonable(values)}),
            "truth": condition["tau"], "world_config": asdict(wcfg), "cells": cells,
            "runtime": runtime, "total_seconds": time.perf_counter() - started}


def _jsonable(x):
    return json.loads(json.dumps(x, default=str))


def run_condition(cfg, condition, out_dir, reps, root_seed, *, smoke=False, budget_seconds=None,
                  overrides=None):
    """Run (or resume) one condition. Returns number of new replications saved."""
    if smoke and reps > SMOKE_MAX_REPS:
        raise ApprovalError(f"Smoke runs are limited to {SMOKE_MAX_REPS} replications")
    values = resolve_parameters(cfg, smoke=smoke)
    if not smoke and not isinstance(values.get("provenance.root_seed"), int):
        raise ApprovalError("Production run needs an approved integer provenance.root_seed")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    label = "smoke_exploratory" if smoke else "production_approved"
    chash = config_hash({"cfg": _jsonable(cfg), "values": _jsonable(values)})
    manifest_path = out_dir / "manifest.json"
    manifest = {"schema": "calendar_dml_v1", "label": label, "condition": condition, "reps_planned": reps,
                "root_seed": int(root_seed), "config_hash": chash, "values": _jsonable(values),
                "overrides": overrides or {}, "git": git_state(), "software": software_versions()}
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        for key in ("config_hash", "root_seed", "condition", "label", "reps_planned", "overrides"):
            if old[key] != manifest[key]:
                raise ValueError(f"Existing run directory has a different {key}; refusing to mix runs")
    else:
        save_json_atomic(manifest_path, manifest)
    started, done = time.perf_counter(), 0
    for rep in range(reps):
        path = out_dir / f"rep_{rep:06d}.json"
        if path.exists():
            continue
        if budget_seconds is not None and time.perf_counter() - started > budget_seconds:
            break
        record = run_replication(cfg, values, condition, rep, root_seed, label=label, overrides=overrides)
        save_json_atomic(path, record)
        done += 1
    return done


def aggregate(out_dir):
    """Summarise a completed condition directory; every planned replication must exist."""
    out_dir = Path(out_dir)
    manifest = json.loads((out_dir / "manifest.json").read_text())
    reps, truth = manifest["reps_planned"], manifest["condition"]["tau"]
    records = []
    for rep in range(reps):
        path = out_dir / f"rep_{rep:06d}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing planned replication {rep}")
        rec = json.loads(path.read_text())
        if rec["replication_id"] != rep or rec["config_hash"] != manifest["config_hash"]:
            raise ValueError(f"Replication record mismatch: {path}")
        records.append(rec)
    cells, hits = {}, {}
    for cell in CELL_MAP:
        rows = [next(c for c in r["cells"] if c["cell"] == cell) for r in records]
        ok = np.array([c["status"] == "ok" for c in rows])
        lo = [c["lower"] if c["status"] == "ok" else np.nan for c in rows]
        hi = [c["upper"] if c["status"] == "ok" else np.nan for c in rows]
        s = summarize_intervals(lo, hi, truth, success=ok, failure_policy="report", expected_replications=reps)
        cells[cell] = {"attempted": s.attempted, "valid": s.valid, "failed": s.failed,
                       "coverage": s.coverage.rate if s.coverage else None,
                       "coverage_mcse": s.coverage.mcse if s.coverage else None,
                       "coverage_wilson95": list(s.coverage.wilson95) if s.coverage else None,
                       "coverage_bounds_all_attempted": s.coverage_bounds_all_attempted,
                       "size": s.size.rate if s.size else None, "power": s.power.rate if s.power else None,
                       "mean_width": s.mean_width, "conditional_on_success": s.conditional_on_success}
        hits[cell] = {i: (bool(l <= truth <= u) if o else None)
                      for i, (l, u, o) in enumerate(zip(lo, hi, ok))}
    pairs = {}
    for name, (a, b) in {"grouped_robust_minus_random_robust": ("grouped_xfit__robust_var", "random_xfit__robust_var"),
                         "random_robust_minus_random_naive": ("random_xfit__robust_var", "random_xfit__naive_var"),
                         "grouped_robust_minus_grouped_naive": ("grouped_xfit__robust_var", "grouped_xfit__naive_var")}.items():
        try:
            p = paired_binary_difference(hits[a], hits[b], failure_policy="report")
            pairs[name] = {"difference": p.difference, "mcse": p.mcse, "valid_pairs": p.valid_pairs}
        except ValueError as exc:
            pairs[name] = {"error": str(exc)}
    return {"label": manifest["label"], "condition": manifest["condition"]["name"], "reps": reps,
            "truth": truth, "cells": cells, "paired": pairs}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["run", "aggregate"])
    ap.add_argument("--config", default="configs/mirun_gate3.yaml")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--condition-index", type=int, default=0)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--root-seed", type=int)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--budget-seconds", type=float)
    ap.add_argument("--override", nargs="*", default=[], help="smoke world-size overrides, e.g. n=120 T=60")
    a = ap.parse_args(argv)
    if a.action == "aggregate":
        print(json.dumps(aggregate(a.out), indent=1))
        return 0
    cfg = load_proposal(a.config)
    values = resolve_parameters(cfg, smoke=a.smoke)
    seed = a.root_seed if a.root_seed is not None else values.get("provenance.root_seed")
    if not isinstance(seed, int):
        raise ApprovalError("A numeric --root-seed is required (the proposal root seed is not approved)")
    overrides = {k: int(v) for k, v in (kv.split("=") for kv in a.override)}
    cond = make_conditions(cfg, values)[a.condition_index]
    n = run_condition(cfg, cond, a.out, a.reps, seed, smoke=a.smoke, budget_seconds=a.budget_seconds,
                      overrides=overrides)
    print(json.dumps({"condition": cond["name"], "saved_this_call": n}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
