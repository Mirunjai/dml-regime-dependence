"""Provisional diagnostics for the explicitly identified calendar-time DGP."""
from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from src.infra.reproducibility import save_json_atomic
from .dgp import Config, build_world


def overlap_density(data):
    return float(np.mean(data["exposed"]))


def pair_density(memberships):
    n, pairs = len(memberships), 0
    sets = [set(membership) for membership in memberships]
    for i in range(n):
        for j in range(i + 1, n):
            pairs += bool(sets[i] & sets[j])
    return pairs / (n * (n - 1) / 2) if n > 1 else 0.


def correlation(a, b, *, rank=False):
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return None
    value = float(spearmanr(a, b).statistic if rank else np.corrcoef(a, b)[0, 1])
    return value if np.isfinite(value) else None


def one_seed(seed, density=.5, K=4, gamma=1., persistence=.9, tau=1., *, config=None):
    cfg = replace(config, seed=int(seed)) if config is not None else Config(
        seed=seed, density=density, n_regimes=K, gamma=gamma, persistence=persistence, tau=tau)
    data = build_world(cfg)
    returns = data["sig"] * data["z"]
    return {"seed": int(seed), "gamma": cfg.gamma, "density_setting": cfg.density, "K": cfg.n_regimes,
            "config": asdict(cfg), "realized_overlap_density": overlap_density(data),
            "pair_density": pair_density(data["cluster_memberships"]),
            "mean_r2": float(np.mean(returns * returns)),
            "max_abs_return": float(np.max(np.abs(returns))),
            "n_nan": int(np.isnan(returns).sum()), "n_inf": int(np.isinf(returns).sum()),
            "n_regime_memberships": int(sum(len(m) for m in data["cluster_memberships"])),
            "n_events_multi_regime": int(sum(len(m) > 1 for m in data["cluster_memberships"])),
            "n_exposed": int(data["exposed"].sum()), "treatment_rate": float(data["D"].mean()),
            "corr_D_Uwin": correlation(data["D"], data["U_win"]),
            "corr_sigma_abs_U": correlation(data["sig_event"][data["exposed"]],
                np.abs(data["U_win"][data["exposed"]]), rank=True), "true_tau": cfg.tau,
            "interpretation": "Correlations are descriptive; undefined is not zero or a passed independence check"}


def run_gate2(seeds=range(50), out_path="results/raw/week2_gate2.json", *, config=None, gamma_values=(0., 1.)):
    base = config or Config()
    base.validate()
    seeds = list(seeds)
    if not seeds:
        raise ValueError("Diagnostic seeds must not be empty")
    records = [one_seed(int(seed), config=base) for seed in seeds]
    gamma_pairs = []
    for seed in seeds:
        worlds = [(float(gamma), build_world(replace(base, seed=int(seed), gamma=float(gamma))))
                  for gamma in gamma_values]
        reference = worlds[0][1]
        gamma_pairs.append({"seed": int(seed), "same_X": all(np.array_equal(reference["X"], data["X"]) for _, data in worlds),
            "same_dates": all(np.array_equal(reference["t0"], data["t0"]) for _, data in worlds),
            "same_U": all(np.array_equal(reference["U_t"], data["U_t"]) for _, data in worlds),
            "treatment_rates": [{"gamma": gamma, "rate": float(data["D"].mean())} for gamma, data in worlds]})
    result = {"schema_version": 2, "purpose": "diagnostic evidence; not a Gate 2 pass decision",
              "base_config": asdict(base), "seeds": [int(seed) for seed in seeds],
              "default_gamma_records": records, "gamma_ablation": gamma_pairs,
              "summary": {"mean_overlap": float(np.mean([row["realized_overlap_density"] for row in records])),
                          "mean_pair_density": float(np.mean([row["pair_density"] for row in records])),
                          "mean_r2": float(np.mean([row["mean_r2"] for row in records])),
                          "events_touching_multiple_regimes": int(sum(row["n_events_multi_regime"] for row in records))}}
    save_json_atomic(out_path, result)
    return result
