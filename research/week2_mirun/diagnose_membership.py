
import numpy as np
from dgp import Config, simulate_dgp

configs = [
    ("K4", 0.4288463592529297, 4),
    ("K16", 0.2480754852294922, 16),
]

for name, density, K in configs:

    cfg = Config(
        seed=10000,
        density=density,
        n_regimes=K,
        gamma=1.0
    )

    d = simulate_dgp(cfg)

    n = cfg.n
    H = cfg.H

    idx = d["t0"][:, None] + np.arange(H)[None, :]
    rw = d["rid_t"][idx]

    memberships = [
        set(row[row >= 0].tolist())
        for row in rw
    ]

    counts = np.array([len(x) for x in memberships])

    print("\n", "=" * 50)
    print(name)
    print("=" * 50)

    print("Total events:", n)
    print("Exposed events:", int(np.sum(counts > 0)))
    print("Unexposed events:", int(np.sum(counts == 0)))

    for k in range(0, K + 1):
        count = int(np.sum(counts == k))
        if count:
            print(
                f"Events touching {k} regimes: "
                f"{count} ({100 * count / n:.2f}%)"
            )

    print(
        "Events touching multiple regimes:",
        int(np.sum(counts > 1))
    )

    # Check whether the stored first-regime label
    # agrees with the first actual regime encountered.
    first_actual = np.array([
        next(iter(sorted(x))) if x else -1
        for x in memberships
    ])

    mismatch = np.sum(first_actual != d["regime"])

    print("First-regime label mismatches:", int(mismatch))
