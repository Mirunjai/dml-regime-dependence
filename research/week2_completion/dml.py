"""Cross-fitted PLR comparison using full regime membership.

The overlap sandwich is an asymptotic *regime-only* covariance proposal, not a
few-cluster correction or a correction for shared calendar factors. Numerical
variance failures and impossible grouped splits are retained per cell. See the
review memo before interpreting this experimental implementation scientifically.
"""
from __future__ import annotations

from math import fsum
import time
from numbers import Integral

import numpy as np
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor

CELLS = (("random", "naive"), ("random", "multiway"),
         ("grouped", "naive"), ("grouped", "multiway"))


def _memberships(memberships, n):
    if len(memberships) != n:
        raise ValueError("Membership count must match observations")
    clean = []
    for membership in memberships:
        values = []
        for value in membership:
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < 0:
                raise ValueError("Membership IDs must be nonnegative integers")
            values.append(int(value))
        clean.append(tuple(sorted(set(values))))
    return clean


def _validate_arrays(Y, D, X, memberships):
    if any(np.iscomplexobj(value) for value in (Y, D, X)):
        raise ValueError("Inputs must be real")
    Y, D, X = np.asarray(Y, dtype=float), np.asarray(D, dtype=float), np.asarray(X, dtype=float)
    if Y.ndim != 1:
        raise ValueError("Y must be a vector")
    n = len(Y)
    if D.shape != (n,) or X.ndim != 2 or X.shape[0] != n:
        raise ValueError("Expected Y,D[n], X[n,p], and n membership sets")
    if n < 4 or X.shape[1] < 1 or not all(np.isfinite(value).all() for value in (Y, D, X)):
        raise ValueError("Inputs must be finite and contain at least four observations")
    return Y, D, X, _memberships(memberships, n)


def _components(memberships):
    n = len(memberships)
    memberships = _memberships(memberships, n)
    parent, rank, owner = list(range(n)), [0] * n, {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a == b:
            return
        if rank[a] < rank[b]:
            a, b = b, a
        parent[b] = a
        if rank[a] == rank[b]:
            rank[a] += 1

    for i, membership in enumerate(memberships):
        for regime in membership:
            if regime in owner:
                union(i, owner[regime])
            else:
                owner[regime] = i
    _, labels = np.unique([find(i) for i in range(n)], return_inverse=True)
    return labels


def make_folds(scheme, memberships, n_folds, rng):
    n = len(memberships)
    memberships = _memberships(memberships, n)
    if isinstance(n_folds, (bool, np.bool_)) or not isinstance(n_folds, Integral) or not 2 <= n_folds <= n:
        raise ValueError("n_folds must be between 2 and n")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy Generator")
    if scheme == "random":
        perm = rng.permutation(n)
        fold = np.empty(n, dtype=int)
        fold[perm] = np.arange(n) % n_folds
        return fold
    if scheme != "grouped":
        raise ValueError("scheme must be random or grouped")
    groups = _components(memberships)
    unique, inverse = np.unique(groups, return_inverse=True)
    if len(unique) < n_folds:
        raise ValueError(f"Only {len(unique)} independent dependence-graph components "
                         f"(regime memberships only); cannot form {n_folds} grouped folds")
    sizes = np.bincount(inverse)
    order = np.lexsort((rng.random(len(unique)), -sizes))
    load, group_fold = np.zeros(n_folds), np.empty(len(unique), dtype=int)
    for group in order:
        selected = int(np.argmin(load))
        group_fold[group] = selected
        load[selected] += sizes[group]
    return group_fold[inverse]


def _learner(seed, n_estimators=40):
    return RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=8,
                                 max_features=.5, n_jobs=1, random_state=int(seed))


def crossfit(Y, D, X, fold, n_folds, seed):
    n = len(Y)
    if (fold.shape != (n,) or fold.dtype.kind not in "iu"
            or set(np.unique(fold)) != set(range(n_folds))):
        raise ValueError("Every fold must be nonempty and represented by integer labels")
    my, md = np.empty(n), np.empty(n)
    for k in range(n_folds):
        train, test = fold != k, fold == k
        if train.sum() < 2 or not test.any():
            raise ValueError(f"Invalid train/test partition for fold {k}")
        my[test] = _learner(seed + k).fit(X[train], Y[train]).predict(X[test])
        md[test] = _learner(seed + 100 + k).fit(X[train], D[train]).predict(X[test])
    return Y - my, D - md


def _multiway_meat(psi, memberships):
    """The same overlap sandwich, counted directly rather than via 2**K subsets.

    Each diagonal is included; each unordered pair sharing any regime contributes
    twice. Returns (meat, number_of_shared_unordered_pairs). This identity avoids
    exponential allocation when an event touches many regimes. Negative meat is
    still possible because the overlap adjacency need not be positive semidefinite.
    """
    psi = np.asarray(psi, dtype=float)
    if psi.ndim != 1 or not np.isfinite(psi).all():
        raise ValueError("Scores must be a finite vector")
    memberships = _memberships(memberships, len(psi))
    owners, terms, pair_count = {}, [], 0
    with np.errstate(over="raise", invalid="raise"):
        terms.extend(float(value) for value in psi ** 2)
        for i, membership in enumerate(memberships):
            neighbors = set()
            for regime in membership:
                neighbors.update(owners.get(regime, ()))
            if neighbors:
                pair_count += len(neighbors)
                terms.append(float(2 * psi[i] * fsum(float(psi[j]) for j in sorted(neighbors))))
            for regime in membership:
                owners.setdefault(regime, []).append(i)
    return fsum(terms), pair_count

