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
import hashlib
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
                   if not cfg.get("approval", {}).get(k) or cfg.get("approval", {}).get(k) == AWAITING]
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


def _paired_block_id(condition_name, replication_id):
    return f"{condition_name}::rep_{int(replication_id):06d}"


def _world_fingerprint(data):
    """Fingerprint the shared inputs consumed by all four estimator cells."""
    digest = hashlib.sha256()
    for name in ("Y", "D", "X", "t0", "idx"):
        value = np.ascontiguousarray(np.asarray(data[name]))
        if value.dtype.kind not in "biuf":
            raise TypeError(f"World field {name} must have a numeric dtype")
        digest.update(name.encode("utf-8"))
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(json.dumps(value.shape).encode("ascii"))
        digest.update(memoryview(value).cast("B"))
    memberships = [[int(regime) for regime in member] for member in data["cluster_memberships"]]
    digest.update(json.dumps(memberships, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


def run_replication(cfg, values, condition, replication_id, root_seed, *, label, overrides=None):
    seed = int(root_seed) + int(replication_id)
    wcfg = world_config(cfg, values, condition, seed, overrides)
    block_id = _paired_block_id(condition["name"], replication_id)
    world_sha256 = None
    started = time.perf_counter()
    try:
        # One world is built once; the single run_dml call evaluates all four cells
        # against this exact shared object.
        data = build_world(wcfg)
        world_sha256 = _world_fingerprint(data)
        rows, runtime = run_dml(data, n_folds=int(values["estimator.n_folds"]), seed=seed,
                                alpha=1 - float(values["estimator.confidence_level"]))
        keys = [(r["folds"], r["variance"]) for r in rows]
        if len(rows) != len(CELL_MAP) or len(set(keys)) != len(CELL_MAP) or set(keys) != set(CELL_MAP.values()):
            raise RuntimeError("DML runner must return exactly one outcome for each of the four cells")
        by = {key: row for key, row in zip(keys, rows)}
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
    paired_status = "complete" if all(cell["status"] == "ok" for cell in cells) else "incomplete"
    for cell in cells:
        cell["paired_block_id"] = block_id
        cell["world_sha256"] = world_sha256
    return {"schema": "calendar_dml_v1", "label": label, "condition": condition["name"],
            "replication_id": int(replication_id), "seed": seed, "root_seed": int(root_seed),
            "config_hash": config_hash({"cfg": _jsonable(cfg), "values": _jsonable(values)}),
            "truth": condition["tau"], "world_config": asdict(wcfg), "cells": cells,
            "paired_block_id": block_id, "world_sha256": world_sha256,
            "paired_block_status": paired_status,
            "runtime": runtime, "total_seconds": time.perf_counter() - started}


def _jsonable(x):
    return json.loads(json.dumps(x, default=str))


def run_condition(cfg, condition, out_dir, reps, root_seed, *, smoke=False, budget_seconds=None,
                  overrides=None):
    """Run (or resume) one condition. Returns number of new replications saved."""
    if type(reps) is not int or reps < 1 or type(root_seed) is not int or root_seed < 0:
        raise ValueError("Require positive integer reps and nonnegative integer root_seed")
    if smoke and reps > SMOKE_MAX_REPS:
        raise ApprovalError(f"Smoke runs are limited to {SMOKE_MAX_REPS} replications")
    values = resolve_parameters(cfg, smoke=smoke)
    if not smoke and not isinstance(values.get("provenance.root_seed"), int):
        raise ApprovalError("Production run needs an approved integer provenance.root_seed")
    if not smoke:
        if root_seed != values["provenance.root_seed"] or reps != values["replications.count"] or overrides:
            raise ApprovalError("Production arguments must match approved root seed/count; overrides are smoke-only")
        if values["estimator.robust_variance"] != "overlap_sandwich_full_membership_CR0_normal" or values["estimator.learner"] != "RandomForestRegressor(n_estimators=40,min_samples_leaf=8,max_features=.5)":
            raise ApprovalError("Approved estimator choice is not implemented by this engine")
        if condition not in make_conditions(cfg, values):
            raise ApprovalError("Condition is outside the approved grid")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    label = "smoke_exploratory" if smoke else "production_approved"
    chash = config_hash({"cfg": _jsonable(cfg), "values": _jsonable(values)})
    source_root = Path(__file__).resolve().parents[2]
    sources = ["src/infra/dml_engine.py", "research/week2_completion/dgp.py", "research/week2_completion/dml.py"]
    hashes = {name: hashlib.sha256((source_root / name).read_bytes()).hexdigest() for name in sources}
    manifest_path = out_dir / "manifest.json"
    manifest = {"schema": "calendar_dml_v1", "label": label, "condition": condition, "reps_planned": reps,
                "root_seed": int(root_seed), "config_hash": chash, "values": _jsonable(values),
                "overrides": overrides or {}, "world_config": asdict(world_config(cfg, values, condition, root_seed, overrides)),
                "paired_block_contract": "one build_world result per replication; all four cells share its input fingerprint",
                "source_sha256": hashes, "git": git_state(), "software": software_versions()}
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        for key in ("config_hash", "root_seed", "condition", "label", "reps_planned", "overrides", "source_sha256", "software", "world_config", "paired_block_contract"):
            if old.get(key) != manifest[key]:
                raise ValueError(f"Existing run directory has a different {key}; refusing to mix runs")
    else:
        save_json_atomic(manifest_path, manifest)
    started, done = time.perf_counter(), 0
    for rep in range(reps):
        path = out_dir / f"rep_{rep:06d}.json"
        if path.exists():
            existing = json.loads(path.read_text())
            _validate_record(existing, manifest, rep)
            continue
        if budget_seconds is not None and time.perf_counter() - started > budget_seconds:
            break
        record = run_replication(cfg, values, condition, rep, root_seed, label=label, overrides=overrides)
        save_json_atomic(path, record)
        done += 1
    return done


def _validate_record(record, manifest, rep):
    expected = {"replication_id": rep, "seed": manifest["root_seed"] + rep,
                "root_seed": manifest["root_seed"], "truth": manifest["condition"]["tau"],
                "condition": manifest["condition"]["name"], "label": manifest["label"],
                "config_hash": manifest["config_hash"]}
    if any(type(record.get(k)) is not type(v) or record.get(k) != v for k, v in expected.items()):
        raise ValueError("Replication identity/seed/truth mismatch")
    expected_world = {**manifest["world_config"], "seed": manifest["root_seed"] + rep}
    if record.get("world_config") != expected_world:
        raise ValueError("Replication world configuration mismatch")
    cells = record.get("cells", [])
    if len(cells) != 4 or sorted(c.get("cell", "") for c in cells) != sorted(CELL_MAP):
        raise ValueError("Replication must contain four unique cells")
    pairing_fields = ("paired_block_id", "world_sha256", "paired_block_status")
    if manifest.get("paired_block_contract") and not all(field in record for field in pairing_fields):
        raise ValueError("Manifest requires paired-block metadata; refusing an unverifiable record")
    if any(field in record for field in pairing_fields):
        if not all(field in record for field in pairing_fields):
            raise ValueError("Paired-block metadata must be complete when present")
        expected_block = _paired_block_id(manifest["condition"]["name"], rep)
        if record["paired_block_id"] != expected_block:
            raise ValueError("Paired-block ID does not match the condition and replication")
        fingerprint = record["world_sha256"]
        if fingerprint is not None and (
            not isinstance(fingerprint, str) or len(fingerprint) != 64
            or any(ch not in "0123456789abcdef" for ch in fingerprint)
        ):
            raise ValueError("Invalid shared-world SHA-256 fingerprint")
        if fingerprint is None and any(cell.get("status") == "ok" for cell in cells):
            raise ValueError("Successful cells require a shared-world fingerprint")
        for cell in cells:
            if cell.get("paired_block_id") != expected_block or cell.get("world_sha256") != fingerprint:
                raise ValueError("Cell outcomes do not share the replication's paired-world identity")
        expected_status = "complete" if all(cell.get("status") == "ok" for cell in cells) else "incomplete"
        if record["paired_block_status"] != expected_status:
            raise ValueError("Paired-block status does not match the four cell outcomes")
    for cell in cells:
        if cell.get("status") not in ("ok", "failed"):
            raise ValueError("Invalid cell status")
        if cell["status"] == "failed" and not cell.get("error"):
            raise ValueError("Failed cells require an error")
        if cell["status"] == "ok":
            vals = [cell.get(k) for k in ("estimate", "lower", "upper")]
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) for v in vals) or vals[1] > vals[2]:
                raise ValueError("Invalid successful interval")


