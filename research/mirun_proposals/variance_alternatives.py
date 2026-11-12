"""PROPOSALS ONLY (not the primary estimator; nothing here is approved or used by the production pipeline).

Alternative standard-error / critical-value pairs computed from the SAME residualized scores as
research.week2_completion.dml.estimate. The existing estimator is reproduced exactly as "existing_cr0_normal"
so every alternative is evaluated side by side with it. Each alternative states the assumption it adds.

  existing_cr0_normal : overlap sandwich psi'A psi, normal quantile (the repo estimator).
  cr1_all_normal      : x G_all/(G_all-1), G_all = regime clusters + singleton events (standard CR1 with one
                        regressor, so the (N-1)/(N-k) factor is 1). Expected to be ~1.00x when most events are
                        singletons. Assumes dependence is regime-only.
  cr0_t               : existing SE with t(G_reg-1) critical value, G_reg = distinct regimes touched. Assumes the
                        few-cluster pivot is approximately t with G_reg-1 df (heuristic; not a theorem here).
  cr1reg_t            : clustered part scaled by G_reg/(G_reg-1) (singleton part unscaled), t(G_reg-1) critical value.
  hc3_cr0_normal      : scores divided by (1-h_i), h_i = Dt_i^2/J (leverage-adjusted), overlap structure, normal.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm, t as student_t

from research.week2_completion.dml import _multiway_meat


def decompose(psi, memberships):
    psi = np.asarray(psi, float)
    total, _ = _multiway_meat(psi, memberships)
    unexposed = np.array([not m for m in memberships])
    single = float(np.sum(psi[unexposed] ** 2))
    regimes = {r for m in memberships for r in m}
    return {"meat_total": float(total), "meat_singletons": single, "meat_clustered": float(total) - single,
            "G_reg": len(regimes), "G_all": len(regimes) + int(unexposed.sum())}


def alternatives(Yt, Dt, memberships, alpha=.05):
    """Return {name: {"se", "crit"}} plus tau and diagnostics. Undefined variants are None (never imputed)."""
    Yt, Dt = np.asarray(Yt, float), np.asarray(Dt, float)
    J = float(np.sum(Dt ** 2))
    tau = float(np.sum(Dt * Yt) / J)
    psi = Dt * (Yt - tau * Dt)
    d = decompose(psi, memberships)
    z = float(norm.ppf(1 - alpha / 2))

    def pack(meat, crit):
        return {"se": float(np.sqrt(meat) / J) if meat > 0 else None, "crit": crit}

    out = {"existing_cr0_normal": pack(d["meat_total"], z),
           "cr1_all_normal": pack(d["meat_total"] * d["G_all"] / (d["G_all"] - 1), z) if d["G_all"] > 1 else None}
    if d["G_reg"] >= 2:
        tcrit = float(student_t.ppf(1 - alpha / 2, d["G_reg"] - 1))
        out["cr0_t"] = pack(d["meat_total"], tcrit)
        out["cr1reg_t"] = pack(d["meat_singletons"] + d["meat_clustered"] * d["G_reg"] / (d["G_reg"] - 1), tcrit)
    else:
        out["cr0_t"] = out["cr1reg_t"] = None
    h = Dt ** 2 / J
    if np.all(h < 1):
        out["hc3_cr0_normal"] = pack(_multiway_meat(psi / (1 - h), memberships)[0], z)
    else:
        out["hc3_cr0_normal"] = None
    out["naive_normal"] = pack(float(np.sum(psi ** 2)), z)
    return {"tau": tau, "J": J, "variants": out, "decomposition": d}
