"""DIAGNOSTIC nuisance residuals for mechanism studies (not estimators).

generic_crossfit: mirrors research.week2_completion.dml.crossfit (same seeds seed+k / seed+100+k) but takes a learner
factory, so a second learner can be compared. oracle_residuals uses simulation TRUTH (g(X) and an approximate
E[D|X]) and exists only to separate nuisance-estimation error from variance-estimator error.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

from research.week2_completion import dml as _dml


def generic_crossfit(Y, D, X, fold, n_folds, seed, learner):
    n = len(Y)
    my, md = np.empty(n), np.empty(n)
    for k in range(n_folds):
        train, test = fold != k, fold == k
        my[test] = learner(seed + k).fit(X[train], Y[train]).predict(X[test])
        md[test] = learner(seed + 100 + k).fit(X[train], D[train]).predict(X[test])
    return Y - my, D - md


def rf_learner(seed):
    return _dml._learner(seed)


def gbr_learner(seed):
    return GradientBoostingRegressor(n_estimators=100, max_depth=2, learning_rate=.1, subsample=.8, random_state=seed)


def oracle_residuals(data, cfg, nodes=40):
    """Truth-based residuals. E[D|X] = P(unexposed)*sigma(a) + P(exposed)*E_v sigma(a+gamma*v), v~N(0,1)
    (exact when each event has at most one regime; APPROXIMATE under multi-membership)."""
    X, D, Y = data["X"], data["D"], data["Y"]
    a = -.5 + .5 * X[:, 0] + .3 * X[:, 1]
    xs, ws = np.polynomial.hermite_e.hermegauss(nodes)
    ws = ws / ws.sum()
    sig = lambda u: 1 / (1 + np.exp(-u))
    expo = sig(a[:, None] + cfg.gamma * xs[None, :]) @ ws
    pi = float(np.mean(data["exposed"]))
    m = (1 - pi) * sig(a) + pi * expo
    g = .5 * X[:, 0] + .3 * X[:, 1] ** 2 + .2 * X[:, 0] * X[:, 2]
    return Y - g - cfg.tau * m, D - m
