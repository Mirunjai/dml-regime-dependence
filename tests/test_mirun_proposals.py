"""Tests for the separately labelled variance proposals (synthetic toy structures)."""
import numpy as np
import pytest
from dataclasses import replace
from research.mirun_proposals.variance_alternatives import alternatives, decompose
from research.mirun_proposals.nuisance import generic_crossfit, rf_learner, oracle_residuals
from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import crossfit, estimate, make_folds


def test_existing_variant_equals_repo_estimator():
    rng = np.random.default_rng(3)
    Dt, Yt = rng.normal(size=60), rng.normal(size=60)
    mem = [(i % 4,) if i < 40 else () for i in range(60)]
    ref = estimate(Yt, Dt, mem)
    alt = alternatives(Yt, Dt, mem)
    assert alt["tau"] == pytest.approx(ref["tau"])
    assert alt["variants"]["existing_cr0_normal"]["se"] == pytest.approx(ref["se_multiway"])
    assert alt["variants"]["naive_normal"]["se"] == pytest.approx(ref["se_naive"])


def test_decomposition_exact_and_cr1_factors():
    psi = np.array([1., 2., -1., 3., .5, -2.])
    mem = [(0,), (0,), (1,), (), (), ()]
    d = decompose(psi, mem)
    assert d["meat_total"] == pytest.approx(d["meat_singletons"] + d["meat_clustered"])
    assert d["meat_clustered"] == pytest.approx((1 + 2) ** 2 + 1.0) and d["G_reg"] == 2 and d["G_all"] == 5
    rng = np.random.default_rng(0)
    Dt, Yt = rng.normal(size=6), rng.normal(size=6)
    a = alternatives(Yt, Dt, mem)["variants"]
    assert a["cr1_all_normal"]["se"] == pytest.approx(a["existing_cr0_normal"]["se"] * np.sqrt(5 / 4))
    assert a["cr0_t"]["crit"] > 1.96 and a["cr0_t"]["se"] == a["existing_cr0_normal"]["se"]


def test_undefined_variants_are_none_not_imputed():
    rng = np.random.default_rng(1)
    Dt, Yt = rng.normal(size=5), rng.normal(size=5)
    a = alternatives(Yt, Dt, [(), (), (), (), ()])["variants"]          # no regimes: t(G_reg-1) undefined
    assert a["cr0_t"] is None and a["cr1reg_t"] is None and a["existing_cr0_normal"]["se"] is not None


def test_generic_crossfit_with_rf_is_bit_identical_to_repo_crossfit():
    data = build_world(replace(Config(), n=120, T=60, seed=5))
    fold = make_folds("random", data["cluster_memberships"], 5, np.random.default_rng(5))
    a = crossfit(data["Y"], data["D"], data["X"], fold, 5, 5)
    b = generic_crossfit(data["Y"], data["D"], data["X"], fold, 5, 5, rf_learner)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_oracle_treatment_residual_is_unbiased_across_worlds():
    """Within one world the mean is noisy (only K regime draws); across worlds E[D - E[D|X]] = 0
    (approximation is exact here: K=4, d=.5 => single membership)."""
    means = []
    for seed in range(80):
        cfg = replace(Config(), n=400, T=260, n_regimes=4, seed=seed)
        data = build_world(cfg)
        assert max(len(m) for m in data["cluster_memberships"]) <= 1
        means.append(oracle_residuals(data, cfg)[1].mean())
    se = np.std(means, ddof=1) / np.sqrt(len(means))
    assert abs(np.mean(means)) < 3 * se
