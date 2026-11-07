
import numpy as np

from src.dgp.regime_shocks import simulate_regimes


def pair_density(ids):
    """Fraction of all window pairs sharing an active regime."""
    n = len(ids)
    active = ids[ids >= 0]

    if n < 2 or len(active) == 0:
        return 0.0

    counts = np.unique(active, return_counts=True)[1]
    shared = np.sum(counts * (counts - 1) / 2)
    return float(shared / (n * (n - 1) / 2))


def experiment(density, n_regimes, seed):
    rng = np.random.default_rng(seed)

    ids, shocks = simulate_regimes(
        1000, density, n_regimes, rng
    )

    # Separate RNG stream for treatment timing.
    treatment_rng = np.random.default_rng(
        np.random.SeedSequence([seed, 12345])
    )

    treatment = treatment_rng.integers(0, 2, size=1000)

    # Association between treatment and shock exposure.
    exposure = (ids >= 0).astype(float)
    association = np.corrcoef(treatment, exposure)[0, 1]

    return pair_density(ids), float(association)


def main():
    seeds = range(100)

    print("\nEXPERIMENT A: DENSITY VALIDATION")
    print("Density | Mean pair density | SD")

    for density in [0.1, 0.3, 0.5, 0.7, 0.9]:
        results = np.array([
            experiment(density, 5, seed)[0]
            for seed in seeds
        ])

        print(
            f"{density:.1f}     | "
            f"{results.mean():.4f}            | "
            f"{results.std(ddof=1):.4f}"
        )

    print("\nEXPERIMENT B: REGIME COUNT")
    print("Regimes | Mean pair density | SD")

    for regimes in [5, 10, 20, 50]:
        results = np.array([
            experiment(0.5, regimes, seed)[0]
            for seed in seeds
        ])

        print(
            f"{regimes:2d}      | "
            f"{results.mean():.4f}            | "
            f"{results.std(ddof=1):.4f}"
        )

    print("\nEXPERIMENT C: TREATMENT INDEPENDENCE")
    associations = np.array([
        experiment(0.5, 5, seed)[1]
        for seed in seeds
    ])

    print("Mean association:", associations.mean())
    print("SD association:", associations.std(ddof=1))
    print("Max absolute association:", np.abs(associations).max())


if __name__ == "__main__":
    main()
