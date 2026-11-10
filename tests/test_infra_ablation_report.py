
"""Integration tests for Sudarshan's Week 2 reporting."""

import csv
import json

from pathlib import Path

import pytest
import yaml

from src.infra.ablation_report import generate_report
from src.infra.experiment_runner import (
    CELL_SPEC,
    run_experiment,
)
from src.infra.reproducibility import save_json_atomic


def build_experiment(root, effect=0.0, count=8):
    """Create a minimal test experiment using existing contracts."""
    dgp_path = root / "configs/dgp/test.yaml"
    experiment_path = (
        root / "configs/experiments/test.yaml"
    )

    dgp_path.parent.mkdir(parents=True, exist_ok=True)
    experiment_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    dgp_path.write_text(
        yaml.safe_dump({
            "treatment": {"effect_true": effect},
        }),
        encoding="utf-8",
    )

    config = {
        "experiment": {
            "name": "ablation-test",
            "owner": "Sudarshan",
        },
        "engine": "mock",
        "provenance": {
            "seed": 42,
            "dgp_config": "configs/dgp/test.yaml",
        },
        "replications": {
            "count": count,
        },
        "ablation_cells": [
            {
                "id": cell,
                "cross_fitting": specification[0],
                "variance_estimation": specification[1],
            }
            for cell, specification in CELL_SPEC.items()
        ],
        "outputs": {
            "raw_dir": "results/raw",
            "summary_dir": "results/tables",
            "figures_dir": "results/figures",
        },
    }

    experiment_path.write_text(
        yaml.safe_dump(config),
        encoding="utf-8",
    )

    run_dir = run_experiment(
        "configs/experiments/test.yaml",
        repo_root=root,
        workers=1,
    )

    return run_dir


def update_replication(run_dir, replication_id, change):
    """Edit a test-only raw record to exercise a specific case."""
    path = (
        Path(run_dir) /
        f"rep_{replication_id:06d}.json"
    )

    data = json.loads(path.read_text())

    change(data)

    save_json_atomic(path, data)


@pytest.fixture
def completed_run(tmp_path):
    run_dir = build_experiment(tmp_path)

    return tmp_path, run_dir


def test_all_four_cells_are_reported(completed_run):
    root, run_dir = completed_run

    report = generate_report(
        run_dir,
        repo_root=root,
    )

    assert len(report["cells"]) == 4

    assert {
        row["cell"] for row in report["cells"]
    } == set(CELL_SPEC)

    for row in report["cells"]:
        assert row["attempted"] == 8
        assert row["valid"] == 8
        assert row["failed"] == 0


