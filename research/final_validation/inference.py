"""Scalar unweighted CR2 with Satterthwaite inference for a PLR score regression.

The second-stage regression is Y_residual ~ 0 + D_residual. A cluster is a
connected regime-membership component; an unexposed event is its own cluster.
Cross-cluster independence is an assumption, not established by this routine.
In particular, shared calendar factors are not covered by regime components.

For working covariance I, CR2's cluster adjustment is (I-H_gg)^(-1/2).
With one regressor it rescales the cluster score by 1/sqrt(1-h_g).
The degrees of freedom are tr(Q)^2/tr(Q^2), calculated from the Gram matrix
of the adjusted, residualized cluster-score directions. This is an independent
scalar derivation of established BRL/CR2, not a new variance estimator.

References: https://doi.org/10.1080/07350015.2016.1247004 and its corrigendum;
official reference API: https://jepusto.github.io/clubSandwich/.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import t

from research.week2_completion.dml import _components


def component_cr2(y_residual, d_residual, memberships, *, alpha=.05):
    """Return CR2 SE/df/CI, retaining undefined information as an exception.

    Truth is deliberately absent from the interface. The working-model
    Satterthwaite approximation does not account for arbitrary nuisance-fitting
    bias or unmodelled dependence between the supplied clusters.
    """
    if np.iscomplexobj(y_residual) or np.iscomplexobj(d_residual):
        raise ValueError("Residuals must be real")
    y, x = np.asarray(y_residual, float), np.asarray(d_residual, float)
    if y.ndim != 1 or x.shape != y.shape or len(x) < 4:
        raise ValueError("Require matching residual vectors with >=4 observations")
    if not np.isfinite(y).all() or not np.isfinite(x).all():
        raise ValueError("Residuals must be finite")
    if isinstance(alpha, (bool, np.bool_)) or not np.isscalar(alpha) or not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be a finite real number in (0,1)")
    labels = _components(memberships)
    if len(labels) != len(x):
        raise ValueError("Membership count must match residuals")
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        information = float(x @ x)
        if information <= np.finfo(float).eps:
            raise ValueError("Residualized treatment has insufficient information")
        theta = float(x @ y / information)
        residual = y - x * theta
        sumsquares = np.bincount(labels, weights=x*x)
        leverage = sumsquares / information
        active = sumsquares > 0
        if active.sum() < 2 or np.any(leverage[active] >= 1):
            raise ValueError("CR2 requires at least two informative independent clusters")
        cluster_scores = np.bincount(labels, weights=x*residual)[active]
        h = leverage[active]
        adjusted_scores = cluster_scores / np.sqrt(1-h)
        variance = float(adjusted_scores @ adjusted_scores / information**2)
        # Off-diagonal Gram entries: -h_g*h_j/sqrt((1-h_g)*(1-h_j)).
        # Computing the small cluster Gram matrix avoids cancellation in a
        # difference of two large sums when one cluster has high leverage.
        gram = -np.outer(h / np.sqrt(1-h), h / np.sqrt(1-h))
        np.fill_diagonal(gram, h)
        df = float(np.trace(gram)**2 / np.sum(gram**2))
        se = float(np.sqrt(variance))
        critical = float(t.ppf(1-alpha/2, df))
        if not np.isfinite([theta,se,df,critical]).all() or se <= 0 or df <= 0:
            raise ValueError("CR2 interval is undefined; no clipping or fallback")
    return {"estimate":theta,"se":se,"df":df,"critical":critical,
            "lower":theta-critical*se,"upper":theta+critical*se,
            "informative_clusters":int(active.sum()),
            "max_cluster_leverage":float(h.max()),
            "score_information_per_observation":information/len(x),
            "method":"component_CR2_Satterthwaite",
            "assumption":"independent regime components; identity working covariance"}
