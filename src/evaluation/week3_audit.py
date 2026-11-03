"""Audit saved Week 3 results independently, without running or importing DML.

Run --help for the canonical CSV interface. Missing/failed attempts are visible
in saved reports; default CLI exit 2 blocks a misleading successful verification.
No command in this module launches an experiment or approves a scientific gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from src.evaluation.verification import (
    CELLS, REQUIRED_COLUMNS, audit_results, audit_stability, compare_claims,
    file_hash, finite, identity, read_csv, validate_plan,
)


def read_json(path):
    def reject_constant(value):
        raise ValueError(f"Non-standard JSON number: {value}")

    def unique_pairs(pairs):
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError(f"Duplicate JSON key: {key}")
            data[key] = value
        return data

    def finite_json_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Unrepresentable JSON floating-point number")
        return result

    return json.loads(Path(path).read_text(encoding="utf-8"), parse_float=finite_json_float,
                      parse_constant=reject_constant, object_pairs_hook=unique_pairs)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".audit-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_runner_records(run_dir, scenario):
    """Read the merged mock-runner JSON format using independent validation.

    Auto-adaptation is explicitly mock-only. A future scientific runner should
    export the canonical CSV; it is not silently assumed to share this contract.
    Returns metadata and the input files for content-addressed provenance.
    """
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("config"), dict):
        raise ValueError("Runner manifest must contain a config mapping")
    config = manifest["config"]
    if config.get("engine") != "mock":
        raise ValueError("The existing runner adapter is mock-only")
    if manifest.get("source_changed_during_run"):
        raise ValueError("Producer invalidated run because source changed")
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)
    expected_hash = hashlib.sha256(canonical.encode()).hexdigest()
    if manifest.get("config_hash") != expected_hash:
        raise ValueError("Runner configuration fingerprint mismatch")
    seed = config["provenance"]["seed"]
    if (type(seed) is not int or seed < 0 or type(manifest.get("root_seed")) is not int
            or manifest["root_seed"] != seed):
        raise ValueError("Invalid runner root seed")
    count = config["replications"]["count"]
    if type(count) is not int or count < 1:
        raise ValueError("Invalid runner replication count")
    truth = finite(config["_resolved_dgp"]["treatment"]["effect_true"], "truth")
    stream_ids = {"factors": 0, "volatility": 1, "regimes": 2, "treatment": 3, "estimator": 4}
    if (manifest.get("rng_stream_ids") != stream_ids
            or not all(type(value) is int for value in manifest.get("rng_stream_ids", {}).values())):
        raise ValueError("Runner stream metadata mismatch")
    records = []
    paths = [manifest_path]
    for path in sorted(run_dir.glob("rep_*.json")):
        record = read_json(path)
        if not isinstance(record, dict):
            raise ValueError("Runner record must be a mapping")
        replication = record.get("replication_id")
        if type(replication) is not int or not 0 <= replication < count:
            raise ValueError("Unplanned runner replication")
        if path.name != f"rep_{replication:06d}.json":
            raise ValueError("Runner filename and replication ID disagree")
        expected = {"run_id": manifest["run_id"], "root_seed": seed,
                    "config_hash": expected_hash, "truth": truth,
                    "seed_addresses": {key: [seed, replication, value] for key, value in stream_ids.items()}}
        addresses = record.get("seed_addresses")
        if (type(record.get("root_seed")) is not int
                or finite(record.get("truth"), "saved truth") != truth
                or not isinstance(addresses, dict)
                or not all(isinstance(values, list) and len(values) == 3
                           and all(type(value) is int for value in values) for values in addresses.values())):
            raise ValueError("Malformed runner numeric provenance")
        if any(record.get(key) != value for key, value in expected.items()):
            raise ValueError("Runner replication provenance mismatch")
        cells = record.get("cells")
        if (not isinstance(cells, list) or len(cells) != 4
                or not all(isinstance(cell, dict) for cell in cells)
                or sorted(cell.get("cell", "") for cell in cells) != sorted(CELLS)):
            raise ValueError("Runner record must contain four unique cells")
        for cell in cells:
            records.append({**cell, "scenario": scenario, "replication": str(replication),
                            "panel_id": f"{manifest['run_id']}:{replication}",
                            "truth": truth, "confidence_level": .95})
        paths.append(path)
    return records, {"kind": "mock", "truth": truth, "replications": count,
                     "producer_manifest": manifest}, paths


def compare_paired_claims(report, claims, *, atol=1e-12, rtol=1e-10):
    if not isinstance(claims, (list, tuple)) or not all(isinstance(row, dict) for row in claims):
        raise ValueError("Claimed comparisons must be a list of mappings")
    atol, rtol = finite(atol, "atol"), finite(rtol, "rtol")
    if atol < 0 or rtol < 0:
        raise ValueError("Comparison tolerances must be nonnegative")
    expected = {(row["scenario"], row["a"], row["b"], row["outcome"]): row
                for row in report["comparisons"]}
    required = {key for key, row in expected.items() if row["central_comparison"]}
    observed = {}
    for row in claims:
        key = tuple(identity(row.get(field), "claimed " + field) for field in ("scenario", "a", "b", "outcome"))
        if key in observed:
            raise ValueError("Duplicate claimed paired comparison")
        observed[key] = row
    differences = []
    for key in sorted(required | observed.keys()):
        if key not in expected or key not in observed:
            differences.append({"comparison": list(key), "reason": "missing or unplanned comparison"})
            continue
        for field in ("difference", "mcse", "valid_pairs", "planned_pairs", "excluded_pairs"):
            actual = expected[key][field]
            claimed = observed[key].get(field)
            try:
                if claimed in (None, "", "N/A", "null"):
                    matches = actual is None and field in observed[key]
                else:
                    number = finite(claimed)
                    matches = actual is not None and (number == actual if field.endswith("pairs") else
                        math.isclose(number, actual, abs_tol=atol, rel_tol=rtol))
            except ValueError:
                matches = False
            if not matches:
                differences.append({"comparison": list(key), "field": field,
                                    "recomputed": actual, "claimed": str(claimed)})
        if observed[key].get("direction") != "a_minus_b":
            differences.append({"comparison": list(key), "field": "direction",
                                "reason": "direction must be a_minus_b"})
    return {"status": "matched" if not differences else "discrepancies", "discrepancies": differences}


def audit_manipulation(rows, plan):
    """Apply only supplied plan thresholds; never infer them from outcomes."""
    scenarios = validate_plan(plan)
    checks = plan.get("manipulation_checks", [])
    if not isinstance(checks, list) or not all(isinstance(check, dict) for check in checks):
        raise ValueError("Manipulation checks must be a list of mappings")
    if not checks:
        return {"status": "pending", "reason": "No locked manipulation-check definitions supplied",
                "records": rows}
    expected = {}
    operators = {">=": lambda a, b: a >= b, ">": lambda a, b: a > b,
                 "<=": lambda a, b: a <= b, "<": lambda a, b: a < b}
    for check in checks:
        name = identity(check.get("name"), "diagnostic")
        operator = check.get("operator")
        if operator not in operators:
            raise ValueError("Manipulation operator must be >=, >, <= or <")
        threshold = finite(check.get("threshold"), "threshold")
        targets = check.get("scenarios")
        if not isinstance(targets, list) or not targets or len(set(targets)) != len(targets):
            raise ValueError("Manipulation check needs unique scenario targets")
        for target in targets:
            if target not in scenarios:
                raise ValueError("Unplanned manipulation-check scenario")
            for cell in CELLS:
                key = target, cell, name
                if key in expected:
                    raise ValueError("Duplicate planned manipulation check")
                expected[key] = operator, threshold
    saved = {}
    for row in rows:
        key = tuple(row.get(field) for field in ("scenario", "cell", "diagnostic"))
        if key not in expected or key in saved:
            raise ValueError("Unexpected or duplicate manipulation-check result")
        saved[key] = row
    results = []
    for key, (operator, threshold) in expected.items():
        if key not in saved:
            results.append({"scenario": key[0], "cell": key[1], "diagnostic": key[2], "status": "missing"})
        else:
            value = finite(saved[key].get("value"), "manipulation value")
            results.append({"scenario": key[0], "cell": key[1], "diagnostic": key[2],
                            "value": value, "operator": operator, "threshold": threshold,
                            "status": "pass" if operators[operator](value, threshold) else "review"})
    return {"status": "evaluated" if all(row["status"] == "pass" for row in results) else "review",
            "threshold_origin": "Input plan; approval not established by the software", "records": results}


def audit_trace(rows, *, limits=None, plan=None):
    """Inspect optional raw numerical traces; count all flags, retain 100 examples."""
    expected = None
    if plan is not None:
        scenarios = validate_plan(plan)
        expected = {(name, replication, cell) for name, scenario in scenarios.items()
                    for replication in scenario["replication_ids"] for cell in CELLS}
    covered = set()
    coordinates = set()
    limits = limits or {}
    limits = {name: finite(limit, "trace limit") for name, limit in limits.items()}
    if any(limit <= 0 for limit in limits.values()):
        raise ValueError("Absolute trace limits must be positive")
    counts = {"values": 0, "nonfinite_or_malformed": 0, "nonpositive_variance": 0,
              "nonpositive_standard_deviation": 0, "extreme": 0}
    examples = []
    flagged = 0
    for row in rows:
        if not {"scenario", "replication", "cell", "component", "quantity", "value"} <= row.keys():
            raise ValueError("Numerical trace lacks required metadata")
        if row["cell"] not in CELLS:
            raise ValueError("Invalid trace cell")
        key = (identity(row["scenario"], "trace scenario"), identity(row["replication"], "trace replication"), row["cell"])
        if expected is not None and key not in expected:
            raise ValueError("Unplanned numerical trace record")
        covered.add(key)
        component, quantity = identity(row["component"], "component"), identity(row["quantity"], "quantity")
        if row.get("coordinate") not in (None, ""):
            coordinate_key = (*key, component, quantity, identity(row["coordinate"], "coordinate"))
            if coordinate_key in coordinates:
                raise ValueError("Duplicate numerical trace coordinate")
            coordinates.add(coordinate_key)
        counts["values"] += 1
        problems = []
        try:
            value = finite(row["value"])
            if quantity in ("variance", "conditional_variance", "conditional_std", "sigma") and value <= 0:
                problem = "nonpositive_variance" if quantity in ("variance", "conditional_variance") else "nonpositive_standard_deviation"
                counts[problem] += 1
                problems.append(problem)
            if quantity in limits and abs(value) > limits[quantity]:
                counts["extreme"] += 1
                problems.append("extreme_review_flag")
        except ValueError:
            counts["nonfinite_or_malformed"] += 1
            problems.append("nonfinite_or_malformed")
        if problems:
            flagged += 1
            if len(examples) < 100:
                examples.append({**row, "value": str(row["value"]), "problems": problems})
    status = "review" if flagged else ("screened" if rows else "not_supplied")
    if status == "screened" and expected is not None and covered != expected:
        status = "partial"
    return {"status": status, "counts": counts,
            "planned_cell_attempts": len(expected) if expected is not None else None,
            "cell_attempts_with_trace": len(covered),
            "cell_attempts_without_trace": len(expected - covered) if expected is not None else None,
            "flagged_values": flagged, "examples": examples, "examples_truncated": flagged > len(examples),
            "limits": limits, "interpretation": "Only supplied traces screened; no clipping or imputation"}


def provenance(paths, *, extra_sources=()):
    root = Path(__file__).resolve().parents[2]
    try:
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        head, dirty = "unavailable", True
    source = [Path(__file__), Path(__file__).with_name("verification.py"), *map(Path, extra_sources)]
    return {"created_utc": datetime.now(timezone.utc).isoformat(), "git_commit": head,
            "git_dirty": dirty, "python": platform.python_version(),
            "input_sha256": {str(Path(path)): file_hash(path) for path in paths},
            "verifier_source_sha256": {path.name: file_hash(path) for path in source}}


def save_source_snapshot(output, recorded, *, extra_sources=()):
    """Retain exact uncommitted verifier sources alongside a content hash."""
    root = Path(__file__).resolve().parents[2]
    sources = [Path(__file__), Path(__file__).with_name("verification.py"), *map(Path, extra_sources)]
    destination = Path(output) / "verifier_sources.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sources:
            if file_hash(path) != recorded["verifier_source_sha256"][path.name]:
                raise ValueError("Verifier source changed during audit")
            archive.write(path, path.resolve().relative_to(root).as_posix())
    return {"path": destination.name, "sha256": file_hash(destination)}


def markdown_report(report):
    lines = ["# Week 3 independent saved-results audit", "", f"Evidence: **{report['evidence_kind']}**.", "",
             "This report verifies saved arithmetic; it does not approve a scientific gate.", "",
             "| Scenario | Cell | Planned | Valid | Failed | Missing | Coverage (MCSE) | Size/power (MCSE) |",
             "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |"]
    def display(value):
        return "N/A" if value is None else f"{value:.6g}"
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    for row in report["summaries"]:
        kind = "size" if row["truth"] == 0 else "power"
        rate = row["empirical_size"] if kind == "size" else row["power"]
        lines.append(f"| {escape(row['scenario'])} | {row['cell']} | {row['planned']} | {row['valid']} | "
                     f"{row['failed']} | {row['missing']} | {display(row['coverage95'])} ({display(row['coverage_mcse'])}) | "
                     f"{kind}: {display(rate)} ({display(row[kind + '_mcse'])}) |")
    lines.extend(["", "Rates are conditional on success when records fail or are missing. Full JSON includes all-planned coverage bounds, "
                  "Wilson intervals, paired Monte Carlo errors, bias and RMSE. A zero boundary MCSE does not imply certainty.", "",
                  "## Open audit items", ""])
    for item in report.get("open_items", []):
        lines.append("- " + escape(item))
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--raw", type=Path, help="Saved canonical CSV; one row per scenario/replication/cell")
    source.add_argument("--runner-dir", type=Path, help="Existing mock-runner directory (mock plans only)")
    parser.add_argument("--scenario", help="Scenario ID for the single-scenario mock runner adapter")
    parser.add_argument("--claims", type=Path, help="Claimed summary CSV or JSON with summaries/cells")
    parser.add_argument("--paired-claims", type=Path)
    parser.add_argument("--manipulation", type=Path)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="New report directory")
    parser.add_argument("--atol", type=float, default=1e-12)
    parser.add_argument("--rtol", type=float, default=1e-10)
    parser.add_argument("--estimate-limit", type=float)
    parser.add_argument("--allow-incomplete", action="store_true", help="Save partial monitoring snapshot with exit 0; does not mark it complete")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output directory already exists; choose a new snapshot name")
    if (not math.isfinite(args.atol) or not math.isfinite(args.rtol)
            or args.atol < 0 or args.rtol < 0):
        parser.error("Comparison tolerances must be finite and nonnegative")
    # Atomically reserve a new report directory, before any report writes.
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        parser.error(f"Cannot reserve a new output directory: {exc}")
    stability = None
    inputs = [args.plan]
    if args.raw:
        inputs.append(args.raw)
    if args.runner_dir:
        inputs += [args.runner_dir / "manifest.json", *sorted(args.runner_dir.glob("rep_*.json"))]
    inputs += [path for path in (args.claims, args.paired_claims, args.manipulation, args.trace) if path]
    inputs = list(dict.fromkeys(inputs))
    try:
        before = provenance(inputs)
        before_hashes = before["input_sha256"]
        plan = read_json(args.plan)
        scenarios = validate_plan(plan)
        if args.raw:
            rows = read_csv(args.raw, REQUIRED_COLUMNS)
            inputs.append(args.raw)
        else:
            if plan["evidence_kind"] != "mock" or len(scenarios) != 1:
                raise ValueError("Existing runner adapter needs a single-scenario mock plan")
            name = args.scenario or next(iter(scenarios))
            rows, metadata, paths = load_runner_records(args.runner_dir, name)
            inputs.extend(paths)
        stability = audit_stability(rows, absolute_estimate_limit=args.estimate_limit)
        report = audit_results(rows, plan)
        if args.runner_dir:
            report["producer_metadata"] = metadata
        report["saved_output_stability"] = stability
        report["open_items"] = []
        report["claims_comparison"] = {"status": "not_supplied"}
        if args.claims:
            if args.claims.suffix.lower() == ".csv":
                claims = read_csv(args.claims)
            else:
                data = read_json(args.claims)
                if not isinstance(data, dict):
                    raise ValueError("Claimed JSON must be a mapping")
                if data.get("engine") == "mock" and plan["evidence_kind"] != "mock":
                    raise ValueError("Mock producer output cannot verify scientific simulation claims")
                if "known_truth" in data and len(scenarios) == 1:
                    if finite(data["known_truth"], "claimed truth") != next(iter(scenarios.values()))["truth"]:
                        raise ValueError("Claimed top-level truth differs from plan")
                claims = data.get("summaries", data.get("cells"))
                if claims is None:
                    raise ValueError("Claimed JSON lacks summaries or cells")
                # Existing single-run reports put the scenario/planned count at top level.
                if len(scenarios) == 1:
                    claims = [{"scenario": next(iter(scenarios)), **row,
                               "planned": row.get("planned", data.get("planned_replications")),
                               "missing": row.get("missing", 0)} for row in claims]
            report["claims_comparison"] = compare_claims(report, claims, atol=args.atol, rtol=args.rtol)
            inputs.append(args.claims)
        report["paired_claims_comparison"] = {"status": "not_supplied"}
        if args.paired_claims:
            paired = read_csv(args.paired_claims)
            report["paired_claims_comparison"] = compare_paired_claims(report, paired, atol=args.atol, rtol=args.rtol)
            inputs.append(args.paired_claims)
        manipulation = read_csv(args.manipulation) if args.manipulation else []
        report["manipulation_checks"] = audit_manipulation(manipulation, plan)
        if args.manipulation:
            inputs.append(args.manipulation)
        report["numerical_trace"] = {"status": "not_supplied"}
        if args.trace:
            report["numerical_trace"] = audit_trace(read_csv(args.trace), limits=plan.get("trace_absolute_limits"), plan=plan)
            inputs.append(args.trace)
        report["plan"] = plan
        for field in ("claims_comparison", "paired_claims_comparison"):
            if report[field]["status"] != "matched":
                report["open_items"].append(field + ": " + report[field]["status"])
        if report["issues"]:
            report["open_items"].append("Missing/failed planned attempts; summaries show success-conditioned values")
        if report["manipulation_checks"]["status"] != "evaluated":
            report["open_items"].append("Manipulation checks need producer evidence and locked definitions")
        if report["numerical_trace"]["status"] != "screened":
            report["open_items"].append("DGP/nuisance numerical traces unavailable; only saved estimates screened")
        report["open_items"].append("Gate 2/3 decision records and scientific interpretation require team review")
        inputs = list(dict.fromkeys(inputs))
        report["provenance"] = provenance(inputs)
        if report["provenance"]["input_sha256"] != before_hashes:
            raise ValueError("Inputs changed during audit; repeat on a frozen snapshot")
        if report["provenance"]["verifier_source_sha256"] != before["verifier_source_sha256"]:
            raise ValueError("Verifier source changed during audit")
        report["provenance"]["source_archive"] = save_source_snapshot(args.output, report["provenance"])
        write_json(args.output / "audit.json", report)
        (args.output / "audit.md").write_text(markdown_report(report), encoding="utf-8")
        print(f"Saved independent audit: {args.output / 'audit.json'}")
        missing = any(row["missing"] for row in report["summaries"])
        failures = any(row["failed"] for row in report["summaries"])
        failed = (missing and not args.allow_incomplete) or (failures and plan["failure_policy"] == "raise")
        failed |= any(report[field]["status"] == "discrepancies"
                      for field in ("claims_comparison", "paired_claims_comparison"))
        failed |= any(value for key, value in stability["counts"].items()
                      if key not in ("records", "failed", "producer_recorded_failure"))
        failed |= report["numerical_trace"]["status"] == "review"
        failed |= report["manipulation_checks"]["status"] == "review"
        if plan["evidence_kind"] == "simulation":
            failed |= any(report[field]["status"] != "matched"
                          for field in ("claims_comparison", "paired_claims_comparison"))
            failed |= report["manipulation_checks"]["status"] != "evaluated"
        return 2 if failed else 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as exc:
        print(f"Audit input error: {exc}")
        # Preserve why a snapshot failed; do not emit partial metric summaries.
        try:
            write_json(args.output / "input_error.json", {
                "status": "invalid_input", "error": str(exc),
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [str(path) for path in dict.fromkeys(inputs)],
                "saved_output_stability": stability,
                "gate_approval": "Not granted; no metrics verified",
            })
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
