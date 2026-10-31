
"""Generate shared regime shocks for Monte Carlo experiments."""

import numpy as np


def simulate_regimes(n_periods, density, n_regimes, rng):
    """
    Generate regime assignments and shared shocks.

    n_periods:
        Number of event windows in this component.
        The name is retained for interface compatibility.
    density:
        Fraction of event windows exposed to common shocks.
    n_regimes:
        Number of independent regime-level shock realizations.
    rng:
        NumPy random Generator.

    Returns:
        regime_id: integer array, -1 for inactive windows.
        U: shock exposure for each event window.

    Windows assigned the same regime share exactly the same
    underlying shock realization.
    """
    if not isinstance(n_periods, (int, np.integer)) or n_periods <= 0:
        raise ValueError("n_periods must be a positive integer")

    if not isinstance(n_regimes, (int, np.integer)) or n_regimes <= 0:
        raise ValueError("n_regimes must be a positive integer")

    if not np.isfinite(density) or not 0 <= density <= 1:
        raise ValueError("density must be between 0 and 1")

    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a NumPy Generator")

    n_active = int(round(n_periods * density))

    if 0 < n_active < n_regimes:
        raise ValueError(
            "Not enough active event windows to represent "
            "all requested regimes. Increase density or "
            "reduce n_regimes."
        )

    regime_id = np.full(n_periods, -1, dtype=int)
    U = np.zeros(n_periods, dtype=float)

    if n_active == 0:
        return regime_id, U

    # Randomly select exposed event windows.
    active_indices = rng.choice(
        n_periods, size=n_active, replace=False
    )

    # Draw one independent realization per regime.
    regime_shocks = rng.standard_normal(n_regimes)

    # Ensure every requested regime is represented.
    assignments = np.arange(n_active) % n_regimes
    rng.shuffle(assignments)

    regime_id[active_indices] = assignments

    # Windows in the same regime receive the same shock.
    U[active_indices] = regime_shocks[assignments]

    return regime_id, U