def test_csv_and_markdown_are_generated(completed_run):
    root, run_dir = completed_run

    report = generate_report(
        run_dir,
        repo_root=root,
    )

    csv_path = Path(report["outputs"]["csv"])
    markdown_path = Path(
        report["outputs"]["markdown"]
    )

    assert csv_path.exists()
    assert markdown_path.exists()

    with csv_path.open(newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 4
    assert "coverage95" in rows[0]

    markdown = markdown_path.read_text()

    assert "random_xfit__robust_var" in markdown
    assert "grouped_xfit__robust_var" in markdown


def test_three_heatmaps_are_generated(completed_run):
    root, run_dir = completed_run

    report = generate_report(
        run_dir,
        repo_root=root,
    )

    plots = report["outputs"]["plots"]

    assert set(plots) == {
        "coverage95",
        "empirical_size",
        "mean_ci_width",
    }

    for path in plots.values():
        assert path is not None
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0


def test_mock_ci_widths_are_correct(completed_run):
    root, run_dir = completed_run

    report = generate_report(
        run_dir,
        repo_root=root,
    )

    rows = {
        row["cell"]: row
        for row in report["cells"]
    }

    assert rows[
        "random_xfit__naive_var"
    ]["mean_ci_width"] == pytest.approx(0.20)

    assert rows[
        "random_xfit__robust_var"
    ]["mean_ci_width"] == pytest.approx(0.30)

    assert rows[
        "grouped_xfit__naive_var"
    ]["mean_ci_width"] == pytest.approx(0.22)

    assert rows[
        "grouped_xfit__robust_var"
    ]["mean_ci_width"] == pytest.approx(0.32)


def test_known_coverage_and_size(tmp_path):
    """
    Construct a known outcome:
    six intervals cover zero and two reject zero.

    Expected coverage = 6/8 = 0.75
    Expected empirical size = 2/8 = 0.25
    """
    run_dir = build_experiment(tmp_path)

    for replication_id in range(8):

        def modify(data, index=replication_id):
            for cell in data["cells"]:
                if index < 6:
                    cell["lower"] = -1.0
                    cell["upper"] = 1.0
                else:
                    cell["lower"] = 0.1
                    cell["upper"] = 1.0

        update_replication(
            run_dir,
            replication_id,
            modify,
        )

    report = generate_report(
        run_dir,
        repo_root=tmp_path,
    )

    for row in report["cells"]:
        assert row["coverage95"] == pytest.approx(0.75)
        assert row["empirical_size"] == pytest.approx(0.25)


def test_paired_robust_difference(tmp_path):
    """
    Random+robust always covers the truth.
    Grouped+robust always misses the truth.

    Paired coverage difference should equal +1.
    """
    run_dir = build_experiment(tmp_path)

    for replication_id in range(8):

        def modify(data):
            for cell in data["cells"]:
                if cell["cell"] == "random_xfit__robust_var":
                    cell["lower"] = -1.0
                    cell["upper"] = 1.0

                elif cell["cell"] == "grouped_xfit__robust_var":
                    cell["lower"] = 0.5
                    cell["upper"] = 1.5

        update_replication(
            run_dir,
            replication_id,
            modify,
        )

    report = generate_report(
        run_dir,
        repo_root=tmp_path,
    )

    paired = report[
        "paired_robust_comparisons"
    ]["coverage"]

    assert paired["estimable"] is True
    assert paired["valid_pairs"] == 8
    assert paired["difference"] == pytest.approx(1.0)
    assert paired["mcse"] == pytest.approx(0.0)


def test_nonzero_effect_reports_power(tmp_path):
    run_dir = build_experiment(
        tmp_path,
        effect=0.5,
    )

    report = generate_report(
        run_dir,
        repo_root=tmp_path,
    )

    for row in report["cells"]:
        assert row["empirical_size"] is None
        assert row["power"] is not None

    assert "power" in report["outputs"]["plots"]
    assert "empirical_size" not in report["outputs"]["plots"]


def test_missing_replication_raises(completed_run):
    root, run_dir = completed_run

    missing = Path(run_dir) / "rep_000003.json"
    missing.unlink()

    with pytest.raises(FileNotFoundError):
        generate_report(
            run_dir,
            repo_root=root,
        )


def test_failed_cell_requires_explicit_policy(completed_run):
    root, run_dir = completed_run

    def modify(data):
        cell = data["cells"][0]

        cell["status"] = "failed"
        cell["estimate"] = None
        cell["lower"] = None
        cell["upper"] = None
        cell["error"] = "Deliberate test failure"

    update_replication(run_dir, 0, modify)

    with pytest.raises(ValueError):
        generate_report(
            run_dir,
            repo_root=root,
        )

    report = generate_report(
        run_dir,
        repo_root=root,
        failure_policy="report",
    )

    affected = report["cells"][0]

    assert affected["attempted"] == 8
    assert affected["valid"] == 7
    assert affected["failed"] == 1
    assert affected["conditional_on_success"] is True


def test_all_failed_cells_are_undefined(tmp_path):
    run_dir = build_experiment(
        tmp_path,
        count=4,
    )

    for replication_id in range(4):

        def modify(data):
            for cell in data["cells"]:
                cell["status"] = "failed"
                cell["estimate"] = None
                cell["lower"] = None
                cell["upper"] = None
                cell["error"] = "Deliberate failure"

        update_replication(
            run_dir,
            replication_id,
            modify,
        )

    report = generate_report(
        run_dir,
        repo_root=tmp_path,
        failure_policy="report",
    )

    for row in report["cells"]:
        assert row["failed"] == 4
        assert row["coverage95"] is None
        assert row["empirical_size"] is None
        assert row["mean_ci_width"] is None

    assert all(
        path is None
        for path in report["outputs"]["plots"].values()
    )

    assert report[
        "paired_robust_comparisons"
    ]["coverage"]["estimable"] is False


def test_tampered_truth_is_rejected(completed_run):
    root, run_dir = completed_run

    def modify(data):
        data["truth"] = 999.0

    update_replication(run_dir, 0, modify)

    with pytest.raises(ValueError, match="truth"):
        generate_report(
            run_dir,
            repo_root=root,
        )


def test_report_rejects_tampered_seed_addresses(completed_run):
    root, run_dir = completed_run
    update_replication(
        run_dir, 0,
        lambda record: record["seed_addresses"].update(factors=[42, 99, 0]),
    )
    with pytest.raises(ValueError, match="seed_addresses"):
        generate_report(run_dir, repo_root=root)


def test_report_rejects_run_id_path_traversal(completed_run):
    root, run_dir = completed_run
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["run_id"] = "../../escaped"
    save_json_atomic(manifest_path, manifest)
    with pytest.raises(ValueError, match="Unsafe run ID"):
        generate_report(run_dir, repo_root=root)
    assert not (root / "escaped_ablation.csv").exists()


def test_all_failed_report_removes_previous_heatmaps(completed_run):
    root, run_dir = completed_run
    before = generate_report(run_dir, repo_root=root)
    old_plots = [Path(path) for path in before["outputs"]["plots"].values()]
    assert all(path.exists() for path in old_plots)

    def fail_all(record):
        for cell in record["cells"]:
            cell.update(status="failed", estimate=None, lower=None, upper=None,
                        error="test failure")

    for replication_id in range(8):
        update_replication(run_dir, replication_id, fail_all)
    after = generate_report(run_dir, repo_root=root, failure_policy="report")
    assert all(path is None for path in after["outputs"]["plots"].values())
    assert not any(path.exists() for path in old_plots)
    assert all(row["failed"] == 8 and row["valid"] == 0 for row in after["cells"])
