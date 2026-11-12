
"""Parallel, resumable Monte Carlo experiment runner.

Infrastructure only. The mock engine does not implement DML.
"""

import argparse
import hashlib
import json
import math
from concurrent.futures import (
    FIRST_COMPLETED,
    ProcessPoolExecutor,
    wait,
)
from pathlib import Path

from src.infra.reproducibility import (
    STREAM_IDS,
    config_hash,
    load_config,
    make_rngs,
    make_run_id,
    result_paths,
    save_json_atomic,
    save_manifest,
    software_versions,
    run_lock,
    validate_run_id,
)


CELL_SPEC = {
    "random_xfit__naive_var": ("random", "naive"),
    "random_xfit__robust_var": ("random", "robust"),
    "grouped_xfit__naive_var": ("grouped", "naive"),
    "grouped_xfit__robust_var": ("grouped", "robust"),
}


# ---------------------------------------------------------
# 1. Experiment configuration validation
# ---------------------------------------------------------

def validate_config(config):
    """Prevent accidental execution of incomplete configurations."""

    seed = config["provenance"]["seed"]
    count = config["replications"]["count"]

    for name, value, minimum in (
        ("seed", seed, 0),
        ("replications.count", count, 1),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < minimum
        ):
            raise ValueError(
                f"{name} must be an integer >= {minimum}"
            )

    cells = config["ablation_cells"]

    if len(cells) != 4:
        raise ValueError("Exactly four DML cells are required")

    actual = {}

    for cell in cells:
        cell_id = cell["id"]

        if cell_id in actual:
            raise ValueError("Duplicate DML cell")

        actual[cell_id] = (
            cell["cross_fitting"],
            cell["variance_estimation"],
        )

    if actual != CELL_SPEC:
        raise ValueError(
            "Cell definitions do not match the locked 2x2 design"
        )

    if config.get("engine") != "mock":
        raise ValueError(
            "Phase 3 supports only the explicit mock engine. "
            "Real DML integration requires separate review."
        )

    truth = float(
        config["_resolved_dgp"]["treatment"]["effect_true"]
    )

    if not math.isfinite(truth):
        raise ValueError("True treatment effect must be finite")


def load_experiment(config_path, repo_root):
    """
    Load existing experiment and referenced DGP configurations.

    Include the resolved DGP in the in-memory fingerprint so
    changes to DGP settings create a different experiment ID.
    """
    root = Path(repo_root).resolve()

    experiment_path = root / config_path
    experiment_path = experiment_path.resolve()

    if not experiment_path.is_relative_to(root):
        raise ValueError(
            "Experiment config must be inside the repository"
        )

    config = load_config(experiment_path)

    dgp_reference = config["provenance"]["dgp_config"]
    dgp_path = (root / dgp_reference).resolve()

    if not dgp_path.is_relative_to(root):
        raise ValueError(
            "DGP configuration must be inside the repository"
        )

    config["_resolved_dgp"] = load_config(dgp_path)

    validate_config(config)

    relative_path = experiment_path.relative_to(root)

    return relative_path, config


# ---------------------------------------------------------
# 2. Source fingerprint for safe resumption
# ---------------------------------------------------------

def source_fingerprint(repo_root):
    """
    Hash project Python source and dependency declarations.

    This prevents mixing results from different uncommitted
    implementations under the same Git commit and run ID.
    """
    root = Path(repo_root)
    paths = sorted(
        (root / "src").rglob("*.py")
    )

    paths += [
        root / "requirements.txt",
        root / "requirements-dev.txt",
    ]

    digest = hashlib.sha256()

    for path in sorted(paths):
        if not path.is_file():
            continue

        digest.update(
            path.relative_to(root).as_posix().encode()
        )
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")

    return digest.hexdigest()


# ---------------------------------------------------------
# 3. Mock four-cell estimator
# ---------------------------------------------------------

def mock_four_cells(config, rngs):
    """
    Return four mock estimates on one shared artificial outcome.

    This is only a software test, NOT Double Machine Learning.
    """
    truth = float(
        config["_resolved_dgp"]["treatment"]["effect_true"]
    )

    noise = (
        0.06 * rngs["factors"].normal()
        + 0.04 * rngs["regimes"].normal()
        + 0.02 * rngs["estimator"].normal()
    )

    # The same mock estimate is used by all four cells.
    estimate = truth + noise

    half_widths = {
        "random_xfit__naive_var": 0.10,
        "random_xfit__robust_var": 0.15,
        "grouped_xfit__naive_var": 0.11,
        "grouped_xfit__robust_var": 0.16,
    }

    return {
        cell: {
            "estimate": estimate,
            "lower": estimate - width,
            "upper": estimate + width,
        }
        for cell, width in half_widths.items()
    }


# ---------------------------------------------------------
# 4. One independent replication
# ---------------------------------------------------------

