
"""Four-cell Monte Carlo reporting on saved replication outputs.

Consumes Phase 3 raw JSON records and existing statistical metrics.
Does not implement a DML estimator or a new statistical metric engine.
"""

import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from src.evaluation.metrics import (
    paired_binary_difference,
    summarize_intervals,
)
from src.infra.experiment_runner import (
    CELL_SPEC, validate_config, validate_saved_result,
)
from src.infra.reproducibility import (
    config_hash,
    save_json_atomic,
    validate_run_id,
)
from src.infra.reporting import (
    markdown_table,
    save_csv_table,
)


# These are the same four cells defined in the Phase 3 runner.
MATRIX = (
    (
        "random_xfit__naive_var",
        "random_xfit__robust_var",
    ),
    (
        "grouped_xfit__naive_var",
        "grouped_xfit__robust_var",
    ),
)

RANDOM_ROBUST = "random_xfit__robust_var"
GROUPED_ROBUST = "grouped_xfit__robust_var"


# ---------------------------------------------------------
# 1. Read and validate completed raw experiments
# ---------------------------------------------------------

def load_results(run_dir):
    """
    Load every planned independent replication.

    Never silently exclude missing replications or duplicate
    cell records. These are required for valid MC accounting.
    """
    run_dir = Path(run_dir)

    manifest_path = run_dir / "manifest.json"

    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    config = manifest["config"]
    run_id = validate_run_id(manifest["run_id"])
    validate_config(config)
    if manifest.get("source_changed_during_run"):
        raise ValueError("Run was invalidated by a source change")
    expected_hash = manifest["config_hash"]

    if config_hash(config) != expected_hash:
        raise ValueError(
            "Manifest configuration fingerprint mismatch"
        )

    count = config["replications"]["count"]
    truth = float(
        config["_resolved_dgp"]["treatment"]["effect_true"]
    )

    if not math.isfinite(truth):
        raise ValueError("Nonfinite known treatment effect")

    by_cell = {
        cell: []
        for cell in CELL_SPEC
    }

    for replication_id in range(count):
        path = (
            run_dir / f"rep_{replication_id:06d}.json"
        )

        if not path.is_file():
            raise FileNotFoundError(
                f"Missing replication {replication_id}: {path}. "
                "Resume or diagnose the runner first."
            )

        record = validate_saved_result(path, replication_id, run_id, config)

        for item in record["cells"]:
            by_cell[item["cell"]].append({
                **item,
                "replication_id": replication_id,
            })

    return manifest, by_cell, truth


# ---------------------------------------------------------
# 2. Existing metrics -> flat summary rows
# ---------------------------------------------------------

def _rate(summary):
    return None if summary is None else summary.rate


def _mcse(summary):
    return None if summary is None else summary.mcse


def summarize_cell(cell, records, truth, failure_policy):
    """
    Call Deeptanshu's existing metrics implementation.

    The arrays contain exactly one entry per planned
    independent replication, including failed attempts.
    """
    success = np.array([
        item["status"] == "ok"
        for item in records
    ], dtype=bool)

    lower = np.array([
        item["lower"] if ok else np.nan
        for item, ok in zip(records, success)
    ], dtype=float)

    upper = np.array([
        item["upper"] if ok else np.nan
        for item, ok in zip(records, success)
    ], dtype=float)

    summary = summarize_intervals(
        lower,
        upper,
        truth,
        success=success,
        failure_policy=failure_policy,
        expected_replications=len(records),
    )

    cross_fitting, variance = CELL_SPEC[cell]

    return {
        "cell": cell,
        "cross_fitting": cross_fitting,
        "variance": variance,
        "attempted": summary.attempted,
        "valid": summary.valid,
        "failed": summary.failed,
        "coverage95": _rate(summary.coverage),
        "coverage_mcse": _mcse(summary.coverage),
        "empirical_size": _rate(summary.size),
        "size_mcse": _mcse(summary.size),
        "power": _rate(summary.power),
        "power_mcse": _mcse(summary.power),
        "mean_ci_width": summary.mean_width,
        "width_mcse": summary.width_mcse,
        "coverage_lower_all_attempted":
            summary.coverage_bounds_all_attempted[0],
        "coverage_upper_all_attempted":
            summary.coverage_bounds_all_attempted[1],
        "conditional_on_success":
            summary.conditional_on_success,
    }


