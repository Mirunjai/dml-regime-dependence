
"""
Shared calendar-time factor ablation.

Purpose:
    Determine whether the common calendar-time factor F contributes
    to undercoverage under regime-level treatment clustering.

Factor conditions:
    sd_factor = 0.50 : shared factor ON
    sd_factor = 0.00 : shared factor OFF

Configurations:
    K = 4, matched event overlap approximately 0.5
    K = 16, matched event overlap approximately 0.5

    gamma = 0.0 and gamma = 1.0

All configurations use common simulation seeds.

Usage:
    python mc_factor_ablation.py 50

Output:
    results/mc_factor_ablation.json
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

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 50

if REPS < 2:
    raise ValueError("REPS must be at least 2.")

OUTPUT_FILE = "results/mc_factor_ablation.json"

out = {}


# ------------------------------------------------------------
# 2. Monte Carlo experiment function
# ------------------------------------------------------------

def mc(name, **kw):

    t0 = time.perf_counter()

    recs = {cell: [] for cell in CELLS}
    runtimes = []

    true_tau = kw.get("tau", 1.0)

    for s in range(REPS):

        seed = 10_000 + s

        # Generate the dataset
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

            "se_to_sd_ratio": float(
                np.mean(standard_errors) /
                np.std(tau_hat, ddof=1)
            ),

        }

    # --------------------------------------------------------
    # 4. Save results after each configuration
    # --------------------------------------------------------

    out[name] = {

        "config": {
            key: value for key, value in kw.items()
        },

        "reps": REPS,

        "sec_per_rep": float(np.mean(runtimes)),

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
# 6. Factor ablation experiments
# ------------------------------------------------------------

# Factor ON: sd_factor = 0.50
# Factor OFF: sd_factor = 0.00

for K, density in [
    (4, dens4),
    (16, dens16),
]:

    for gamma in [0.0, 1.0]:

        # Shared calendar-time factor ON
        mc(
            f"K{K}_gamma{int(gamma)}_factorON",
            density=density,
            n_regimes=K,
            gamma=gamma,
            sd_factor=0.50
        )

        # Shared calendar-time factor OFF
        mc(
            f"K{K}_gamma{int(gamma)}_factorOFF",
            density=density,
            n_regimes=K,
            gamma=gamma,
            sd_factor=0.0
        )


# ------------------------------------------------------------
# 7. Completion
# ------------------------------------------------------------

print("\nALL FACTOR-ABLATION EXPERIMENTS COMPLETED.")
print("Results saved to:", OUTPUT_FILE)
print("Repetitions per configuration:", REPS)