def failed_cells(message):
    """Materialize all four failures rather than omitting rows."""
    return {
        cell: {
            "status": "failed",
            "estimate": None,
            "lower": None,
            "upper": None,
            "error": message,
        }
        for cell in CELL_SPEC
    }


def run_replication(replication_id, config, run_id):
    """
    Execute one replication and save the four-cell information
    in a serializable Python dictionary.
    """
    root_seed = config["provenance"]["seed"]

    rngs = make_rngs(root_seed, replication_id)

    try:
        estimates = mock_four_cells(config, rngs)

    except Exception as exc:
        estimates = failed_cells(
            f"{type(exc).__name__}: {exc}"
        )

    cells = []

    for cell in CELL_SPEC:
        try:
            result = estimates[cell]

            if result.get("status", "ok") != "ok":
                raise RuntimeError(
                    result.get("error", "Estimator failed")
                )

            estimate = float(result["estimate"])
            lower = float(result["lower"])
            upper = float(result["upper"])

            if not all(
                math.isfinite(value)
                for value in (estimate, lower, upper)
            ):
                raise ValueError("Nonfinite estimate or bounds")

            if lower > upper:
                raise ValueError("Invalid confidence interval")

            cells.append({
                "cell": cell,
                "status": "ok",
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
                "error": None,
            })

        except Exception as exc:
            cells.append({
                "cell": cell,
                "status": "failed",
                "estimate": None,
                "lower": None,
                "upper": None,
                "error": f"{type(exc).__name__}: {exc}",
            })

    return {
        "run_id": run_id,
        "replication_id": replication_id,
        "root_seed": root_seed,
        "config_hash": config_hash(config),
        "truth": float(
            config["_resolved_dgp"]["treatment"]["effect_true"]
        ),
        "seed_addresses": {
            name: [
                root_seed,
                replication_id,
                stream_id,
            ]
            for name, stream_id in STREAM_IDS.items()
        },
        "cells": cells,
    }


def _worker(replication_id, config, run_id):
    """Top-level multiprocessing worker, macOS spawn compatible."""
    return run_replication(replication_id, config, run_id)


# ---------------------------------------------------------
# 5. Validate existing raw results before resuming
# ---------------------------------------------------------

def validate_saved_result(
    path, replication_id, run_id, config
):
    """
    Reject corrupted or mismatched records.

    Failed estimator cells are still complete records:
    they are not silently retried or discarded.
    """
    try:
        with path.open("r", encoding="utf-8") as file:
            result = json.load(file)

    except (OSError, ValueError) as exc:
        raise ValueError(
            f"Unreadable saved replication: {path}"
        ) from exc

    validate_run_id(run_id)
    if not isinstance(result, dict):
        raise ValueError("Saved replication must be a mapping")

    expected = {
        "run_id": run_id,
        "replication_id": replication_id,
        "root_seed": config["provenance"]["seed"],
        "config_hash": config_hash(config),
        "truth": float(config["_resolved_dgp"]["treatment"]["effect_true"]),
        "seed_addresses": {
            name: [config["provenance"]["seed"], replication_id, stream_id]
            for name, stream_id in STREAM_IDS.items()
        },
    }

    for key, value in expected.items():
        if result.get(key) != value:
            raise ValueError(
                f"Saved replication metadata mismatch for {key}: {path}"
            )

    cells = result.get("cells")

    if not isinstance(cells, list) or len(cells) != 4:
        raise ValueError("Incomplete saved cell list")

    if not all(
        isinstance(cell, dict) and isinstance(cell.get("cell"), str)
        for cell in cells
    ):
        raise ValueError("Malformed saved cell identities")

    ids = [cell.get("cell") for cell in cells]

    if len(set(ids)) != 4 or set(ids) != set(CELL_SPEC):
        raise ValueError("Invalid saved cell identities")

    for cell in cells:
        if cell.get("status") not in ("ok", "failed"):
            raise ValueError("Invalid saved cell status")

        if cell["status"] == "ok":
            try:
                values = [
                    float(cell[key])
                    for key in ("estimate", "lower", "upper")
                ]
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    "Malformed successful cell"
                ) from exc

            if not all(map(math.isfinite, values)):
                raise ValueError("Nonfinite successful cell")

            if values[1] > values[2]:
                raise ValueError("Reversed saved interval")

    return result


# ---------------------------------------------------------
# 6. Main experiment runner
# ---------------------------------------------------------