def estimate(Yt, Dt, memberships, alpha=.05, *, allow_invalid_multiway=False):
    Yt, Dt = np.asarray(Yt, dtype=float), np.asarray(Dt, dtype=float)
    if Yt.ndim != 1 or Dt.shape != Yt.shape or not np.isfinite(Yt).all() or not np.isfinite(Dt).all():
        raise ValueError("Residuals must be matching finite vectors")
    memberships = _memberships(memberships, len(Yt))
    if isinstance(alpha, (bool, np.bool_)) or not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        J = float(np.sum(Dt ** 2))
        if not np.isfinite(J) or J <= np.finfo(float).eps:
            raise ValueError("Residualized treatment has zero/near-zero sum of squares")
        tau = float(np.sum(Dt * Yt) / J)
        psi = Dt * (Yt - tau * Dt)
        naive = float(np.sqrt(np.sum(psi ** 2)) / J)
    if not np.isfinite(tau) or not np.isfinite(naive):
        raise FloatingPointError("Nonfinite point estimate or naive standard error")
    multiway, dependency_pairs, error = None, None, None
    try:
        meat, dependency_pairs = _multiway_meat(psi, memberships)
        if not np.isfinite(meat) or meat <= 0:
            raise ValueError(f"Multiway sandwich meat is nonpositive ({meat}); inference undefined")
        multiway = float(np.sqrt(meat) / J)
        if not np.isfinite(multiway):
            raise FloatingPointError("Nonfinite multiway standard error")
    except (ValueError, FloatingPointError, OverflowError) as exc:
        if not allow_invalid_multiway:
            raise
        error = f"{type(exc).__name__}: {exc}"
    critical = float(norm.ppf(1 - alpha / 2))
    if not np.isfinite(critical):
        raise ValueError("Critical value is not representable at this alpha")
    return {"tau": tau, "se_naive": naive, "se_multiway": multiway,
            "multiway_error": error, "n_multiway_intersections": None,
            "n_dependency_pairs": dependency_pairs,
            "score_sum": float(psi.sum()), "J": J, "critical_value": critical}


def audit_folds(data, folds):
    """Potential cross-fold shared sources; index relations are not a test."""
    memberships = [set(m) for m in data["cluster_memberships"]]
    n = len(memberships)
    regime_pairs = sum(bool(memberships[i] & memberships[j]) and folds[i] != folds[j]
                       for i in range(n) for j in range(i + 1, n))
    cfg = data.get("cfg")
    factor_present = bool(cfg.sd_factor > 0) if cfg is not None else None
    calendar_pairs = None
    if factor_present is False:
        calendar_pairs = 0
    elif factor_present and "idx" in data:
        windows = [set(map(int, indices)) for indices in data["idx"]]
        calendar_pairs = sum(bool(windows[i] & windows[j]) and folds[i] != folds[j]
                             for i in range(n) for j in range(i + 1, n))
    return {"regime_cross_fold_pairs": int(regime_pairs),
            "calendar_factor_cross_fold_pairs": None if calendar_pairs is None else int(calendar_pairs),
            "calendar_factor_present": factor_present,
            "all_known_sources_fold_pure": None if calendar_pairs is None else bool(not regime_pairs and not calendar_pairs),
            "scope": "Potential dependence from regime labels and shared calendar-factor dates; no significance claim"}


def run_dml(data, n_folds=5, seed=0, alpha=.05):
    Y, D, X, memberships = _validate_arrays(data["Y"], data["D"], data["X"], data["cluster_memberships"])
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral) or not 0 <= seed < 2**32 - 101 - n_folds:
        raise ValueError("Estimator seed must fit the sklearn uint32 seed range, including fold offsets")
    rows, runtime = [], {}
    for scheme in ("random", "grouped"):
        started, fold, info = time.perf_counter(), None, None
        try:
            fold = make_folds(scheme, memberships, n_folds, np.random.default_rng(seed + (scheme == "grouped")))
            Yt, Dt = crossfit(Y, D, X, fold, n_folds, seed)
            result = estimate(Yt, Dt, memberships, alpha, allow_invalid_multiway=True)
            info = audit_folds(data, fold)
            for variance, key in (("naive", "se_naive"), ("multiway", "se_multiway")):
                se, tau, z = result[key], result["tau"], result["critical_value"]
                failure = result["multiway_error"] if variance == "multiway" else None
                rows.append({"folds": scheme, "variance": variance, "status": "failed" if failure else "ok",
                             "error": failure, "tau": tau, "se": se,
                             "lo": tau - z * se if se is not None else None,
                             "hi": tau + z * se if se is not None else None,
                             "n_multiway_intersections": None, "n_dependency_pairs": result["n_dependency_pairs"],
                             "fold_ids": fold.tolist(), "fold_diagnostics": info})
        except Exception as exc:
            for variance in ("naive", "multiway"):
                rows.append({"folds": scheme, "variance": variance, "status": "failed",
                             "error": f"{type(exc).__name__}: {exc}", "tau": None, "se": None,
                             "lo": None, "hi": None, "n_multiway_intersections": None, "n_dependency_pairs": None,
                             "fold_ids": fold.tolist() if fold is not None else None, "fold_diagnostics": info})
        runtime[scheme] = time.perf_counter() - started
    return rows, runtime
