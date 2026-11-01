
import json

import numpy as np
import pytest

from src.infra.reproducibility import (
    config_hash,
    load_config,
    make_rngs,
    make_run_id,
    result_paths,
    save_json_atomic,
    save_manifest,
)


def test_load_existing_experiment_template():
    config = load_config(
        "configs/experiments/_template.yaml"
    )

    assert "experiment" in config
    assert "provenance" in config
    assert len(config["ablation_cells"]) == 4


def test_config_hash_ignores_dictionary_key_order():
    first = {"seed": 42, "count": 100}
    second = {"count": 100, "seed": 42}

    assert config_hash(first) == config_hash(second)


def test_same_seed_produces_same_values():
    a = make_rngs(42, 0)
    b = make_rngs(42, 0)

    np.testing.assert_array_equal(
        a["volatility"].normal(size=100),
        b["volatility"].normal(size=100),
    )


def test_rng_streams_are_isolated():
    a = make_rngs(42, 0)
    b = make_rngs(42, 0)

    # Consuming regimes must not advance volatility.
    a["regimes"].normal(size=5000)

    np.testing.assert_array_equal(
        a["volatility"].normal(size=100),
        b["volatility"].normal(size=100),
    )


def test_replication_streams_differ():
    a = make_rngs(42, 0)
    b = make_rngs(42, 1)

    assert not np.array_equal(
        a["factors"].normal(size=100),
        b["factors"].normal(size=100),
    )


def test_invalid_seed_is_rejected():
    with pytest.raises(ValueError):
        make_rngs(-1, 0)

    with pytest.raises(ValueError):
        make_rngs(True, 0)


def test_run_id_is_deterministic():
    config = {
        "experiment": {"name": "mock-test"},
        "provenance": {"seed": 42},
    }

    first = make_run_id("test.yaml", config)
    second = make_run_id("test.yaml", config)

    assert first == second
    assert "mock-test" in first


def test_result_paths(tmp_path):
    config = {
        "outputs": {
            "raw_dir": "results/raw",
            "summary_dir": "results/tables",
        }
    }

    paths = result_paths(config, "test-run", tmp_path)

    assert paths["raw"].is_dir()
    assert paths["tables"].is_dir()
    assert paths["figures"].is_dir()


def test_atomic_json_save(tmp_path):
    path = tmp_path / "test.json"

    data = {
        "replication": 1,
        "estimate": 0.25,
    }

    save_json_atomic(path, data)

    assert json.loads(path.read_text()) == data

    # Replacement must not corrupt or append.
    save_json_atomic(path, {"replication": 2})

    assert json.loads(path.read_text()) == {
        "replication": 2
    }


def test_manifest_contains_provenance(tmp_path):
    config = {
        "experiment": {"name": "mock-test"},
        "provenance": {"seed": 42},
    }

    path = tmp_path / "manifest.json"

    manifest = save_manifest(
        path,
        "mock.yaml",
        config,
    )

    assert manifest["root_seed"] == 42
    assert manifest["config_hash"] == config_hash(config)
    assert "git" in manifest
    assert path.exists()
