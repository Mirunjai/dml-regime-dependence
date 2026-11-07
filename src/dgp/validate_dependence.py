
"""Week 2: Validate regime-level cross-sectional dependence."""

import numpy as np

from src.dgp.regime_shocks import simulate_regimes
from src.dgp.matched_density import pair_density


def run_experiment(density, n_regimes, seed=42):
    """Generate toy returns and measure shared-shock dependence."""
    regime_seed, noise_seed = np.random.SeedSequence(seed).spawn(2)
    rng = np.random.default_rng(regime_seed)

    n_windows = 1000
    n_firms = 100

    regime_id, shocks = simulate_regimes(
        n_periods=n_windows,
        density=density,
        n_regimes=n_regimes,
        rng=rng,
    )

    # Each firm's return includes independent noise and
    # an exposure to the common shock for that window.
    firm_noise = np.random.default_rng(noise_seed).standard_normal((n_firms, n_windows))
    loadings = np.ones((n_firms, 1))
    returns = firm_noise + loadings * shocks

    # Average correlation between distinct firms.
    corr = np.corrcoef(returns)
    upper = corr[np.triu_indices(n_firms, k=1)]
    avg_corr = float(np.mean(upper))

    # Fraction of window pairs assigned the same active regime.
    realized_density = pair_density(regime_id)

    return avg_corr, realized_density


def main():
    print("WEEK 2: DEPENDENCE VALIDATION")
    print("-" * 65)

    print("\nExperiment 1: Vary density")
    for density in [0.1, 0.3, 0.5, 0.7, 0.9]:
        corr, pair_density = run_experiment(
            density=density,
            n_regimes=5,
        )
        print(
            f"Density={density:.1f} | "
            f"Avg correlation={corr:.4f} | "
            f"Pair density={pair_density:.4f}"
        )

    print("\nExperiment 2: Vary regime count")
    for n_regimes in [5, 10, 20, 50]:
        corr, pair_density = run_experiment(
            density=0.5,
            n_regimes=n_regimes,
        )
        print(
            f"Regimes={n_regimes:2d} | "
            f"Avg correlation={corr:.4f} | "
            f"Pair density={pair_density:.4f}"
        )


if __name__ == "__main__":
    main()
