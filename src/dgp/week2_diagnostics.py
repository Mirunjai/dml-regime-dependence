"""Event-index toy diagnostics; descriptive associations do not prove independence."""
import numpy as np

from src.dgp.regime_shocks import simulate_regimes
from src.dgp.matched_density import pair_density


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
    association = None if np.ptp(treatment) == 0 or np.ptp(exposure) == 0 else float(np.corrcoef(treatment, exposure)[0, 1])

    return pair_density(ids), association


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
    associations = [
        experiment(0.5, 5, seed)[1]
        for seed in seeds
    ]
    valid = np.array([value for value in associations if value is not None])
    print(f"Defined associations: {valid.size}/{len(associations)}; undefined values are not zero.")
    print("Mean association:", valid.mean() if valid.size else None)
    print("SD association:", valid.std(ddof=1) if valid.size > 1 else None)
    print("Max absolute association:", np.abs(valid).max() if valid.size else None)
    print("Descriptive toy checks only. Balanced regime counts fix pair density across seeds; small treatment correlations do not prove independence.")


if __name__ == "__main__":
    main()
