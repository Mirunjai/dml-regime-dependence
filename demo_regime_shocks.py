
"""Demonstrate the two independent experimental controls."""

import numpy as np

from src.dgp.regime_shocks import simulate_regimes


N_WINDOWS = 1000

for n_regimes in [5, 20, 50]:
    for density in [0.2, 0.5, 0.9]:
        ids, shocks = simulate_regimes(
            n_periods=N_WINDOWS,
            density=density,
            n_regimes=n_regimes,
            rng=np.random.default_rng(42),
        )

        active = ids >= 0
        actual_regimes = len(np.unique(ids[active]))

        print(
            f"Regimes={n_regimes:2d} | "
            f"Density={density:.1f} | "
            f"Exposed windows={active.sum():4d} | "
            f"Distinct regimes={actual_regimes:2d}"
        )
