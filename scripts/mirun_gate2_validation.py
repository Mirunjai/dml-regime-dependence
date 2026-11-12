"""Source-faithful Gate 2 structural and independence diagnostic for Project A.

Uses the repository's integrated build_world() implementation. No DML coverage
or production inference is run here. The diagnostic thresholds for control
checks are calibrated on an independent null seed set and evaluated on a
separate validation seed set.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from research.week2_completion.dgp import Config, build_world

N, T, H = 400, 260, 5
REGIMES = (4, 16)
BASE_DENSITIES = (0.25, 0.50, 0.75)
DGP_GIT_BLOB_SHA = "47e24f88c4724be4708271931f03492eb968f741"
MATCHED = {
    0.32: {4: 0.250, 16: 0.075},
    0.56: {4: 0.500, 16: 0.300},
    0.82: {4: 0.750, 16: 0.575},
}


def verify_source_hash():
    dgp_path = Path(__file__).resolve().parents[1] / "research" / "week2_completion" / "dgp.py"
    data = dgp_path.read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if git_blob != DGP_GIT_BLOB_SHA:
        raise RuntimeError(
            f"DGP source changed: expected Git blob {DGP_GIT_BLOB_SHA}, got {git_blob}"
        )
    return git_blob


def event_metrics(world):
    memberships = world["cluster_memberships"]
    n = len(memberships)
    k = world["cfg"].n_regimes
    mat = np.zeros((n, k), dtype=np.int64)
    for i, mem in enumerate(memberships):
        for r in mem:
            mat[i, r] = 1
    counts = mat.sum(axis=1)
    shared = (mat @ mat.T) > 0
    pair = shared[np.triu_indices(n, 1)]
    exposed = counts > 0
    exp_pairs = exposed[:, None] & exposed[None, :]
    exp_pair_mask = exp_pairs[np.triu_indices(n, 1)]
    cond_pair = float(pair[exp_pair_mask].mean()) if exp_pair_mask.any() else 0.0
    regime_counts = mat.sum(axis=0).astype(float)
    nonzero = regime_counts[regime_counts > 0]
    effective_k = float(regime_counts.sum() ** 2 / np.sum(regime_counts ** 2)) if len(nonzero) else 0.0
    return {
        "exposed_event_share": float(exposed.mean()),
        "shared_pair_density": float(pair.mean()),
        "conditional_shared_pair_density_exposed": cond_pair,
        "multi_regime_event_share": float(np.mean(counts > 1)),
        "mean_regimes_per_event": float(counts.mean()),
        "effective_regimes_inverse_hhi": effective_k,
        "membership_count_distribution": {
            str(i): int(np.sum(counts == i)) for i in range(k + 1) if np.any(counts == i)
        },
    }


def summarize_values(values):
    a = np.asarray(values, dtype=float)
    return {"mean": float(a.mean()), "sd_between_worlds": float(a.std(ddof=1)),
            "mcse_mean": float(a.std(ddof=1) / np.sqrt(len(a))),
            "n_worlds": int(len(a))}


def run_grid(seeds):
    rows = []
    for k in REGIMES:
        for d in BASE_DENSITIES:
            metrics = []
            for seed in seeds:
                w = build_world(Config(n=N, T=T, H=H, density=d, n_regimes=k, seed=int(seed)))
                metrics.append(event_metrics(w))
            rows.append({"K": k, "calendar_active_fraction": d,
                         **{key: summarize_values([m[key] for m in metrics])
                            for key in ("exposed_event_share", "shared_pair_density",
                                        "conditional_shared_pair_density_exposed",
                                        "multi_regime_event_share", "mean_regimes_per_event",
                                        "effective_regimes_inverse_hhi")}})
    return rows


def run_matched(seeds):
    rows = []
    for target, by_k in MATCHED.items():
        summaries = {}
        raw = {}
        for k, d in by_k.items():
            metrics = []
            for seed in seeds:
                w = build_world(Config(n=N, T=T, H=H, density=d, n_regimes=k, seed=int(seed)))
                metrics.append(event_metrics(w))
            raw[k] = metrics
            summaries[k] = {key: summarize_values([m[key] for m in metrics])
                             for key in ("exposed_event_share", "shared_pair_density",
                                         "multi_regime_event_share", "effective_regimes_inverse_hhi")}
        # Same seed IDs are paired across K; report paired differences rather than
        # comparing two independent MCSEs as if the samples were unrelated.
        paired = {}
        for key in ("exposed_event_share", "shared_pair_density", "multi_regime_event_share",
                    "effective_regimes_inverse_hhi"):
            diffs = [raw[4][i][key] - raw[16][i][key] for i in range(len(seeds))]
            paired[key + "_K4_minus_K16"] = summarize_values(diffs)
        rows.append({"target_exposed_event_share": target,
                     "calendar_fraction_by_K": {str(k): d for k, d in by_k.items()},
                     "by_K": {str(k): summaries[k] for k in (4, 16)},
                     "paired_differences": paired})
    return rows


def corr(x, y):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    if x.shape != y.shape or x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Correlation requires aligned, finite vectors of length >=2")
    if np.std(x) <= 1e-12 or np.std(y) <= 1e-12:
        raise ValueError("Undefined correlation for a constant vector")
    return float(np.corrcoef(x, y)[0, 1])


def independence_metrics(world):
    # Predeclared to match the intervention terms in build_world(): the
    # volatility break multiplies sigma by |U_t|; the treatment break adds U_win
    # to the treatment logit.
    sigma = np.asarray(world["sig_event"], dtype=float)
    if not np.isfinite(sigma).all() or np.any(sigma <= 0):
        raise ValueError("Conditional standard deviations must be finite and positive; no clipping")
    vol_r = corr(np.log(sigma), np.abs(world["U_win"]))
    treat_r = corr(world["D"], world["U_win"])
    return {"volatility_abs_shock_corr": vol_r,
            "treatment_signed_shock_corr": treat_r}


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054):
    """Two-sided Wilson score interval for a binomial rate."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("Require 0 <= successes <= trials and trials > 0")
    phat = successes / trials
    denom = 1.0 + z * z / trials
    center = (phat + z * z / (2.0 * trials)) / denom
    half = (z * np.sqrt(phat * (1 - phat) / trials + z * z / (4.0 * trials * trials))) / denom
    return [float(max(0.0, center - half)), float(min(1.0, center + half))]


