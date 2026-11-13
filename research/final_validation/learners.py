"""Two predeclared nuisance families; tuning stays inside outer training data."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from research.week2_completion.dml import _learner, crossfit


def residualize(world, fold, n_folds, seed, *, learner):
    """Fit only observed X/Y/D; no simulation truth or latent shocks are inputs."""
    Y, D, X = (world[k] for k in ("Y","D","X"))
    if learner == "legacy_rf40":
        return crossfit(Y,D,X,fold,n_folds,seed)
    if learner != "quadratic_ridge_logit":
        raise ValueError("Unknown predeclared learner")
    if fold.shape != (len(Y),) or set(np.unique(fold)) != set(range(n_folds)):
        raise ValueError("Every outer fold must be represented")
    my, md = np.empty(len(Y)), np.empty(len(D))
    for k in range(n_folds):
        train, test = fold != k, fold == k
        if len(np.unique(D[train])) < 2:
            raise ValueError("Training partition has only one treatment class")
        # All scaler, polynomial and GCV fits see outer-training observations only.
        outcome = make_pipeline(StandardScaler(), PolynomialFeatures(2,include_bias=False),
                                RidgeCV(alphas=np.array([.1,1.,10.])))
        treatment = make_pipeline(StandardScaler(),
                                 LogisticRegression(C=1.,max_iter=1000,random_state=int(seed+100+k)))
        my[test] = outcome.fit(X[train],Y[train]).predict(X[test])
        md[test] = treatment.fit(X[train],D[train]).predict_proba(X[test])[:,1]
    if not np.isfinite(my).all() or not np.isfinite(md).all():
        raise ValueError("Nonfinite out-of-fold predictions")
    return Y-my, D-md
