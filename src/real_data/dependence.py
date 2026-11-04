"""Descriptive cross-firm dependence by externally supplied market-regime labels.

No DML, price downloads, label fitting, p-values or real-data coverage estimates.
Pairs use only overlapping dates within one label. Every undefined pair and all
missingness remain visible. See docs/week3_verification.md for interpretation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path
from statistics import median

from src.evaluation.verification import finite, identity, read_csv
from src.evaluation.week3_audit import provenance, save_source_snapshot, write_json

REQUIRED = {"date", "firm_id", "value", "regime"}


def average(values):
    return math.fsum(value / len(values) for value in values) if values else None


def correlation(x, y):
    """Pearson product-moment correlation on already aligned finite observations."""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Correlation needs matching sequences of at least two observations")
    x, y = [finite(value) for value in x], [finite(value) for value in y]
    sx, sy = max(map(abs, x)), max(map(abs, y))
    if sx == 0 or sy == 0:
        return None
    x, y = [value / sx for value in x], [value / sy for value in y]
    mx, my = math.fsum(value / len(x) for value in x), math.fsum(value / len(y) for value in y)
    dx, dy = [value - mx for value in x], [value - my for value in y]
    xx, yy = math.fsum(value * value for value in dx), math.fsum(value * value for value in dy)
    if not xx or not yy:
        return None
    result = math.fsum(a * b for a, b in zip(dx, dy)) / math.sqrt(xx) / math.sqrt(yy)
    # Bound only floating-point rounding of a mathematically bounded statistic.
    if not math.isfinite(result) or abs(result) > 1 + 1e-12:
        raise ValueError("Invalid derived correlation")
    return min(1., max(-1., result))


def analyze_dependence(rows, *, min_overlap, value_kind, label_source, evidence_kind="real"):
    if evidence_kind not in ("real", "mock"):
        raise ValueError("evidence_kind must be real or mock")
    rows = list(rows)
    if type(min_overlap) is not int or min_overlap < 3:
        raise ValueError("Explicit min_overlap must be an integer >=3; two-point correlations are uninformative")
    if value_kind not in ("return", "abnormal_return", "residual"):
        raise ValueError("Declare value_kind: return, abnormal_return or residual")
    label_source = identity(label_source, "external label definition/source")
    series = defaultdict(lambda: defaultdict(dict))
    seen = set()
    labels_by_date = {}
    dates_by_label = defaultdict(set)
    firms = set()
    counts = Counter()
    missing = []
    missing_count = 0
    for row in rows:
        if not isinstance(row, dict) or not REQUIRED <= row.keys():
            raise ValueError("Panel needs date, firm_id, value, regime")
        day = identity(row["date"], "date")
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError("Dates must use YYYY-MM-DD")
        firm = identity(row["firm_id"], "firm_id")
        label = row["regime"]
        if label not in ("calm", "turbulent"):
            raise ValueError("Use explicit external calm/turbulent labels")
        key = day, firm
        if key in seen:
            raise ValueError("Duplicate date/firm observation")
        seen.add(key)
        if day in labels_by_date and labels_by_date[day] != label:
            raise ValueError("One calendar date has conflicting market-regime labels")
        labels_by_date[day] = label
        dates_by_label[label].add(day)
        firms.add(firm)
        counts[label] += 1
        if row["value"] in (None, ""):
            missing_count += 1
            if len(missing) < 100:
                missing.append({"date": day, "firm_id": firm, "regime": label})
            continue
        series[label][firm][day] = finite(row["value"], "panel value")
    if not rows:
        raise ValueError("Panel is empty")
    pairs = []
    summaries = {}
    usable = defaultdict(dict)
    for label in ("calm", "turbulent"):
        for a, b in combinations(sorted(firms), 2):
            left, right = series[label][a], series[label][b]
            common = sorted(left.keys() & right.keys())
            value = None
            reason = "insufficient_overlap"
            if len(common) >= min_overlap:
                value = correlation([left[day] for day in common], [right[day] for day in common])
                reason = "constant_series" if value is None else None
            if value is not None:
                usable[label][a, b] = value
            pairs.append({"regime": label, "firm_a": a, "firm_b": b,
                          "overlapping_dates": len(common), "correlation": value,
                          "status": "evaluated" if value is not None else "undefined", "reason": reason})
        values = list(usable[label].values())
        valid_values = sum(len(data) for data in series[label].values())
        summaries[label] = {
            "dates": len(dates_by_label[label]), "firms_with_values": sum(bool(v) for v in series[label].values()),
            "observed_rows": counts[label], "usable_values": valid_values,
            "explicit_missing_values": counts[label] - valid_values,
            "absent_firm_dates": len(dates_by_label[label]) * len(firms) - counts[label],
            "possible_pairs": len(firms) * (len(firms) - 1) // 2,
            "usable_pairs": len(values),
            "undefined_pairs": len(firms) * (len(firms) - 1) // 2 - len(values),
            "mean_correlation": average(values),
            "median_correlation": median(values) if values else None,
            "mean_absolute_correlation": average([abs(value) for value in values]),
        }
    matched = sorted(usable["calm"].keys() & usable["turbulent"].keys())
    differences = [usable["turbulent"][key] - usable["calm"][key] for key in matched]
    return {
        "status": "evaluated" if all(summaries[label]["usable_pairs"] for label in ("calm", "turbulent")) else "insufficient_data",
        "evidence_kind": "mock_diagnostic" if evidence_kind == "mock" else "qualitative_real_data_diagnostic",
        "value_kind": value_kind,
        "label_source": label_source, "min_overlap": min_overlap, "firms_in_union": len(firms),
        "summaries": summaries, "matched_pair_comparison": {
            "usable_in_both_regimes": len(matched), "direction": "turbulent_minus_calm",
            "mean_correlation_difference": average(differences),
            "median_correlation_difference": median(differences) if differences else None,
            "inferential_standard_error": None,
        },
        "explicit_missing_examples": missing, "missing_examples_truncated": missing_count > len(missing),
        "pairs": pairs,
        "limitations": [
            "Descriptive equal-weight pair summaries; pairs share firms and dates and are not independent samples.",
            "No iid correlation p-values or iid pair-based standard errors are reported.",
            "Overlapping dates and sample sizes differ by pair/label; selection, market factors and volatility can affect comparisons.",
            "Labels and values must come from the team's documented data pipeline; this tool neither selects regimes nor residualizes returns.",
            "Unknown true causal effect: real data cannot establish coverage or empirical size.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", required=True, type=Path)
    parser.add_argument("--evidence-kind", required=True, choices=("real", "mock"))
    parser.add_argument("--min-overlap", required=True, type=int)
    parser.add_argument("--value-kind", required=True, choices=("return", "abnormal_return", "residual"))
    parser.add_argument("--label-source", required=True, help="Location/version of Preksha's external label definition")
    parser.add_argument("--output", required=True, type=Path, help="New diagnostic output directory")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output directory exists; choose a new diagnostic name")
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        parser.error(f"Cannot reserve a new output directory: {exc}")
    try:
        before = provenance([args.panel], extra_sources=[__file__])
        report = analyze_dependence(read_csv(args.panel, REQUIRED), min_overlap=args.min_overlap,
                                    value_kind=args.value_kind, label_source=args.label_source, evidence_kind=args.evidence_kind)
        after = provenance([args.panel], extra_sources=[__file__])
        if before["input_sha256"] != after["input_sha256"]:
            raise ValueError("Panel changed while being read; repeat on a frozen snapshot")
        if before["verifier_source_sha256"] != after["verifier_source_sha256"]:
            raise ValueError("Diagnostic source changed during audit")
        report["provenance"] = after
        report["provenance"]["diagnostic_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        pairs = report.pop("pairs")
        report["provenance"]["source_archive"] = save_source_snapshot(args.output, after, extra_sources=[__file__])
        with (args.output / "pair_correlations.csv").open("w", newline="", encoding="utf-8") as stream:
            columns = ("regime", "firm_a", "firm_b", "overlapping_dates", "correlation", "status", "reason")
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(pairs)
        write_json(args.output / "dependence.json", report)
        print(f"Saved qualitative diagnostics: {args.output / 'dependence.json'}")
        return 0 if all(report["summaries"][label]["usable_pairs"] for label in ("calm", "turbulent")) else 2
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"Real-data input error: {exc}")
        try:
            write_json(args.output / "input_error.json", {"status": "invalid_input", "error": str(exc)})
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