# ---------------------------------------------------------
# 3. Primary paired comparison
# ---------------------------------------------------------

def _binary_outcomes(records, truth, kind):
    """
    Align indicators by independent replication ID.

    Failed cells are explicitly represented by None.
    """
    outcomes = {}

    for item in records:
        replication_id = item["replication_id"]

        if item["status"] != "ok":
            outcomes[replication_id] = None
            continue

        lower = float(item["lower"])
        upper = float(item["upper"])

        if kind == "coverage":
            value = lower <= truth <= upper

        elif kind == "rejection":
            value = upper < 0 or lower > 0

        else:
            raise ValueError("Unknown paired outcome")

        outcomes[replication_id] = bool(value)

    return outcomes


def paired_comparison(by_cell, truth, failure_policy):
    """
    Compare Random+Robust minus Grouped+Robust.

    This uses the existing paired-difference implementation.
    """
    comparisons = {}

    metric_types = {
        "coverage": "coverage",
        "size" if truth == 0 else "power": "rejection",
    }

    for label, kind in metric_types.items():
        random_outcomes = _binary_outcomes(
            by_cell[RANDOM_ROBUST],
            truth,
            kind,
        )

        grouped_outcomes = _binary_outcomes(
            by_cell[GROUPED_ROBUST],
            truth,
            kind,
        )

        common_valid = sum(
            random_outcomes[replication] is not None
            and grouped_outcomes[replication] is not None
            for replication in random_outcomes
        )

        if common_valid < 2:
            comparisons[label] = {
                "estimable": False,
                "valid_pairs": common_valid,
                "reason": (
                    "At least two jointly successful paired "
                    "replications are required"
                ),
            }
            continue

        result = paired_binary_difference(
            random_outcomes,
            grouped_outcomes,
            failure_policy=failure_policy,
        )

        comparisons[label] = {
            "estimable": True,
            "direction": "random_robust_minus_grouped_robust",
            **asdict(result),
        }

    return comparisons


# ---------------------------------------------------------
# 4. 2x2 plots
# ---------------------------------------------------------

def save_heatmap(rows, metric, title, output_path, *, limits=(None, None)):
    """
    Generate the 2x2 fold-versus-variance comparison.

    Unlike the existing generic line plot, this visualizes
    the research design's factorial cell structure.
    """
    lookup = {
        row["cell"]: row[metric]
        for row in rows
    }

    values = np.array([
        [
            np.nan if lookup[cell] is None
            else float(lookup[cell])
            for cell in line
        ]
        for line in MATRIX
    ], dtype=float)

    output_path = Path(output_path)

    # Remove this run's stale plot if a later report has no usable estimates.
    if np.isnan(values).all():
        output_path.unlink(missing_ok=True)
        return None

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(8, 5))

    try:
        image = ax.imshow(
            np.ma.masked_invalid(values),
            aspect="auto",
            vmin=limits[0],
            vmax=limits[1],
        )

        ax.set_xticks([0, 1])
        ax.set_xticklabels([
            "Naive variance",
            "Robust variance",
        ])

        ax.set_yticks([0, 1])
        ax.set_yticklabels([
            "Random folds",
            "Grouped folds",
        ])

        for row in range(2):
            for col in range(2):
                value = values[row, col]

                label = (
                    f"{value:.4f}"
                    if math.isfinite(value)
                    else "N/A"
                )

                ax.text(
                    col,
                    row,
                    label,
                    color="black",
                    ha="center",
                    va="center",
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9},
                )

        ax.set_title(title)
        fig.colorbar(image, ax=ax)

        fig.tight_layout()
        fig.savefig(output_path, dpi=150)

    finally:
        plt.close(fig)

    return output_path


# ---------------------------------------------------------
# 5. Full report generation
# ---------------------------------------------------------

def _safe_output_dir(root, relative_path):
    """Keep output destinations inside the repository."""
    path = Path(relative_path)

    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Unsafe output directory")

    result = (root / path).resolve()

    if not result.is_relative_to(root):
        raise ValueError("Output directory escapes repository")

    result.mkdir(parents=True, exist_ok=True)

    return result


