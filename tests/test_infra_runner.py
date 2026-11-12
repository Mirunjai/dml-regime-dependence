
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


@pytest.mark.parametrize("field", ["truth", "seed_addresses"])
def test_resume_rejects_tampered_provenance(tmp_path, field):
    config_path = prepare_project(tmp_path, count=2)
    run_dir = run_experiment(config_path, repo_root=tmp_path)
    path = run_dir / "rep_000000.json"
    result = json.loads(path.read_text())
    if field == "truth":
        result[field] = 99.0
    else:
        result[field]["factors"] = [42, 100, 0]
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match=field):
        run_experiment(config_path, repo_root=tmp_path)


@pytest.mark.parametrize("field", ["config", "software", "rng_stream_ids"])
def test_resume_rejects_tampered_manifest(tmp_path, field):
    config_path = prepare_project(tmp_path, count=2)
    run_dir = run_experiment(config_path, repo_root=tmp_path)
    path = run_dir / "manifest.json"
    result = json.loads(path.read_text())
    result[field] = {}
    path.write_text(json.dumps(result))
    with pytest.raises(ValueError):
        run_experiment(config_path, repo_root=tmp_path)


def test_source_edit_during_run_invalidates_reporting(tmp_path, monkeypatch):
    from src.infra import experiment_runner as runner
    from src.infra.ablation_report import generate_report
    config_path = prepare_project(tmp_path, count=2)
    source = tmp_path / "src/mock.py"
    source.parent.mkdir()
    source.write_text("# original\n")
    original = runner._worker

    def edit_source(*args):
        source.write_text("# changed\n")
        return original(*args)

    monkeypatch.setattr(runner, "_worker", edit_source)
    with pytest.raises(ValueError, match="Source changed during run"):
        run_experiment(config_path, repo_root=tmp_path)
    run_dir = next((tmp_path / "results/raw").iterdir())
    with pytest.raises(ValueError, match="invalidated"):
        generate_report(run_dir, repo_root=tmp_path)


def test_two_controlling_processes_cannot_overwrite_run(tmp_path):
    import subprocess
    import sys
    from src.infra.reproducibility import run_lock

    script = (
        "import sys; from src.infra.reproducibility import run_lock; "
        "\nwith run_lock(sys.argv[1]): pass"
    )
    with run_lock(tmp_path):
        child = subprocess.run(
            [sys.executable, "-c", script, str(tmp_path)],
            capture_output=True, text=True, check=False,
        )
        assert child.returncode != 0
        assert "already locked" in child.stderr
    # A released lock leaves a reusable file, not a stale lock.
    with run_lock(tmp_path):
        pass


def test_parallel_spawn_matches_serial(tmp_path, monkeypatch):
    import multiprocessing
    from functools import partial
    from concurrent.futures import ProcessPoolExecutor
    from src.infra import experiment_runner as runner

    serial = tmp_path / "serial"
    spawned = tmp_path / "spawn"
    serial_config = prepare_project(serial, count=3)
    spawn_config = prepare_project(spawned, count=3)
    expected = read_results(run_experiment(serial_config, repo_root=serial))
    monkeypatch.setattr(
        runner, "ProcessPoolExecutor",
        partial(ProcessPoolExecutor, mp_context=multiprocessing.get_context("spawn")),
    )
    actual = read_results(run_experiment(spawn_config, repo_root=spawned, workers=2))
    assert actual == expected


def test_engine_exception_is_recorded_and_not_retried(tmp_path, monkeypatch):
    from src.infra import experiment_runner as runner
    from src.infra.ablation_report import generate_report
    config_path = prepare_project(tmp_path, count=2)
    calls = []

    def broken_engine(*args):
        calls.append(1)
        raise RuntimeError("intentional engine failure")

    monkeypatch.setattr(runner, "mock_four_cells", broken_engine)
    run_dir = run_experiment(config_path, repo_root=tmp_path)
    assert len(calls) == 2
    run_experiment(config_path, repo_root=tmp_path)
    assert len(calls) == 2
    assert all(cell["status"] == "failed"
               for record in read_results(run_dir) for cell in record["cells"])
    with pytest.raises(ValueError):
        generate_report(run_dir, repo_root=tmp_path)
    report = generate_report(run_dir, repo_root=tmp_path, failure_policy="report")
    assert all(row["attempted"] == 2 and row["failed"] == 2
               for row in report["cells"])
