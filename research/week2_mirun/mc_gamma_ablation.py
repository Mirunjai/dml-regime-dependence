
"""
Controlled gamma-ablation Monte Carlo experiment.

Purpose:
    Compare regime-dependent outcome simulations with:
        gamma = 0.0 : no regime-level treatment clustering
        gamma = 1.0 : regime-level treatment clustering

Configurations:
    K = 4, matched event overlap approximately 0.5
    K = 16, matched event overlap approximately 0.5

All configurations use common simulation seeds.

Usage:
    python mc_gamma_ablation.py 20

Output:
    results/mc_gamma_ablation.json
"""

import sys
import json
import time
import numpy as np

from dgp import *
from dml import *


# ------------------------------------------------------------
# 1. Experiment settings
# ------------------------------------------------------------

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 20

if REPS < 2:
    raise ValueError("REPS must be at least 2.")

OUTPUT_FILE = "results/mc_gamma_ablation.json"

out = {}


# ------------------------------------------------------------
# 2. Monte Carlo experiment function
# ------------------------------------------------------------

def mc(name, **kw):
    """
    Run Monte Carlo repetitions for one configuration.

    Uses identical seed sequences across configurations,
    allowing paired comparisons between gamma conditions.
    """

    t0 = time.perf_counter()

    recs = {cell: [] for cell in CELLS}
    runtimes = []

    true_tau = kw.get("tau", 1.0)

    for s in range(REPS):

        seed = 10_000 + s

        # Generate simulated dataset
        d = simulate_dgp(Config(seed=seed, **kw))

        # Run all four DML cells
        start = time.perf_counter()
        rows, _ = run_dml(d, seed=seed)

        runtimes.append(time.perf_counter() - start)

        # Store results
        for r in rows:
            recs[(r["folds"], r["variance"])].append(r)

    # --------------------------------------------------------
    # 3. Calculate Monte Carlo statistics
    # --------------------------------------------------------

    results = {}

    for cell, rs in recs.items():

        tau_hat = np.array([r["tau"] for r in rs])
        lower = np.array([r["lo"] for r in rs])
        upper = np.array([r["hi"] for r in rs])
        standard_errors = np.array([r["se"] for r in rs])

        coverage = float(
            np.mean((lower <= true_tau) & (true_tau <= upper))
        )

        results["/".join(cell)] = {

            "coverage": coverage,

            "mc_se_cov": float(
                np.sqrt(coverage * (1.0 - coverage) / REPS)
            ),

            "bias": float(
                np.mean(tau_hat) - true_tau
            ),

            "width": float(
                np.mean(upper - lower)
            ),

            "sd_tau": float(
                np.std(tau_hat, ddof=1)
            ),

            "mean_se": float(
                np.mean(standard_errors)
            ),

        }

    # --------------------------------------------------------
    # 4. Save configuration and results
    # --------------------------------------------------------

    out[name] = {

        "config": {
            key: value for key, value in kw.items()
        },

        "reps": REPS,

        "sec_per_rep": float(
            np.mean(runtimes)
        ),

        "results": results,

    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print(
        name,
        "done",
        round(time.perf_counter() - t0, 2),
        "seconds",
        flush=True
    )


# ------------------------------------------------------------
# 5. Match event overlap across regime counts
# ------------------------------------------------------------

print("Calculating matched-overlap densities...", flush=True)

dens4 = density_for_overlap(0.5, 4)
dens16 = density_for_overlap(0.5, 16)

print(f"K=4 density:  {dens4:.6f}")
print(f"K=16 density: {dens16:.6f}")


# ------------------------------------------------------------
# 6. Controlled gamma-ablation experiments
# ------------------------------------------------------------

# K = 4, gamma = 0
mc(
    "dependent_K4_gamma0",
    density=dens4,
    n_regimes=4,
    gamma=0.0
)

# K = 4, gamma = 1
mc(
    "dependent_K4_gamma1",
    density=dens4,
    n_regimes=4,
    gamma=1.0
)

# K = 16, gamma = 0
mc(
    "dependent_K16_gamma0",
    density=dens16,
    n_regimes=16,
    gamma=0.0
)

# K = 16, gamma = 1
mc(
    "dependent_K16_gamma1",
    density=dens16,
    n_regimes=16,
    gamma=1.0
)


# ------------------------------------------------------------
# 7. Completion
# ------------------------------------------------------------

print("\nALL GAMMA-ABLATION EXPERIMENTS COMPLETED.")
print("Results saved to:", OUTPUT_FILE)
print("Repetitions per configuration:", REPS)
