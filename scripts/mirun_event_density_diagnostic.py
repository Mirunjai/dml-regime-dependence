"""Reproducibly audit event-level density induced by the calendar-regime DGP."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
from research.week2_completion.dgp import spawn_rngs, simulate_calendar_regimes

def event_memberships(*, seed: int, n: int, T: int, H: int, density: float,
                      n_regimes: int, sd_shock: float = 0.4):
    """Reproduce build_world's date/window-to-regime membership mapping."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(n) is not int or n < 2 or type(T) is not int or T < 2:
        raise ValueError("n and T must be integers with n>=2 and T>=2")
    if type(H) is not int or not 1 <= H <= T:
        raise ValueError("H must be an integer in [1,T]")
    if type(n_regimes) is not int or n_regimes < 0:
        raise ValueError("n_regimes must be a nonnegative integer")
    rng = spawn_rngs(seed)
    t0 = rng["dates"].integers(0, T - H + 1, size=n)
    regime_id, _, _ = simulate_calendar_regimes(
        T, density, n_regimes, sd_shock, rng["layout"], rng["shock"])
    windows = regime_id[t0[:, None] + np.arange(H)[None, :]]
    return [tuple(int(k) for k in np.unique(row) if k >= 0) for row in windows]

def summarize_memberships(memberships, n_regimes: int):
    """Report event exposure, any-shared-regime pair density and multiplicity."""
    n = len(memberships)
    if n < 2 or n_regimes < 0:
        raise ValueError("Need at least two events and nonnegative n_regimes")
    matrix = np.zeros((n, n_regimes), dtype=np.uint8)
    for i, membership in enumerate(memberships):
        for regime in membership:
            if type(regime) is not int or not 0 <= regime < n_regimes:
                raise ValueError("Membership contains an invalid regime ID")
            matrix[i, regime] = 1
    counts = matrix.sum(axis=1)
    shared = (matrix @ matrix.T) > 0
    upper = shared[np.triu_indices(n, k=1)]
    return {
        "n_events": int(n),
        "realized_regime_count": int(np.count_nonzero(matrix.sum(axis=0))),
        "exposed_event_share": float(np.mean(counts > 0)),
        "shared_regime_pair_density": float(np.mean(upper)),
        "multi_regime_event_share": float(np.mean(counts > 1)),
        "mean_regimes_per_event": float(np.mean(counts)),
        "membership_count_distribution": {
            str(int(k)): int(np.sum(counts == k)) for k in np.unique(counts)
        },
    }

def summarize_condition(*, seeds, n, T, H, density, n_regimes):
    metrics = [summarize_memberships(
        event_memberships(seed=int(seed), n=n, T=T, H=H, density=density,
                          n_regimes=n_regimes), n_regimes)
        for seed in seeds]
    keys = ("exposed_event_share", "shared_regime_pair_density",
            "multi_regime_event_share", "mean_regimes_per_event")
    out = {"n_regimes": n_regimes, "calendar_density": float(density),
           "replications": len(metrics)}
    for key in keys:
        vals = np.asarray([m[key] for m in metrics], dtype=float)
        out[key] = {"mean": float(vals.mean()),
                    "sd_between_worlds": float(vals.std(ddof=1)) if len(vals)>1 else 0.0,
                    "mcse_mean": float(vals.std(ddof=1)/np.sqrt(len(vals))) if len(vals)>1 else 0.0}
    out["realized_regime_count_min"] = min(m["realized_regime_count"] for m in metrics)
    out["realized_regime_count_max"] = max(m["realized_regime_count"] for m in metrics)
    return out

def calibrate_calendar_density(*, target_exposure, candidates, seeds, n, T, H, n_regimes):
    rows = [summarize_condition(seeds=seeds, n=n, T=T, H=H,
                                density=float(d), n_regimes=n_regimes)
            for d in candidates]
    return min(rows, key=lambda r: abs(r["exposed_event_share"]["mean"]-target_exposure))

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=400)
    p.add_argument("--T", type=int, default=260)
    p.add_argument("--H", type=int, default=5)
    p.add_argument("--regimes", type=int, nargs="+", default=[4,16])
    p.add_argument("--densities", type=float, nargs="+", default=[.25,.50,.75])
    p.add_argument("--reps", type=int, default=100)
    p.add_argument("--seed-start", type=int, default=91000)
    p.add_argument("--calibrate-targets", type=float, nargs="*", default=[])
    p.add_argument("--grid-step", type=float, default=.025)
    p.add_argument("--out", type=Path, default=Path("results/tables/mirun_event_density_audit.json"))
    a = p.parse_args(argv)
    if a.reps < 2 or a.seed_start < 0 or not 0 < a.grid_step <= 1:
        p.error("Require reps>=2, seed-start>=0 and grid-step in (0,1]")
    seeds = list(range(a.seed_start, a.seed_start+a.reps))
    conditions = [summarize_condition(seeds=seeds,n=a.n,T=a.T,H=a.H,
                    density=d,n_regimes=k) for k in a.regimes for d in a.densities]
    calibrations=[]
    if a.calibrate_targets:
        candidates=np.arange(a.grid_step,1.000001,a.grid_step)
        if candidates[-1] < 1: candidates=np.append(candidates,1.)
        for k in a.regimes:
            for target in a.calibrate_targets:
                if not 0 <= target <= 1: p.error("Targets must be in [0,1]")
                chosen=calibrate_calendar_density(target_exposure=target,candidates=candidates,
                    seeds=seeds,n=a.n,T=a.T,H=a.H,n_regimes=k)
                calibrations.append({"n_regimes":k,"target_exposed_event_share":target,
                    "selected_calendar_density":chosen["calendar_density"],
                    "selected_condition_summary":chosen})
    payload={"schema":"event_density_audit_v1","status":"diagnostic_not_gate_approval",
        "dgp_rng_contract":"spawn_rngs + simulate_calendar_regimes + build_world event-window mapping",
        "n":a.n,"T":a.T,"H":a.H,"seed_start":a.seed_start,"replications":a.reps,
        "conditions":conditions,"matched_exposure_calibration":calibrations}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    csv_path=a.out.with_suffix(".csv")
    fields=["n_regimes","calendar_density","replications",
      "exposed_event_share_mean","exposed_event_share_mcse",
      "shared_regime_pair_density_mean","shared_regime_pair_density_mcse",
      "multi_regime_event_share_mean","multi_regime_event_share_mcse",
      "mean_regimes_per_event_mean"]
    with csv_path.open("w",newline="",encoding="utf-8") as stream:
        w=csv.DictWriter(stream,fieldnames=fields); w.writeheader()
        for r in conditions:
            w.writerow({"n_regimes":r["n_regimes"],"calendar_density":r["calendar_density"],
              "replications":r["replications"],
              "exposed_event_share_mean":r["exposed_event_share"]["mean"],
              "exposed_event_share_mcse":r["exposed_event_share"]["mcse_mean"],
              "shared_regime_pair_density_mean":r["shared_regime_pair_density"]["mean"],
              "shared_regime_pair_density_mcse":r["shared_regime_pair_density"]["mcse_mean"],
              "multi_regime_event_share_mean":r["multi_regime_event_share"]["mean"],
              "multi_regime_event_share_mcse":r["multi_regime_event_share"]["mcse_mean"],
              "mean_regimes_per_event_mean":r["mean_regimes_per_event"]["mean"]})
    print(json.dumps({"json":str(a.out),"csv":str(csv_path),
                      "conditions":len(conditions),"calibrations":len(calibrations)},indent=2))

if __name__ == "__main__":
    main()
