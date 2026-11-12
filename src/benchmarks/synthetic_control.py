"""Synthetic Control estimator helper with explicit donor-panel inputs.

The function does not choose a donor pool, predictors, periods, placebos, or
inference method. Freeze those choices before applying it to project data.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def fit_synthetic_control(
    treated_pre: Sequence[float],
    donor_pre: np.ndarray,
    treated_post: Sequence[float],
    donor_post: np.ndarray,
    *,
    donor_ids: Sequence[str],
) -> dict[str, object]:
    """Fit nonnegative, sum-to-one donor weights by pre-period outcome fit.

    ``donor_pre`` and ``donor_post`` are time-by-donor matrices with identical
    donor-column order. ``treated_pre`` and ``treated_post`` are the treated
    unit's adjusted-return or outcome series on the corresponding dates.
    Inputs must already be aligned to the frozen design's dates. Missing values
    are rejected rather than filled. The pre-period loss is mean squared error.
    """
    y_pre = np.asarray(treated_pre, dtype=float)
    y_post = np.asarray(treated_post, dtype=float)
    y0_pre = np.asarray(donor_pre, dtype=float)
    y0_post = np.asarray(donor_post, dtype=float)
    ids = list(donor_ids)
    if y_pre.ndim != 1 or y_post.ndim != 1:
        raise ValueError("Treated pre/post outcomes must be one-dimensional")
    if y0_pre.ndim != 2 or y0_post.ndim != 2:
        raise ValueError("Donor pre/post outcomes must be time-by-donor matrices")
    if y0_pre.shape[0] != len(y_pre) or y0_post.shape[0] != len(y_post):
        raise ValueError("Treated and donor panels must have matching time dimensions")
    if y0_pre.shape[1] != y0_post.shape[1] or y0_pre.shape[1] != len(ids):
        raise ValueError("Donor count/order must match pre/post panels and donor_ids")
    if y0_pre.shape[1] < 2:
        raise ValueError("At least two donor units are required")
    if not (len(y_pre) and len(y_post)):
        raise ValueError("Pre and post periods must both contain observations")
    arrays = (y_pre, y0_pre, y_post, y0_post)
    if any(not np.isfinite(a).all() for a in arrays):
        raise ValueError("Synthetic Control inputs contain missing or nonfinite values")
    if any(not isinstance(i, str) or not i.strip() for i in ids):
        raise ValueError("donor_ids must be nonempty strings")
    if len(set(ids)) != len(ids):
        raise ValueError("donor_ids must be unique")

    n_donors = y0_pre.shape[1]
    initial = np.full(n_donors, 1.0 / n_donors)

    def objective(weights: np.ndarray) -> float:
        residual = y_pre - y0_pre @ weights
        return float(np.mean(residual**2))

    result = minimize(
        objective,
        initial,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n_donors,
        constraints=[{"type": "eq", "fun": lambda weights: float(weights.sum() - 1.0)}],
        options={"ftol": 1e-12, "maxiter": 10000, "disp": False},
    )
    if not result.success:
        raise RuntimeError(f"Synthetic Control optimization failed: {result.message}")
    weights = np.asarray(result.x, dtype=float)
    if (not np.isfinite(weights).all() or (weights < 0).any() or (weights > 1).any()
            or not np.isclose(weights.sum(), 1., atol=1e-8, rtol=0)):
        raise RuntimeError("Optimizer returned infeasible donor weights")
    synthetic_pre = y0_pre @ weights
    synthetic_post = y0_post @ weights
    pre_gap = y_pre - synthetic_pre
    post_gap = y_post - synthetic_post

    # Donor-pool concentration diagnostics
    largest_donor_weight = float(np.max(weights))
    active_donor_count = int(np.sum(weights > 1e-6))
    effective_donor_count = float(
        1.0 / np.sum(weights**2)
    )
    donor_concentration = float(np.sum(weights**2))

    return {
        "weights": pd.Series(weights, index=ids, name="weight"),
        "synthetic_pre": synthetic_pre,
        "pre_gap": pre_gap,
        "pre_rmspe": float(np.sqrt(np.mean(pre_gap**2))),
        "synthetic_post": synthetic_post,
        "post_gap": post_gap,
        "mean_post_gap": float(np.mean(post_gap)),
        "largest_donor_weight": largest_donor_weight,
        "active_donor_count": active_donor_count,
        "effective_donor_count": effective_donor_count,
        "donor_concentration": donor_concentration,
        "optimizer_message": str(result.message),
    }
