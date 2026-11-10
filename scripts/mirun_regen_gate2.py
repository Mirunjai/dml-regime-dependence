"""EXPLORATORY Gate 2 diagnostic regeneration with explicit config, seeds and provenance. NOT a Gate 2 decision.
Calendar DGP (research.week2_completion), unmodified. Never overwrites existing output.
  python -m scripts.mirun_regen_gate2 --raw results/raw/mirun_session4/gate2_regen.json --summary results/tables/mirun_gate2_regen_summary.json
"""
import argparse, json, platform, sys, time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from research.week2_completion.dgp import Config
from research.week2_completion.validation import one_seed, run_gate2
from src.infra.reproducibility import config_hash, git_state, software_versions

SEEDS = list(range(60000, 60100))

def garch_table(alpha=.10, sigma2_bar=1.):
    rows = []
    for rho in (.5, .8, .9, .95, .98, .99):
        beta = rho - alpha; m4 = 3 * alpha**2 + 2 * alpha * beta + beta**2
        kurt = 3 * (1 - rho**2) / (1 - rho**2 - 2 * alpha**2) if m4 < 1 else None
        rows.append({"persistence": rho, "alpha": alpha, "beta": round(beta, 10), "omega": (1 - rho) * sigma2_bar,
                     "unconditional_variance": sigma2_bar, "fourth_moment_condition_value": m4,
                     "fourth_moment_finite": bool(m4 < 1), "gaussian_kurtosis": kurt})
    return rows

def control(cfg, field, key):
    from dataclasses import replace
    vals = np.array([one_seed(s, config=replace(cfg, **{field: True}))[key] for s in SEEDS], float)
    return vals

def tstat(v):
    v = v[np.isfinite(v)]
    return {"n": int(len(v)), "mean": float(v.mean()), "sd": float(v.std(ddof=1)), "t": float(v.mean() / (v.std(ddof=1) / np.sqrt(len(v))))}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", type=Path, required=True); ap.add_argument("--summary", type=Path, required=True)
    a = ap.parse_args()
    for p in (a.raw, a.summary):
        if p.exists(): ap.error(f"{p} exists; refusing to overwrite")
    cfg = Config(); t0 = time.time()
    res = run_gate2(SEEDS, a.raw, config=cfg, gamma_values=(0., 1.))
    prod = res["default_gamma_records"]
    arr = lambda k: np.array([r[k] if r[k] is not None else np.nan for r in prod], float)
    summary = {
        "purpose": "exploratory Gate 2 diagnostic regeneration; not an approval; thresholds not pre-declared by team",
        "provenance": {"command": " ".join(sys.argv), "git": git_state(), "software": software_versions(), "python": platform.python_version(),
                       "config": asdict(cfg), "config_hash": config_hash(asdict(cfg)), "seeds": [SEEDS[0], SEEDS[-1]], "n_seeds": len(SEEDS),
                       "raw_file": str(a.raw), "wall_seconds": time.time() - t0, "schema_version": res["schema_version"]},
        "garch_theory": garch_table(cfg.garch_alpha, cfg.sigma2_bar),
        "empirical": {"mean_overlap_density": float(np.mean(arr("realized_overlap_density"))),
                      "mean_pair_density": float(np.mean(arr("pair_density"))),
                      "mean_exposed_share": float(np.mean(arr("n_exposed")) / cfg.n),
                      "multi_regime_events_total": int(sum(r["n_events_multi_regime"] for r in prod)),
                      "worlds_with_multi_regime": int(sum(r["n_events_multi_regime"] > 0 for r in prod)),
                      "mean_r2_of_unit_variance_returns": float(np.mean(arr("mean_r2"))),
                      "max_abs_return_overall": float(np.max(arr("max_abs_return"))),
                      "n_nan_total": int(arr("n_nan").sum()), "n_inf_total": int(arr("n_inf").sum()),
                      "same_X_dates_U_across_gamma_all_seeds": bool(all(g["same_X"] and g["same_dates"] and g["same_U"] for g in res["gamma_ablation"]))},
        "independence": {
            "production_corr_D_Uwin": tstat(arr("corr_D_Uwin")),
            "production_corr_sigma_abs_U": tstat(arr("corr_sigma_abs_U")),
            "positive_control_treat_dependence_corr_D_Uwin": tstat(control(cfg, "break_treat_independence", "corr_D_Uwin")),
            "positive_control_vol_dependence_corr_sigma_abs_U": tstat(control(cfg, "break_vol_independence", "corr_sigma_abs_U")),
            "note": "Non-rejection in production does not prove independence; controls show the diagnostics can detect injected dependence"}}
    a.summary.write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary["empirical"][k] for k in summary["empirical"]}, indent=0)[:900]); print(json.dumps(summary["independence"], indent=0)[:1200])

if __name__ == "__main__":
    main()