def aggregate(out_dir, *, allow_partial=False):
    """Summarise a condition; partial runs are opt-in and never hide unstarted replications."""
    out_dir = Path(out_dir)
    manifest = json.loads((out_dir / "manifest.json").read_text())
    reps, truth = manifest["reps_planned"], manifest["condition"]["tau"]
    records, missing_ids = [], []
    for rep in range(reps):
        path = out_dir / f"rep_{rep:06d}.json"
        if not path.is_file():
            missing_ids.append(rep)
            continue
        rec = json.loads(path.read_text())
        _validate_record(rec, manifest, rep)
        records.append(rec)
    if missing_ids and not allow_partial:
        raise FileNotFoundError(f"Missing planned replications: {missing_ids[:10]}")
    saved_ids = [int(record["replication_id"]) for record in records]
    cells, saved_hits = {}, {}
    for cell in CELL_MAP:
        rows = [next(c for c in record["cells"] if c["cell"] == cell) for record in records]
        ok = np.array([item["status"] == "ok" for item in rows], dtype=bool)
        lo = [item["lower"] if item["status"] == "ok" else np.nan for item in rows]
        hi = [item["upper"] if item["status"] == "ok" else np.nan for item in rows]
        if records:
            summary = summarize_intervals(lo, hi, truth, success=ok, failure_policy="report",
                                          expected_replications=len(records))
            covered = summary.coverage.successes if summary.coverage else 0
            failed_count = summary.failed
            bounds_saved = list(summary.coverage_bounds_all_attempted)
            coverage = summary.coverage.rate if summary.coverage else None
            coverage_mcse = summary.coverage.mcse if summary.coverage else None
            coverage_wilson = list(summary.coverage.wilson95) if summary.coverage else None
            size = summary.size.rate if summary.size else None
            power = summary.power.rate if summary.power else None
            mean_width = summary.mean_width
            conditional = summary.conditional_on_success
        else:
            covered, failed_count = 0, 0
            bounds_saved = None
            coverage = coverage_mcse = coverage_wilson = size = power = mean_width = None
            conditional = False
        bounds_planned = [covered / reps, (covered + failed_count + len(missing_ids)) / reps]
        cells[cell] = {"planned": reps, "attempted": len(records), "valid": int(ok.sum()),
                       "failed": failed_count, "not_started": len(missing_ids),
                       "coverage": coverage, "coverage_mcse": coverage_mcse,
                       "coverage_wilson95": coverage_wilson,
                       "coverage_bounds_all_attempted": bounds_saved,
                       "coverage_bounds_all_planned": bounds_planned,
                       "size": size, "power": power, "mean_width": mean_width,
                       "conditional_on_success": conditional}
        saved_hits[cell] = {
            int(record["replication_id"]): (bool(item["lower"] <= truth <= item["upper"])
                                             if item["status"] == "ok" else None)
            for record, item in zip(records, rows)
        }

    # Only a four-cell-successful block with a matching shared-world fingerprint
    # contributes to any paired comparison.
    complete_ids, incomplete_ids, unverified_ids = [], [], []
    for record in records:
        record_cells = record["cells"]
        has_verified_identity = (
            record.get("paired_block_id") == _paired_block_id(record["condition"], record["replication_id"])
            and isinstance(record.get("world_sha256"), str)
            and len(record["world_sha256"]) == 64
            and all(cell.get("paired_block_id") == record["paired_block_id"]
                    and cell.get("world_sha256") == record["world_sha256"] for cell in record_cells)
        )
        if not has_verified_identity:
            unverified_ids.append(record["replication_id"])
        elif all(cell["status"] == "ok" for cell in record_cells):
            complete_ids.append(record["replication_id"])
        else:
            incomplete_ids.append(record["replication_id"])

    paired_hits = {
        cell: {rep_id: saved_hits[cell][rep_id] for rep_id in complete_ids}
        for cell in CELL_MAP
    }
    pairs = {}
    comparisons = {
        "grouped_robust_minus_random_robust": ("grouped_xfit__robust_var", "random_xfit__robust_var"),
        "random_robust_minus_random_naive": ("random_xfit__robust_var", "random_xfit__naive_var"),
        "grouped_robust_minus_grouped_naive": ("grouped_xfit__robust_var", "grouped_xfit__naive_var"),
    }
    for name, (a, b) in comparisons.items():
        try:
            result = paired_binary_difference(paired_hits[a], paired_hits[b], failure_policy="report")
            pairs[name] = {"difference": result.difference, "mcse": result.mcse,
                           "valid_pairs": result.valid_pairs, "attempted_complete_blocks": len(complete_ids)}
        except ValueError as exc:
            pairs[name] = {"error": str(exc), "valid_pairs": 0,
                           "attempted_complete_blocks": len(complete_ids)}
    return {"label": manifest["label"], "condition": manifest["condition"]["name"], "reps": reps,
            "planned_reps": reps, "saved_reps": len(records), "not_started_reps": len(missing_ids),
            "execution_status": "partial" if missing_ids else "planned_budget_attempted",
            "truth": truth, "cells": cells, "paired": pairs,
            "paired_audit": {"planned_blocks": reps, "saved_blocks": len(records),
                             "complete_blocks": len(complete_ids), "incomplete_blocks": len(incomplete_ids),
                             "unverified_blocks": len(unverified_ids), "not_started_blocks": len(missing_ids),
                             "complete_block_replication_ids": complete_ids,
                             "incomplete_block_replication_ids": incomplete_ids,
                             "unverified_block_replication_ids": unverified_ids}}


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
    ap.add_argument("--allow-partial", action="store_true",
                    help="report a partially executed condition, including planned but unstarted replications")
    ap.add_argument("--override", nargs="*", default=[], help="smoke world-size overrides, e.g. n=120 T=60")
    a = ap.parse_args(argv)
    if a.action == "aggregate":
        print(json.dumps(aggregate(a.out, allow_partial=a.allow_partial), indent=1))
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
