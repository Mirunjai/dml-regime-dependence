
"""Reusable experiment configuration and reproducibility utilities."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import yaml


# Fixed IDs prevent RNG streams from depending on call order.
STREAM_IDS = {
    "factors": 0,
    "volatility": 1,
    "regimes": 2,
    "treatment": 3,
    "estimator": 4,
}


def load_config(path):
    """Load a YAML configuration without changing its contents."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping")

    return config


def config_hash(config):
    """Compute a deterministic fingerprint of a configuration."""
    canonical = json.dumps(
        config,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def git_state(repo_root="."):
    """Identify the current Git revision and dirty-worktree state."""
    root = Path(repo_root).resolve()

    try:
        sha = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        status = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        return {
            "commit": sha,
            "dirty": bool(status),
        }

    except (OSError, subprocess.CalledProcessError):
        return {
            "commit": "unavailable",
            "dirty": True,
        }


def make_run_id(config_path, config, repo_root="."):
    """
    Identify a run using the configuration path,
    contents, seed and Git commit.

    This follows the repository's existing naming convention.
    """
    seed = config["provenance"]["seed"]

    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("Seed must be a nonnegative integer")

    experiment = config["experiment"]["name"]

    slug = re.sub(
        r"[^A-Za-z0-9_-]+",
        "-",
        str(experiment),
    ).strip("-") or "experiment"

    identity = {
        "config_path": Path(config_path).as_posix(),
        "configuration": config,
    }

    fingerprint = config_hash(identity)[:12]
    revision = git_state(repo_root)["commit"][:8]

    return f"{slug}-s{seed}-{fingerprint}-{revision}"


def make_rngs(root_seed, replication_id):
    """
    Create independent, addressable RNG streams.

    Identical root seed, replication ID and stream name
    produce identical random sequences.

    The order in which streams are consumed is irrelevant
    to the other streams.
    """
    for name, value in (
        ("root_seed", root_seed),
        ("replication_id", replication_id),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise ValueError(
                f"{name} must be a nonnegative integer"
            )

    streams = {}

    for name, stream_id in STREAM_IDS.items():
        sequence = np.random.SeedSequence(
            [root_seed, replication_id, stream_id]
        )

        streams[name] = np.random.default_rng(sequence)

    return streams


def result_paths(config, run_id, repo_root="."):
    """
    Reuse repository output paths instead of inventing
    a new results-directory structure.
    """
    root = Path(repo_root)
    outputs = config.get("outputs", {})

    relative_paths = {
        "raw": Path(outputs.get("raw_dir", "results/raw")) / run_id,
        "tables": Path(
            outputs.get("summary_dir", "results/tables")
        ),
        "figures": Path(
            outputs.get("figures_dir", "results/figures")
        ),
    }

    for relative in relative_paths.values():
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(
                "Output paths must remain within the project"
            )

    paths = {
        key: root / relative
        for key, relative in relative_paths.items()
    }

    for directory in paths.values():
        directory.mkdir(parents=True, exist_ok=True)

    return paths


def save_json_atomic(path, data):
    """
    Safely write one JSON artifact.

    Temporary files are created in the destination directory.
    An atomic replacement prevents partially written results
    from being mistaken for completed replications.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as file:
            temporary = Path(file.name)

            json.dump(
                data,
                file,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary, path)

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_manifest(path, config_path, config, repo_root="."):
    """Record the inputs and source revision of an experiment."""
    manifest = {
        "run_id": make_run_id(
            config_path, config, repo_root
        ),
        "config_path": str(config_path),
        "config_hash": config_hash(config),
        "root_seed": config["provenance"]["seed"],
        "git": git_state(repo_root),
        "config": config,
        "rng_stream_ids": STREAM_IDS,
    }

    save_json_atomic(path, manifest)

    return manifest
