"""EXPLORATORY. (a) Power of each SE variant = rejection rate of H0: tau=0 when tau=1 (from raw undercoverage-study records;
NOT size-adjusted, so conservative/anti-conservative variants are not compared on equal footing).
(b) Effective regime-cluster count G_eff=(sum s)^2/sum s^2 from regime sizes (events per regime) in the same worlds (seeds 30000+).
Calendar DGP unmodified; build_world only."""
import json, sys
from dataclasses import replace
from pathlib import Path
import numpy as np
from research.week2_completion.dgp import Config, build_world

def power(d):
    recs = [json.loads(f.read_text()) for f in sorted(Path(d).glob("rep_*.json"))]
    out = {}
    for route in [k for k in recs[0] if isinstance(recs[0][k], dict) and "tau" in recs[0][k]]:
        row = {}
        for v in recs[0][route]["variants"]:
            rej = [abs(r[route]["tau"]) > r[route]["variants"][v]["crit"] * r[route]["variants"][v]["se"]
                   for r in recs if r[route]["variants"][v] and r[route]["variants"][v]["se"]]
            p = float(np.mean(rej)); row[v] = {"power": p, "mcse": float(np.sqrt(p * (1 - p) / len(rej))), "n": len(rej)}
        out[route] = row
    return out

def geff(K, n, reps=200, seed0=30000):
    rows = []
    for r in range(reps):
        d = build_world(replace(Config(), n=n, n_regimes=K, density=.5, gamma=1., tau=1., seed=seed0 + r))
        sizes = np.bincount([k for m in d["cluster_memberships"] for k in m], minlength=K).astype(float)
        sizes = sizes[sizes > 0]
        rows.append({"G_nonempty": len(sizes), "G_eff": float(sizes.sum() ** 2 / np.sum(sizes ** 2)),
                     "largest_share_of_clustered": float(sizes.max() / sizes.sum())})
    return {k: float(np.mean([x[k] for x in rows])) for k in rows[0]} | {"reps": reps}

if __name__ == "__main__":
    res = {"purpose": "exploratory power and effective cluster counts", "power_tau1": {}, "effective_clusters": {}}
    for K, n in ((4, 400), (4, 1000), (4, 2500), (16, 400), (16, 1000), (16, 2500)):
        res["power_tau1"][f"K{K}_n{n}"] = power(f"results/raw/mirun_session4/uc_K{K}_n{n}")
        res["effective_clusters"][f"K{K}_n{n}"] = geff(K, n)
    Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
    for k in res["power_tau1"]:
        r = res["power_tau1"][k]["rf_random"]; g = res["effective_clusters"][k]
        print(k, "G_eff %.2f/%d largest %.2f" % (g["G_eff"], g["G_nonempty"], g["largest_share_of_clustered"]),
              {v: round(r[v]["power"], 2) for v in ("naive_normal", "existing_cr0_normal", "cr0_t", "cr1reg_t")})
