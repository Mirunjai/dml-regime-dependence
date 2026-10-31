
"""Check whether regime counts can match realized pair density."""

from math import comb

import numpy as np

from src.dgp.regime_shocks import simulate_regimes


def pair_density(regime_id):
    """Fraction of all window pairs sharing an active regime."""
    ids = np.asarray(regime_id)
    n = len(ids)
    if n < 2:
        return 0.0

    _, counts = np.unique(ids[ids >= 0], return_counts=True)
    matching_pairs = sum(comb(int(c), 2) for c in counts if c >= 2)
    return matching_pairs / comb(n, 2)


def run_experiment():
    n_windows = 1000
    target_density = 0.0495
    regime_counts = [5, 10, 20, 50]
    grid = np.linspace(0.0, 1.0, 1001)

    print("MATCHED PAIR-DENSITY FEASIBILITY")
    print(f"Target pair density: {target_density:.4f}")
    print("Regimes | Active density | Pair density | Error")

    for n_regimes in regime_counts:
        best = None

        for density in grid:
            n_active = round(n_windows * float(density))
            if 0 < n_active < n_regimes:
                continue

            ids, _ = simulate_regimes(
                n_windows,
                float(density),
                n_regimes,
                np.random.default_rng(42),
            )

            realized = pair_density(ids)
            error = abs(realized - target_density)

            if best is None or error < best[0]:
                best = (error, density, realized)

        error, density, realized = best
        print(
            f"{n_regimes:7d} | {density:14.3f} | "
            f"{realized:12.5f} | {error:.5f}"
        )


if __name__ == "__main__":
    run_experiment()