def generate_report(
    run_dir,
    *,
    repo_root=".",
    failure_policy="raise",
):
    """
    Produce CSV, Markdown, JSON and 2x2 PNG reports.

    Default strict mode fails on unsuccessful estimator cells.
    Report mode must be requested explicitly to show
    success-conditional statistics and failure counts.
    """
    if failure_policy not in ("raise", "report"):
        raise ValueError("Invalid failure policy")

    root = Path(repo_root).resolve()

    run_dir = Path(run_dir)

    if not run_dir.is_absolute():
        run_dir = root / run_dir

    run_dir = run_dir.resolve()

    if not run_dir.is_relative_to(root):
        raise ValueError("Run directory escapes repository")

    manifest, by_cell, truth = load_results(run_dir)

    config = manifest["config"]
    run_id = manifest["run_id"]

    # Reuse the existing repository output conventions.
    outputs = config.get("outputs", {})

    tables_dir = _safe_output_dir(
        root,
        outputs.get("summary_dir", "results/tables"),
    )

    figures_dir = _safe_output_dir(
        root,
        outputs.get("figures_dir", "results/figures"),
    )

    rows = [
        summarize_cell(
            cell,
            by_cell[cell],
            truth,
            failure_policy,
        )
        for cell in CELL_SPEC
    ]

    paired = paired_comparison(
        by_cell,
        truth,
        failure_policy,
    )

    columns = list(rows[0])

    # Reuse your Week 1 table utilities.
    csv_path = tables_dir / f"{run_id}_ablation.csv"

    save_csv_table(
        rows,
        columns,
        csv_path,
    )

    markdown_path = (
        tables_dir / f"{run_id}_ablation.md"
    )

    markdown_path.write_text(
        "# Four-cell mock infrastructure summary\n\n"
        + "**Engine:** "
        + str(config.get("engine", "unspecified"))
        + "\n\n"
        + markdown_table(rows, columns)
        + "\n\n"
        + (
            "Rates are conditional on successful replications "
            "if failures occurred. See failed counts and "
            "all-attempted coverage bounds.\n"
        ),
        encoding="utf-8",
    )

    # Choose size at the null, power at a nonzero effect.
    rejection_metric = (
        "empirical_size" if truth == 0 else "power"
    )

    plot_specs = [
        ("coverage95", "95% confidence interval coverage"),
        (
            rejection_metric,
            "Empirical size" if truth == 0 else "Power",
        ),
        ("mean_ci_width", "Mean confidence interval width"),
    ]

    plots = {}

    for metric, title in plot_specs:
        path = figures_dir / f"{run_id}_{metric}.png"

        output = save_heatmap(
            rows,
            metric,
            f"MOCK infrastructure check — {title}",
            path,
        )

        plots[metric] = (
            str(output)
            if output is not None
            else None
        )

    report = {
        "run_id": run_id,
        "experiment": config["experiment"]["name"],
        "engine": config.get("engine", "unspecified"),
        "known_truth": truth,
        "planned_replications":
            config["replications"]["count"],
        "failure_policy": failure_policy,
        "statistical_interpretation": (
            "Success-conditional when failures occur; "
            "mock engine results are infrastructure tests."
        ),
        "cells": rows,
        "paired_robust_comparisons": paired,
        "outputs": {
            "csv": str(csv_path),
            "markdown": str(markdown_path),
            "plots": plots,
        },
    }

    json_path = (
        tables_dir / f"{run_id}_ablation.json"
    )

    report["outputs"]["json"] = str(json_path)
    save_json_atomic(json_path, report)

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Four-cell Monte Carlo ablation reporting"
    )

    parser.add_argument(
        "--run-dir",
        required=True,
    )

    parser.add_argument(
        "--repo-root",
        default=".",
    )

    parser.add_argument(
        "--failure-policy",
        choices=("raise", "report"),
        default="raise",
    )

    args = parser.parse_args()

    report = generate_report(
        args.run_dir,
        repo_root=args.repo_root,
        failure_policy=args.failure_policy,
    )

    print("Experiment:", report["run_id"])
    print("Engine:", report["engine"])
    print("Known truth:", report["known_truth"])
    print()

    for row in report["cells"]:
        print(
            row["cell"],
            "coverage =", row["coverage95"],
            "size =", row["empirical_size"],
            "power =", row["power"],
            "width =", row["mean_ci_width"],
            "failed =", row["failed"],
        )

    print()
    print("CSV:", report["outputs"]["csv"])
    print("Markdown:", report["outputs"]["markdown"])
    print("JSON:", report["outputs"]["json"])


if __name__ == "__main__":
    main()
