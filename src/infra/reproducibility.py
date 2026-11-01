
"""Reusable experiment configuration and reproducibility utilities."""

import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
from contextlib import contextmanager
from importlib.metadata import version
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


def validate_run_id(run_id):
    """Require a single portable filename token, including for saved manifests."""
    if (not isinstance(run_id, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]+", run_id)):
        raise ValueError("Unsafe run ID")
    return run_id


def software_versions():
    """Record the runtime needed to interpret and replay RNG draws."""
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "matplotlib": version("matplotlib"),
        "pyyaml": yaml.__version__,
        "rng_bit_generator": type(np.random.default_rng(0).bit_generator).__name__,
    }


@contextmanager
def run_lock(run_dir):
    """Reject a second controlling process; OS locks release on process exit.

    Keep the lock file after release so all callers lock the same inode.
    Local filesystems are supported; network filesystem locking is not verified.
    """
    with (Path(run_dir) / ".runner.lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError(
                    "Run is already locked or lock unavailable"
                ) from exc
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError(
                    "Run is already locked or lock unavailable"
                ) from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def result_paths(config, run_id, repo_root="."):
    """
    Reuse repository output paths instead of inventing
    a new results-directory structure.
    """
    validate_run_id(run_id)
    root = Path(repo_root).resolve()
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
        key: (root / relative).resolve()
        for key, relative in relative_paths.items()
    }

    if any(not path.is_relative_to(root) for path in paths.values()):
        raise ValueError("Output paths must remain within the project")

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
        "software": software_versions(),
    }

    save_json_atomic(path, manifest)

    return manifest