def rate_summary(values, threshold):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or not np.isfinite(threshold) or threshold < 0:
        raise ValueError("Detection rates require nonempty finite values and a finite nonnegative threshold")
    successes = int(np.sum(np.abs(values) > threshold))
    n = int(len(values))
    return {"rate": successes / n, "successes": successes, "trials": n,
            "wilson_95": wilson_interval(successes, n)}


def run_controls(calibration_seeds, validation_seeds):
    calibration_seeds, validation_seeds = list(calibration_seeds), list(validation_seeds)
    for seeds in (calibration_seeds, validation_seeds):
        if len(seeds) < 2 or len(set(seeds)) != len(seeds) or any(type(s) is not int or s < 0 for s in seeds):
            raise ValueError("Each control seed set must contain >=2 distinct nonnegative integers")
    if set(calibration_seeds) & set(validation_seeds):
        raise ValueError("Calibration and validation seeds must be disjoint")
    out = {}
    for k, d in ((4, 0.75), (16, 0.575)):
        null_cal = {"volatility_abs_shock_corr": [], "treatment_signed_shock_corr": []}
        null_val = {"volatility_abs_shock_corr": [], "treatment_signed_shock_corr": []}
        vol_pos = {"volatility_abs_shock_corr": [], "treatment_signed_shock_corr": []}
        treat_pos = {"volatility_abs_shock_corr": [], "treatment_signed_shock_corr": []}
        for seed in calibration_seeds:
            w = build_world(Config(n=N, T=T, H=H, density=d, n_regimes=k, seed=int(seed)))
            m = independence_metrics(w)
            for key in null_cal: null_cal[key].append(m[key])
        thresholds = {key: float(np.quantile(np.abs(vals), .95)) for key, vals in null_cal.items()}
        for seed in validation_seeds:
            base = build_world(Config(n=N, T=T, H=H, density=d, n_regimes=k, seed=int(seed)))
            vbreak = build_world(Config(n=N, T=T, H=H, density=d, n_regimes=k, seed=int(seed),
                                        break_vol_independence=True))
            tbreak = build_world(Config(n=N, T=T, H=H, density=d, n_regimes=k, seed=int(seed),
                                        break_treat_independence=True))
            for key, value in independence_metrics(base).items(): null_val[key].append(value)
            for key, value in independence_metrics(vbreak).items(): vol_pos[key].append(value)
            for key, value in independence_metrics(tbreak).items(): treat_pos[key].append(value)
        evaluations = {}
        for key in thresholds:
            thr = thresholds[key]
            false_pos = rate_summary(null_val[key], thr)
            vol_power = rate_summary(vol_pos[key], thr)
            treat_power = rate_summary(treat_pos[key], thr)
            evaluations[key] = {
                "null_calibration_abs_corr_q95": thr,
                "null_validation_false_positive": false_pos,
                "volatility_break_detection": vol_power,
                "treatment_break_detection": treat_power,
                "null_calibration_corr": summarize_values(null_cal[key]),
                "null_validation_corr": summarize_values(null_val[key]),
                "volatility_break_corr": summarize_values(vol_pos[key]),
                "treatment_break_corr": summarize_values(treat_pos[key]),
            }
        out[str(k)] = {"calendar_fraction": d, "target_exposed_event_share": 0.82,
                       "calibration_worlds": len(calibration_seeds),
                       "validation_worlds": len(validation_seeds),
                       "evaluations": evaluations}
    return out


