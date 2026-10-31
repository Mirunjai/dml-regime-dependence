"""Component-level volatility/regime diagnostics and an invalid positive control.

This is not the integrated event-study DGP. A time index is aligned with one
synthetic event-window index for this diagnostic only. Actual date/window mapping
and a team-frozen regime version still belong to the integration/gate decision.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from numpy.typing import ArrayLike

from src.dgp.volatility import _count, _finite_real

RegimeSimulator = Callable[[int, float, int, np.random.Generator], tuple[np.ndarray, np.ndarray]]


@contextmanager
def regime_reference(
    repo: Path, ref: str, *, snapshot_dir: Path | None = None,
) -> Iterator[tuple[RegimeSimulator, dict]]:
    """Load exact teammate Git source temporarily, without merging or editing it.

    Imports Python code from the explicitly selected project repository. This is
    for trusted team code, not an untrusted plugin loader. Provenance records the
    resolved commit and source hash, independent of an edited worktree file.
    """
    repo = Path(repo).resolve()
    sha = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{ref}^{{commit}}"], text=True
    ).strip()
    source_path = "src/dgp/regime_shocks.py"
    source = subprocess.check_output(["git", "-C", str(repo), "show", f"{sha}:{source_path}"])
    metadata = {
        "commit": sha, "source_path": source_path,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "url": f"https://github.com/Mirunjai/dml-regime-dependence/blob/{sha}/{source_path}",
        "team_frozen_status": "not established by this diagnostic; exact commit and source hash recorded",
        "mapping": "one time index per synthetic event-window index; diagnostic only",
    }
    with tempfile.TemporaryDirectory(prefix="ada-regime-reference-") as temporary:
        path = Path(temporary) / "regime_shocks.py"
        path.write_bytes(source)
        spec = importlib.util.spec_from_file_location("_ada_pinned_regime_reference", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        simulator = getattr(module, "simulate_regimes")
        if not callable(simulator):
            raise TypeError("Reference does not export callable simulate_regimes")
        if snapshot_dir is not None:
            snapshot_dir = Path(snapshot_dir)
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            (snapshot_dir / "regime_shocks.py").write_bytes(source)
            metadata["raw_snapshot"] = "reference/regime_shocks.py (ignored raw output)"
        yield simulator, metadata


def _correlation(a: np.ndarray, b: np.ndarray) -> float | None:
    a, b = a - a.mean(), b - b.mean()
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    # Near-constant h at rho=0 has no stochastic variation to test.
    if denominator == 0 or np.ptp(a) <= np.finfo(float).eps or np.ptp(b) <= np.finfo(float).eps:
        return None
    return float(np.dot(a, b) / denominator)


def dependence_statistics(
    variance: ArrayLike, regime_id: ArrayLike, shocks: ArrayLike,
) -> dict[str, float | None]:
    """Signed associations of mean log conditional variance with U, U², exposure.

    Lags 0 and 1 are checked. Pooling is only a statistic, never an iid sample-size
    claim. This detects common-direction state/shock association; it cannot prove
    every possible form of independence (e.g. exact cancellation across firms).
    """
    h = np.asarray(variance, dtype=float)
    ids, u = np.asarray(regime_id), np.asarray(shocks, dtype=float)
    if h.ndim != 2 or min(h.shape) < 1 or u.ndim != 1 or ids.shape != u.shape or h.shape[1] != u.size:
        raise ValueError("Require variance[firm,time] and matching 1-D regime arrays")
    if not np.isfinite(h).all() or np.any(h <= 0) or not np.isfinite(u).all():
        raise ValueError("Require positive finite variance and finite shocks")
    if ids.dtype.kind not in "iu" or np.any(ids < -1):
        raise ValueError("Regime IDs must be integers >= -1")
    if np.any(u[ids == -1] != 0):
        raise ValueError("Inactive regime entries must have zero shock")
    state = np.mean(np.log(h), axis=0)
    with np.errstate(over="raise", invalid="raise"):
        features = {"signed_shock": u, "squared_shock": u**2, "exposure": (ids >= 0).astype(float)}
    result = {}
    for name, feature in features.items():
        for lag in (0, 1):
            result[f"{name}_lag{lag}"] = (
                _correlation(state[lag:], feature[:u.size - lag]) if u.size - lag >= 2 else None
            )
    return result


def positive_control(variance: ArrayLike, shocks: ArrayLike, strength: float = 1.0) -> np.ndarray:
    """Deliberately violate independence by multiplying h by a function of U².

    Never use this corrupted state in a scientific DGP. It exists solely to
    demonstrate diagnostic sensitivity, including magnitude dependence.
    """
    h, u = np.asarray(variance, dtype=float), np.asarray(shocks, dtype=float)
    strength = _finite_real("strength", strength)
    if strength <= 0:
        raise ValueError("strength must be positive")
    if h.ndim != 2 or u.ndim != 1 or h.shape[1] != u.size or u.size == 0:
        raise ValueError("Require matching variance[firm,time] and shocks[time]")
    if not np.isfinite(h).all() or np.any(h <= 0) or not np.isfinite(u).all():
        raise ValueError("Require positive finite variance and finite shocks")
    with np.errstate(over="raise", invalid="raise"):
        squares = u**2
        scale = float(np.mean(squares))
        if scale == 0:
            raise ValueError("Positive control is undefined with all-zero shocks")
        return h * (1 + strength * squares / scale)


def conditional_randomization_check(
    variance: ArrayLike,
    regime_id: ArrayLike,
    shocks: ArrayLike,
    simulator: RegimeSimulator,
    *,
    density: float,
    n_regimes: int,
    rng: np.random.Generator,
    randomizations: int = 199,
) -> dict:
    """Monte Carlo null check resampling the *whole* regime process conditional on h.

    Under independence and the stated known regime simulator, observed and null
    shock vectors are exchangeable conditional on h. Their repeated-regime
    structure is retained. Use max absolute association over six features to
    calibrate this family of diagnostics jointly. p=(1+#null>=observed)/(B+1)
    includes ties, avoiding zero p-values. Independent panels, not flattened
    panel rows, determine reported detection-rate uncertainty.
    """
    randomizations = _count("randomizations", randomizations)
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    observed = dependence_statistics(variance, regime_id, shocks)
    values = [abs(value) for value in observed.values() if value is not None]
    if not values:
        return {"status": "undefined", "reason": "constant or insufficient state/shock variation",
                "associations": observed, "statistic": None, "p_value": None,
                "randomizations": 0, "null_at_least_observed": None}
    statistic = max(values)
    exceedances = 0
    for _ in range(randomizations):
        null_ids, null_shocks = simulator(len(shocks), density, n_regimes, rng)
        null_stats = dependence_statistics(variance, null_ids, null_shocks)
        values = [abs(value) for value in null_stats.values() if value is not None]
        if not values:
            # A failed null draw must not silently shrink the denominator.
            raise ValueError("Null regime draw has no usable diagnostic variation")
        exceedances += max(values) >= statistic
    return {"status": "evaluated", "associations": observed, "statistic": statistic,
            "p_value": (1 + int(exceedances)) / (randomizations + 1),
            "randomizations": randomizations, "null_at_least_observed": int(exceedances)}
