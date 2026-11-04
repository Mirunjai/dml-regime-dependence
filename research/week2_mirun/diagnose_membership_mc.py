
import numpy as np
from dgp import Config, simulate_dgp

CONFIGS = [
    ("K4", 0.4288463592529297, 4),
    ("K16", 0.2480754852294922, 16),
]

REPS = 200

for name, density, K in CONFIGS:

    total_events = 0
    total_exposed = 0
    total_multi = 0
    total_mismatch = 0
    total_overlapping_pairs = 0
    total_pairs = 0

    max_cluster_sizes = []
    regime_cluster_counts = []

    for s in range(REPS):

        d = simulate_dgp(Config(
            seed=10000 + s,
            density=density,
            n_regimes=K,
            gamma=1.0
        ))

        n = d["cfg"].n
        H = d["cfg"].H

        idx = d["t0"][:, None] + np.arange(H)[None, :]
        rw = d["rid_t"][idx]

        memberships = [
            set(row[row >= 0].tolist())
            for row in rw
        ]

        counts = np.array([len(x) for x in memberships])

        first_actual = np.array([
            min(x) if x else -1 for x in memberships
        ])

        total_events += n
        total_exposed += int(np.sum(counts > 0))
        total_multi += int(np.sum(counts > 1))
        total_mismatch += int(
            np.sum(first_actual != d["regime"])
        )

        # Regime cluster sizes, excluding singleton unexposed events
        cluster = d["cluster"]
        unique, sizes = np.unique(cluster, return_counts=True)

        exposed_sizes = sizes[unique >= 0]

        if len(exposed_sizes):
            max_cluster_sizes.append(int(exposed_sizes.max()))
            regime_cluster_counts.append(len(exposed_sizes))

        # Calendar-window overlap between distinct event pairs
        starts = d["t0"]

        for i in range(n):
            for j in range(i + 1, n):
                total_pairs += 1

                overlap = (
                    max(starts[i], starts[j])
                    <
                    min(starts[i] + H, starts[j] + H)
                )

                if overlap:
                    total_overlapping_pairs += 1

    print("\n" + "=" * 55)
    print(name, "- 200 SEED DIAGNOSTIC")
    print("=" * 55)

    print("Total events:", total_events)
    print("Exposed events:", total_exposed)
    print("Multi-regime events:", total_multi)
    print(
        "Multi-regime event percentage:",
        round(100 * total_multi / total_events, 3)
    )
    print("First-regime label mismatches:", total_mismatch)

    print(
        "Mean exposed regime clusters:",
        round(np.mean(regime_cluster_counts), 2)
    )

    print(
        "Mean largest regime cluster size:",
        round(np.mean(max_cluster_sizes), 2)
    )

    print("Total event pairs:", total_pairs)
    print("Overlapping calendar-window pairs:", total_overlapping_pairs)
    print(
        "Calendar-window overlap percentage:",
        round(100 * total_overlapping_pairs / total_pairs, 3)
    )
