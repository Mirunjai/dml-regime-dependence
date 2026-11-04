"""DML (partially linear model, Chernozhukov et al.) with 2 fold schemes x 2 variance estimators = 4 cells."""
import time
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from scipy import stats

CELLS = [("random", "naive"), ("random", "robust"), ("grouped", "naive"), ("grouped", "robust")]


def make_folds(scheme, cluster, n_folds, rng):
    n = len(cluster)
    if scheme == "random":
        perm = rng.permutation(n)
        fold = np.empty(n, int); fold[perm] = np.arange(n) % n_folds
        return fold
    # grouped: whole clusters go to one fold (greedy balance, random tie-break)
    uniq, inv = np.unique(cluster, return_inverse=True)
    sizes = np.bincount(inv)
    order = np.lexsort((rng.random(len(uniq)), -sizes))
    load = np.zeros(n_folds); gfold = np.empty(len(uniq), int)
    for g in order:
        f = int(np.argmin(load + 1e-6 * rng.random(n_folds))); gfold[g] = f; load[f] += sizes[g]
    return gfold[inv]


def learner(seed, n_estimators=40):
    return RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=8, max_features=0.5,
                                 n_jobs=1, random_state=seed)


def crossfit(Y, D, X, fold, n_folds, seed):
    mY = np.empty_like(Y); mD = np.empty_like(D)
    for k in range(n_folds):
        tr, te = fold != k, fold == k
        mY[te] = learner(seed + k).fit(X[tr], Y[tr]).predict(X[te])
        mD[te] = learner(seed + 100 + k).fit(X[tr], D[tr]).predict(X[te])
    return Y - mY, D - mD


def estimate(Yt, Dt, cluster, tau_true=None, alpha=0.05):
    """Orthogonal-score estimate + naive (iid) and cluster-robust (CR1 by regime cluster) variance."""
    n = len(Yt); J = np.sum(Dt**2)
    tau = np.sum(Dt * Yt) / J
    psi = Dt * (Yt - tau * Dt)
    se_naive = np.sqrt(np.sum(psi**2) / J**2)
    uniq, inv = np.unique(cluster, return_inverse=True)
    G = len(uniq)
    S = np.bincount(inv, weights=psi)
    se_rob = np.sqrt((G / (G - 1)) * np.sum(S**2) / J**2)
    return tau, se_naive, se_rob, G


def run_dml(data, n_folds=5, seed=0, alpha=0.05):
    """All four cells on one dataset. Returns list of dict rows + runtime per scheme."""
    Y, D, X, cl = data["Y"], data["D"], data["X"], data["cluster"]
    rng = np.random.default_rng(seed)
    z = stats.norm.ppf(1 - alpha / 2)
    rows, rt = [], {}
    for scheme in ("random", "grouped"):
        t = time.perf_counter()
        fold = make_folds(scheme, cl, n_folds, rng)
        Yt, Dt = crossfit(Y, D, X, fold, n_folds, seed)
        tau, sn, sr, G = estimate(Yt, Dt, cl)
        rt[scheme] = time.perf_counter() - t
        for var, se in (("naive", sn), ("robust", sr)):
            rows.append(dict(folds=scheme, variance=var, tau=tau, se=se, lo=tau - z * se, hi=tau + z * se, G=G))
    return rows, rt
