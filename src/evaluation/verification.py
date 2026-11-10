"""Independent Week 3 arithmetic on saved estimates, never estimator inputs.

Uses only Python's standard library: no imports from metrics, the runner or DML.
Independent replications (whole panels) are the uncertainty unit. See the input
contract in docs/week3_verification.md and Morris et al. (2019), Table 6.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from statistics import NormalDist

CELLS = (
    "random_xfit__naive_var", "random_xfit__robust_var",
    "grouped_xfit__naive_var", "grouped_xfit__robust_var",
)
REQUIRED_COLUMNS = {
    "scenario", "replication", "cell", "panel_id", "truth", "estimate",
    "lower", "upper", "status", "confidence_level",
}
COUNT_FIELDS = {"planned", "attempted", "valid", "failed", "missing"}


def finite(value, name="value"):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def identity(value, name="ID"):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{name} must be a nonempty string or integer")
    result = str(value).strip()
    if not result or len(result) > 256:
        raise ValueError(f"{name} must have 1 to 256 characters")
    return result


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path, required=()):
    """Strict CSV reader: duplicate headers and truncated/overwide rows fail."""
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if not columns or len(columns) != len(set(columns)) or "" in columns:
            raise ValueError("CSV needs nonempty unique column names")
        if not set(required) <= set(columns):
            raise ValueError(f"CSV missing columns: {sorted(set(required) - set(columns))}")
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV row {line}")
            rows.append(row)
    return rows


def validate_plan(plan):
    """Validate declared expected attempts; this does not approve a design."""
    if (not isinstance(plan, dict) or type(plan.get("schema_version")) is not int
            or plan["schema_version"] != 1):
        raise ValueError("Plan schema_version must be 1")
    if plan.get("evidence_kind") not in ("mock", "simulation"):
        raise ValueError("evidence_kind must be mock or simulation")
    if plan.get("failure_policy") not in ("raise", "report"):
        raise ValueError("Specify failure_policy: raise or report")
    level = finite(plan.get("confidence_level"), "confidence_level")
    if level != .95:
        raise ValueError("This locked-question verifier requires 0.95 confidence intervals")
    scenarios = plan.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Plan needs nonempty scenarios")
    normalized = {}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a mapping")
        name = identity(scenario.get("id"), "scenario")
        if name in normalized:
            raise ValueError("Duplicate scenario ID")
        truth = finite(scenario.get("truth"), "truth")
        ids = scenario.get("replication_ids")
        if not isinstance(ids, list) or not ids:
            raise ValueError("Each scenario needs explicit planned replication_ids")
        ids = [identity(value, "replication") for value in ids]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate planned replication IDs")
        role = scenario.get("role")
        if role not in ("primary", "robustness", "extra_seed"):
            raise ValueError("Specify scenario role: primary, robustness or extra_seed")
        normalized[name] = {**scenario, "truth": truth, "replication_ids": ids}
    return normalized


def normalize_records(rows, plan):
    scenarios = validate_plan(plan)
    records = {}
    planned_ids = {name: set(item["replication_ids"]) for name, item in scenarios.items()}
    panels = {}
    for source in rows:
        if not isinstance(source, dict) or not REQUIRED_COLUMNS <= source.keys():
            raise ValueError("Raw record lacks required saved-result columns")
        scenario = identity(source["scenario"], "scenario")
        replication = identity(source["replication"], "replication")
        cell = source["cell"]
        if scenario not in scenarios or cell not in CELLS:
            raise ValueError("Unplanned scenario or invalid cell")
        if replication not in planned_ids[scenario]:
            raise ValueError("Unplanned replication ID")
        key = scenario, replication, cell
        if key in records:
            raise ValueError(f"Duplicate saved result: {key}")
        truth = finite(source["truth"], "truth")
        if truth != scenarios[scenario]["truth"]:
            raise ValueError("Saved truth differs from planned truth")
        if finite(source["confidence_level"], "confidence_level") != finite(plan["confidence_level"], "confidence_level"):
            raise ValueError("Saved confidence level differs from plan")
        panel = identity(source["panel_id"], "panel_id")
        panel_key = scenario, replication
        if panel_key in panels and panels[panel_key] != panel:
            raise ValueError("Cells with one replication ID use different panel IDs")
        panels[panel_key] = panel
        status = source["status"]
        if status not in ("ok", "failed"):
            raise ValueError("Saved status must be ok or failed")
        record = {**source, "scenario": scenario, "replication": replication,
                  "panel_id": panel, "truth": truth, "status": status}
        if status == "ok":
            for field in ("estimate", "lower", "upper"):
                record[field] = finite(source[field], field)
            if record["lower"] > record["upper"]:
                raise ValueError("Successful confidence interval has reversed bounds")
        else:
            if not isinstance(source.get("error"), str) or not source["error"].strip():
                raise ValueError("Failed results need a recorded error reason")
            record.update(estimate=None, lower=None, upper=None)
        if source.get("seconds") not in (None, ""):
            record["seconds"] = finite(source["seconds"], "seconds")
            if record["seconds"] < 0:
                raise ValueError("Runtime must be nonnegative")
        records[key] = record
    # Distinct replication IDs must never point to the same simulated panel.
    for scenario in scenarios:
        values = [panel for (name, _), panel in panels.items() if name == scenario]
        if len(values) != len(set(values)):
            raise ValueError("Independent replication IDs reuse a panel ID")
    return records, scenarios


def mean_mcse(values):
    """Stable sample mean and sample-SD/sqrt(n); n=1 has undefined MCSE."""
    values = list(values)
    if not values:
        return None, None
    for value in values:
        finite(value)
    scale = max(map(abs, values))
    if scale == 0:
        return 0., 0. if len(values) > 1 else None
    normalized = [value / scale for value in values]
    mean = math.fsum(value / len(values) for value in normalized)
    value = finite(scale * mean, "derived mean")
    if len(values) < 2:
        return value, None
    variance = math.fsum((item - mean) ** 2 for item in normalized) / (len(values) - 1)
    mcse = finite(scale * math.sqrt(variance / len(values)), "derived MCSE")
    return value, mcse


def rate_summary(successes, count):
    if not count:
        return {"rate": None, "mcse": None, "wilson95": None}
    rate = successes / count
    z = NormalDist().inv_cdf(.975)
    denominator = 1 + z * z / count
    center = (rate + z * z / (2 * count)) / denominator
    radius = z * math.sqrt(rate * (1 - rate) / count + z ** 2 / (4 * count ** 2)) / denominator
    return {"rate": rate, "mcse": math.sqrt(rate * (1 - rate) / count),
            "wilson95": [max(0., center - radius), min(1., center + radius)]}


def summarize_cell(records, scenario, cell):
    attempted = len(records)
    valid = [row for row in records if row["status"] == "ok"]
    planned = len(scenario["replication_ids"])
    truth = scenario["truth"]
    covered = sum(row["lower"] <= truth <= row["upper"] for row in valid)
    rejected = sum(row["upper"] < 0 or row["lower"] > 0 for row in valid)
    coverage = rate_summary(covered, len(valid))
    rejection = rate_summary(rejected, len(valid))
    widths = [finite(row["upper"] - row["lower"], "derived interval width") for row in valid]
    errors = [finite(row["estimate"] - truth, "derived estimation error") for row in valid]
    width, width_mcse = mean_mcse(widths)
    bias, bias_mcse = mean_mcse(errors)
    rmse = rmse_mcse = None
    if errors:
        scale = max(map(abs, errors))
        scaled_squares = [(value / scale) ** 2 for value in errors] if scale else [0.] * len(errors)
        mse, mse_mcse = mean_mcse(scaled_squares)
        rmse = finite(scale * math.sqrt(mse), "RMSE")
        if mse and mse_mcse is not None:
            rmse_mcse = finite(scale * (mse_mcse / (2 * math.sqrt(mse))), "RMSE MCSE")
    failed = attempted - len(valid)
    missing = planned - attempted
    return {
        "scenario": scenario["id"], "cell": cell, "truth": truth,
        "role": scenario["role"], "planned": planned, "attempted": attempted,
        "valid": len(valid), "failed": failed, "missing": missing,
        "coverage95": coverage["rate"], "coverage_mcse": coverage["mcse"],
        "coverage_wilson95": coverage["wilson95"],
        "empirical_size": rejection["rate"] if truth == 0 else None,
        "size_mcse": rejection["mcse"] if truth == 0 else None,
        "power": rejection["rate"] if truth != 0 else None,
        "power_mcse": rejection["mcse"] if truth != 0 else None,
        "rejection_wilson95": rejection["wilson95"],
        "mean_ci_width": width, "width_mcse": width_mcse,
        "bias": bias, "bias_mcse": bias_mcse, "rmse": rmse,
        "rmse_mcse_delta": rmse_mcse,
        "coverage_lower_all_planned": covered / planned,
        "coverage_upper_all_planned": (covered + failed + missing) / planned,
        "conditional_on_success": bool(failed or missing),
    }


def paired_comparisons(records, scenarios):
    comparisons = []
    for name, scenario in scenarios.items():
        for a, b in combinations(CELLS, 2):
            for outcome in ("coverage", "empirical_size" if scenario["truth"] == 0 else "power"):
                differences = []
                for replication in scenario["replication_ids"]:
                    left, right = records.get((name, replication, a)), records.get((name, replication, b))
                    if not left or not right or left["status"] != "ok" or right["status"] != "ok":
                        continue
                    if outcome == "coverage":
                        indicator = lambda row: row["lower"] <= scenario["truth"] <= row["upper"]
                    else:
                        indicator = lambda row: row["upper"] < 0 or row["lower"] > 0
                    differences.append(int(indicator(left)) - int(indicator(right)))
                difference, mcse = mean_mcse(differences)
                comparisons.append({
                    "scenario": name, "a": a, "b": b, "outcome": outcome,
                    "direction": "a_minus_b", "difference": difference, "mcse": mcse,
                    "planned_pairs": len(scenario["replication_ids"]),
                    "valid_pairs": len(differences),
                    "excluded_pairs": len(scenario["replication_ids"]) - len(differences),
                    "conditional_on_joint_success": len(differences) != len(scenario["replication_ids"]),
                    "central_comparison": (a, b) == (CELLS[1], CELLS[3]),
                })
    return comparisons


def audit_results(rows, plan):
    records, scenarios = normalize_records(rows, plan)
    grouped = defaultdict(list)
    for (name, _, cell), record in records.items():
        grouped[name, cell].append(record)
    summaries = [summarize_cell(grouped[name, cell], {**scenario, "id": name}, cell)
                 for name, scenario in scenarios.items() for cell in CELLS]
    issues = []
    for row in summaries:
        for field in ("missing", "failed"):
            if row[field]:
                issues.append({"code": field + "_replications", "scenario": row["scenario"],
                               "cell": row["cell"], "count": row[field]})
    return {
        "schema_version": 1, "evidence_kind": plan["evidence_kind"],
        "independent_arithmetic": "Python standard library; no production metric or runner imports",
        "all_planned_records_present": not any(row["missing"] for row in summaries),
        "all_records_successful": not any(row["failed"] or row["missing"] for row in summaries),
        "failure_policy": plan["failure_policy"],
        "summaries": summaries, "comparisons": paired_comparisons(records, scenarios),
        "issues": issues,
        "interpretation": "Mock arithmetic only" if plan["evidence_kind"] == "mock" else
            "Saved-interval arithmetic; DGP validity, manipulation checks and design approval require separate evidence",
        "gate_approval": "Not granted by this verifier",
    }


def compare_claims(report, claims, *, atol=1e-12, rtol=1e-10):
    """Compare full-precision headline metrics and denominators, not rounded prose."""
    atol, rtol = finite(atol, "atol"), finite(rtol, "rtol")
    if atol < 0 or rtol < 0:
        raise ValueError("Comparison tolerances must be nonnegative")
    if not isinstance(claims, (list, tuple)) or not all(isinstance(row, dict) for row in claims):
        raise ValueError("Claimed summaries must be a list of mappings")
    expected = {(row["scenario"], row["cell"]): row for row in report["summaries"]}
    observed = {}
    for row in claims:
        key = identity(row.get("scenario"), "claimed scenario"), identity(row.get("cell"), "claimed cell")
        if key in observed:
            raise ValueError("Duplicate claimed summary")
        observed[key] = row
    discrepancies = []
    for key in sorted(expected.keys() | observed.keys()):
        if key not in expected or key not in observed:
            discrepancies.append({"scenario": key[0], "cell": key[1], "field": "row",
                                  "reason": "missing or unexpected claimed summary"})
            continue
        fields = COUNT_FIELDS | {"coverage95", "coverage_mcse", "mean_ci_width", "width_mcse"}
        fields |= {"empirical_size", "size_mcse"} if expected[key]["truth"] == 0 else {"power", "power_mcse"}
        fields |= {field for field in ("bias", "bias_mcse", "rmse", "rmse_mcse_delta", "truth",
                                           "empirical_size", "size_mcse", "power", "power_mcse") if field in observed[key]}
        for field in sorted(fields):
            actual = expected[key][field]
            if field not in observed[key]:
                discrepancies.append({"scenario": key[0], "cell": key[1], "field": field,
                                      "reason": "claimed field absent"})
                continue
            claimed = observed[key][field]
            if claimed in (None, "", "N/A", "null"):
                matched = actual is None
                claimed = None
            else:
                try:
                    claimed = finite(claimed, "claimed " + field)
                    matched = actual is not None and (claimed == actual if field in COUNT_FIELDS or field == "truth" else
                        math.isclose(claimed, actual, rel_tol=rtol, abs_tol=atol))
                except ValueError:
                    matched = False
            if not matched:
                discrepancies.append({"scenario": key[0], "cell": key[1], "field": field,
                                      "recomputed": actual, "claimed": str(claimed)})
    return {"status": "matched" if not discrepancies else "discrepancies",
            "atol": atol, "rtol": rtol, "discrepancies": discrepancies}


def audit_stability(rows, *, absolute_estimate_limit=None):
    """Quick saved-output screen. Large finite values are logged, never clipped."""
    limit = None if absolute_estimate_limit is None else finite(absolute_estimate_limit, "limit")
    if limit is not None and limit <= 0:
        raise ValueError("Limit must be positive")
    counts = Counter()
    examples = []
    runtimes = []
    flagged = 0
    for row in rows:
        counts["records"] += 1
        label = {key: row.get(key) for key in ("scenario", "replication", "cell")}
        problems = []
        if row.get("status") == "failed":
            counts["failed"] += 1
            problems.append("producer_recorded_failure")
        elif row.get("status") != "ok":
            problems.append("invalid_status")
        else:
            values = {}
            for field in ("estimate", "lower", "upper"):
                try:
                    values[field] = finite(row.get(field), field)
                except ValueError:
                    problems.append("invalid_" + field)
            if "lower" in values and "upper" in values:
                if values["lower"] > values["upper"]:
                    problems.append("reversed_interval")
                elif not math.isfinite(values["upper"] - values["lower"]):
                    problems.append("unrepresentable_interval_width")
            if limit is not None and "estimate" in values and abs(values["estimate"]) > limit:
                problems.append("extreme_estimate_review_flag")
        if row.get("seconds") not in (None, ""):
            try:
                seconds = finite(row["seconds"], "seconds")
                if seconds < 0:
                    raise ValueError("negative runtime")
                runtimes.append(seconds)
            except ValueError:
                problems.append("invalid_runtime")
        for problem in problems:
            counts[problem] += 1
        flagged += bool(problems)
        if problems and len(examples) < 100:
            examples.append({**label, "problems": problems,
                             "estimate": str(row.get("estimate")), "error": row.get("error")})
    return {"counts": dict(counts), "examples": examples,
            "example_limit": 100, "flagged_records": flagged,
            "examples_truncated": flagged > len(examples),
            "absolute_estimate_limit": limit, "runtime_count": len(runtimes),
            "runtime_mean_seconds": mean_mcse(runtimes)[0],
            "runtime_max_seconds": max(runtimes) if runtimes else None,
            "interpretation": "Saved-output screen only; full DGP/nuisance path stability needs producer traces. No exclusions applied."}
