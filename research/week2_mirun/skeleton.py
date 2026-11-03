"""Week 1 deliverable: runnable DGP skeleton on placeholders, plus proof that Week 2 v0 is the same skeleton with real modules.
Run:  python skeleton.py"""
import numpy as np
from dgp import *; from dml import run_dml

cfg = Config(seed=3, density=0.0, n_regimes=0, gamma=0.0)
sk = build_world(cfg, placeholder_volatility, placeholder_regimes)      # skeleton: placeholders only
print("SKELETON (placeholders): n=%d  treated share=%.2f  exposed events=%d" % (len(sk["Y"]), sk["D"].mean(), sk["exposed"].sum()))
# the skeleton must run on its own and recover the known effect (single dataset, informal)
rows, _ = run_dml(sk, seed=3); print("  DML tau_hat (random/naive) = %.3f  (true %.1f)" % (rows[0]["tau"], cfg.tau))

# where each mechanism enters: switching the plug-ins changes ONLY that component
real = build_world(cfg, simulate_volatility, placeholder_regimes)
print("  vol plugged in: sigma varies over time:", bool(real["sig"].std(1).mean() > 1e-6), "| U still zero:", bool(np.all(real["U_t"] == 0)))
same_X = np.array_equal(sk["X"], real["X"]) and np.array_equal(sk["t0"], real["t0"]) and np.array_equal(sk["D"], real["D"])
print("  covariates, dates, treatment unchanged by the swap:", same_X)

# Week 2: v0 == skeleton with both real modules
c2 = Config(seed=7, density=0.5, n_regimes=4)
a = simulate_dgp(c2); b = build_world(c2, simulate_volatility, simulate_regimes)
print("v0 identical to skeleton+real modules:", all(np.array_equal(a[k], b[k]) for k in ["Y", "D", "X", "cluster"]))