def run_experiment(
    config_path,
    *,
    workers=1,
    repo_root=".",
):
    """
    Run missing replications, or resume an interrupted run.

    Replication outputs are written only by the parent process,
    avoiding concurrent writes to the same result file.
    """
    if (
        isinstance(workers, bool)
        or not isinstance(workers, int)
        or workers < 1
    ):
        raise ValueError("workers must be a positive integer")

    root = Path(repo_root).resolve()

    relative_config, config = load_experiment(
        config_path, root
    )

    run_id = make_run_id(
        relative_config,
        config,
        root,
    )

    paths = result_paths(
        config,
        run_id,
        root,
    )

    run_dir = paths["raw"]
    with run_lock(run_dir):
        manifest_path = run_dir / "manifest.json"

        current_fingerprint = source_fingerprint(root)

        if manifest_path.exists():
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )

            if manifest.get("source_changed_during_run"):
                raise ValueError("Run was invalidated by a source change")

            if manifest.get("run_id") != run_id:
                raise ValueError("Manifest run ID mismatch")

            if (manifest.get("config_hash") != config_hash(config)
                    or config_hash(manifest.get("config")) != config_hash(config)):
                raise ValueError("Manifest configuration mismatch")

            if manifest.get("source_fingerprint") != current_fingerprint:
                raise ValueError(
                    "Source changed since this run started. "
                    "Use a new experiment identity; do not mix versions."
                )

            if manifest.get("software") != software_versions():
                raise ValueError(
                    "Software environment changed since this run started"
                )

            if (manifest.get("root_seed") != config["provenance"]["seed"]
                    or manifest.get("rng_stream_ids") != STREAM_IDS):
                raise ValueError("Manifest RNG provenance mismatch")

        else:
            manifest = save_manifest(
                manifest_path,
                relative_config,
                config,
                root,
            )

            manifest["source_fingerprint"] = current_fingerprint

            save_json_atomic(manifest_path, manifest)

        if manifest["git"]["dirty"]:
            print(
                "WARNING: Uncommitted code detected. "
                "These are development results, not a frozen "
                "scientific experiment."
            )

        count = config["replications"]["count"]

        pending = []

        for replication_id in range(count):
            path = (
                run_dir / f"rep_{replication_id:06d}.json"
            )

            if path.exists():
                validate_saved_result(
                    path,
                    replication_id,
                    run_id,
                    config,
                )
            else:
                pending.append(replication_id)

        print(f"Run ID: {run_id}")
        print(f"Total replications: {count}")
        print(f"Already completed: {count - len(pending)}")
        print(f"Remaining: {len(pending)}")
        print(f"Workers: {workers}")

        def save_result(result):
            replication_id = result["replication_id"]

            path = (
                run_dir / f"rep_{replication_id:06d}.json"
            )

            save_json_atomic(path, result)

        if workers == 1:
            for replication_id in pending:
                result = _worker(
                    replication_id,
                    config,
                    run_id,
                )

                save_result(result)

        else:
            # Keep only a bounded number of futures in memory.
            iterator = iter(pending)

            with ProcessPoolExecutor(
                max_workers=workers
            ) as executor:

                futures = {}

                def submit_next():
                    try:
                        replication_id = next(iterator)
                    except StopIteration:
                        return

                    future = executor.submit(
                        _worker,
                        replication_id,
                        config,
                        run_id,
                    )

                    futures[future] = replication_id

                for _ in range(min(workers * 2, len(pending))):
                    submit_next()

                while futures:
                    completed, _ = wait(
                        tuple(futures),
                        return_when=FIRST_COMPLETED,
                    )

                    for future in completed:
                        replication_id = futures.pop(future)

                        try:
                            result = future.result()

                        except Exception as exc:
                            # Worker-level failure remains visible
                            # as four failed cell records.
                            result = run_replication_failure(
                                replication_id,
                                config,
                                run_id,
                                f"{type(exc).__name__}: {exc}",
                            )

                        save_result(result)
                        submit_next()

        if source_fingerprint(root) != current_fingerprint:
            manifest["source_changed_during_run"] = True
            save_json_atomic(manifest_path, manifest)
            raise ValueError("Source changed during run; results cannot be mixed")

        if manifest.get("source_changed_during_run"):
            raise ValueError("Run was invalidated by a source change")

        print(f"Raw results saved in: {run_dir}")

        return run_dir


def run_replication_failure(
    replication_id, config, run_id, message
):
    """Record a failed worker without rerunning it silently."""
    root_seed = config["provenance"]["seed"]

    return {
        "run_id": run_id,
        "replication_id": replication_id,
        "root_seed": root_seed,
        "config_hash": config_hash(config),
        "truth": float(
            config["_resolved_dgp"]["treatment"]["effect_true"]
        ),
        "seed_addresses": {
            name: [root_seed, replication_id, stream_id]
            for name, stream_id in STREAM_IDS.items()
        },
        "cells": [
            {"cell": cell, **record}
            for cell, record in failed_cells(message).items()
        ],
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        required=True,
        help="Experiment YAML relative to repository root",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--repo-root",
        default=".",
    )

    args = parser.parse_args()

    run_experiment(
        args.config,
        workers=args.workers,
        repo_root=args.repo_root,
    )


if __name__ == "__main__":
    main()
