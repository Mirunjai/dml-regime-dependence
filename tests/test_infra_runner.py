
import json

from pathlib import Path

import pytest
import yaml

from src.infra.experiment_runner import (
    CELL_SPEC,
    run_experiment,
)


def prepare_project(root, count=8):
    """Create an isolated test project with existing YAML contracts."""
    dgp_path = root / "configs/dgp/test.yaml"
    exp_path = root / "configs/experiments/mock.yaml"

    dgp_path.parent.mkdir(parents=True, exist_ok=True)
    exp_path.parent.mkdir(parents=True, exist_ok=True)

    dgp = {
        "treatment": {"effect_true": 0.0},
    }

    config = {
        "experiment": {
            "name": "test-experiment",
            "owner": "Sudarshan",
        },
        "engine": "mock",
        "provenance": {
            "seed": 42,
            "dgp_config": "configs/dgp/test.yaml",
        },
        "replications": {"count": count},
        "ablation_cells": [
            {
                "id": cell,
                "cross_fitting": settings[0],
                "variance_estimation": settings[1],
            }
            for cell, settings in CELL_SPEC.items()
        ],
        "outputs": {
            "raw_dir": "results/raw",
            "summary_dir": "results/tables",
        },
    }

    dgp_path.write_text(yaml.safe_dump(dgp))
    exp_path.write_text(yaml.safe_dump(config))

    return "configs/experiments/mock.yaml"


def read_results(run_dir):
    files = sorted(Path(run_dir).glob("rep_*.json"))

    return [
        json.loads(path.read_text())
        for path in files
    ]


def test_serial_execution(tmp_path):
    config_path = prepare_project(tmp_path)

    run_dir = run_experiment(
        config_path,
        workers=1,
        repo_root=tmp_path,
    )

    results = read_results(run_dir)

    assert len(results) == 8

    for replication in results:
        assert len(replication["cells"]) == 4
        assert {
            item["cell"]
            for item in replication["cells"]
        } == set(CELL_SPEC)

        assert all(
            item["status"] == "ok"
            for item in replication["cells"]
        )


def test_serial_parallel_equivalence(tmp_path):
    root_a = tmp_path / "serial"
    root_b = tmp_path / "parallel"

    config_a = prepare_project(root_a)
    config_b = prepare_project(root_b)

    serial_dir = run_experiment(
        config_a,
        workers=1,
        repo_root=root_a,
    )

    parallel_dir = run_experiment(
        config_b,
        workers=2,
        repo_root=root_b,
    )

    assert read_results(serial_dir) == read_results(
        parallel_dir
    )


def test_resume_preserves_results(tmp_path):
    config_path = prepare_project(tmp_path)

    run_dir = run_experiment(
        config_path,
        repo_root=tmp_path,
    )

    before = read_results(run_dir)

    run_experiment(
        config_path,
        workers=2,
        repo_root=tmp_path,
    )

    after = read_results(run_dir)

    assert before == after
    assert len(after) == 8


def test_missing_replication_is_recreated(tmp_path):
    config_path = prepare_project(tmp_path)

    run_dir = run_experiment(
        config_path,
        repo_root=tmp_path,
    )

    original = read_results(run_dir)

    missing = run_dir / "rep_000003.json"
    missing.unlink()

    assert not missing.exists()

    run_experiment(
        config_path,
        workers=2,
        repo_root=tmp_path,
    )

    assert missing.exists()
    assert read_results(run_dir) == original


def test_corrupt_replication_is_rejected(tmp_path):
    config_path = prepare_project(tmp_path)

    run_dir = run_experiment(
        config_path,
        repo_root=tmp_path,
    )

    corrupt = run_dir / "rep_000002.json"
    corrupt.write_text("not valid JSON")

    with pytest.raises(ValueError):
        run_experiment(
            config_path,
            repo_root=tmp_path,
        )


def test_dgp_change_creates_new_run(tmp_path):
    config_path = prepare_project(tmp_path)

    first = run_experiment(
        config_path,
        repo_root=tmp_path,
    )

    dgp_path = tmp_path / "configs/dgp/test.yaml"

    dgp_path.write_text(
        yaml.safe_dump({
            "treatment": {"effect_true": 0.5}
        })
    )

    second = run_experiment(
        config_path,
        repo_root=tmp_path,
    )

    assert first != second
    assert first.exists()
    assert second.exists()


def test_rejects_incomplete_cell_design(tmp_path):
    config_path = prepare_project(tmp_path)

    full_path = tmp_path / config_path

    config = yaml.safe_load(full_path.read_text())
    config["ablation_cells"].pop()

    full_path.write_text(yaml.safe_dump(config))

    with pytest.raises(ValueError):
        run_experiment(
            config_path,
            repo_root=tmp_path,
        )


def test_different_replications_have_distinct_seeds(tmp_path):
    config_path = prepare_project(tmp_path)

    run_dir = run_experiment(
        config_path,
        repo_root=tmp_path,
    )

    results = read_results(run_dir)

    addresses = [
        tuple(rep["seed_addresses"]["volatility"])
        for rep in results
    ]

    assert len(addresses) == len(set(addresses))