def run_known_truth(seeds):
    rows = []
    for seed in seeds:
        common = dict(n=N, T=T, H=H, density=0.0, n_regimes=0,
                      sd_shock=0.0, sd_factor=0.0, gamma=0.0, seed=int(seed))
        y1 = build_world(Config(**common, tau=1.0))
        y0 = build_world(Config(**common, tau=0.0))
        error = float(np.max(np.abs((y1["Y"] - y0["Y"]) - y1["D"])))
        rows.append({"seed": int(seed), "max_abs_tau_contrast_error": error,
                     "treated_share": float(y1["D"].mean())})
    return {
        "control": "no_regime_shock_no_common_factor_tau_1_vs_tau_0_same_world",
        "worlds": len(rows),
        "all_exact_truth_checks_pass": bool(all(r["max_abs_tau_contrast_error"] <= 1e-12 for r in rows)),
        "maximum_absolute_error": max(r["max_abs_tau_contrast_error"] for r in rows),
        "mean_treated_share": float(np.mean([r["treated_share"] for r in rows])),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("grid", "matched", "controls", "truth", "all"), default="all")
    parser.add_argument("--out", default="results/tables/mirun_gate2_validation.json")
    args = parser.parse_args()
    source_sha = verify_source_hash()
    phases = {}
    if args.phase in ("grid", "all"):
        phases["grid"] = run_grid(range(10000, 10100))
    if args.phase in ("matched", "all"):
        phases["matched_exposure_h4"] = run_matched(range(11000, 11200))
    if args.phase in ("controls", "all"):
        phases["independence_controls"] = run_controls(range(12000, 12100), range(13000, 13100))
    if args.phase in ("truth", "all"):
        phases["known_truth_control"] = run_known_truth(range(14000, 14100))
    result = {
        "schema": "project_a_gate2_validation_v1",
        "status": "EXPLORATORY_DIAGNOSTIC_NOT_GATE_APPROVAL",
        "generator": "research.week2_completion.dgp.build_world",
        "dgp_git_blob_sha": source_sha,
        "n": N, "T": T, "H": H,
        "phase": args.phase,
        "seed_contract": {
            "grid": [10000, 10100], "matched": [11000, 11200],
            "control_calibration": [12000, 12100], "control_validation": [13000, 13100],
            "known_truth": [14000, 14100]
        },
        **phases,
    }
    path = Path(args.out); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(path), "phase": args.phase,
                      "sections": list(phases), "source_sha": source_sha}, indent=2))

if __name__ == "__main__":
    main()
