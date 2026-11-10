"""Characterisation tests for the week2_completion overlap sandwich and fold geometry.

All inputs are SYNTHETIC toy structures. These tests document what the existing
estimator does; they do not endorse it as the primary robust estimator.
"""
import numpy as np
import pytest

from research.week2_completion.dml import _components, _multiway_meat, estimate, make_folds
from scripts.mirun_fold_variance_diagnostics import (
    calendar_share_matrix, leakage, min_eigenvalue, overlap_matrix)


def test_independent_events_meat_equals_sum_of_squared_scores():
    psi = np.array([1., -2., 3., .5])
    meat, pairs = _multiway_meat(psi, [(), (), (), ()])
    assert meat == pytest.approx(np.sum(psi ** 2)) and pairs == 0


def test_single_membership_equals_cr0_cluster_sum():
    rng = np.random.default_rng(1)
    psi = rng.normal(size=12)
    memberships = [(i % 3,) for i in range(12)]
    meat, _ = _multiway_meat(psi, memberships)
    expected = sum(psi[np.arange(12) % 3 == k].sum() ** 2 for k in range(3))
    assert meat == pytest.approx(expected)


def test_single_membership_overlap_matrix_is_psd():
    memberships = [(0,), (0,), (1,), (), (1,), ()]
    assert min_eigenvalue(memberships) >= -1e-12


def test_chain_overlap_matrix_is_not_psd_and_meat_can_be_negative():
    memberships = [(0,), (0, 1), (1,)]
    assert min_eigenvalue(memberships) == pytest.approx(1 - np.sqrt(2))
    meat, _ = _multiway_meat(np.array([1., -1., 1.]), memberships)
    assert meat == pytest.approx(-1.0)


def test_nonpositive_meat_is_reported_as_failed_cell_not_silently_clipped():
    memberships = [(0,), (0, 1), (1,), (), ()]
    Dt = np.array([1., 1., 1., 1., 1.])
    Yt = np.array([1., -1., 1., 0., 0.])
    with pytest.raises(ValueError, match="nonpositive"):
        estimate(Yt, Dt, memberships)
    out = estimate(Yt, Dt, memberships, allow_invalid_multiway=True)
    assert out["se_multiway"] is None and "nonpositive" in out["multiway_error"]


def test_meat_matches_dense_quadratic_form_for_random_overlap():
    rng = np.random.default_rng(7)
    memberships = [tuple(sorted(set(rng.integers(0, 6, size=rng.integers(0, 3))))) for _ in range(30)]
    psi = rng.normal(size=30)
    meat, _ = _multiway_meat(psi, memberships)
    assert meat == pytest.approx(psi @ overlap_matrix(memberships) @ psi, rel=1e-10)


def test_degenerate_inputs_rejected():
    with pytest.raises(ValueError):
        _multiway_meat(np.array([np.nan, 1.]), [(), ()])
    with pytest.raises(ValueError):
        estimate(np.ones(4), np.zeros(4), [()] * 4)


def test_large_scores_raise_instead_of_wrapping():
    with pytest.raises(Exception):
        _multiway_meat(np.array([1e200, 1e200]), [(0,), (0,)])


def test_components_connect_through_multi_membership():
    labels = _components([(0,), (0, 1), (1,), (2,), ()])
    assert labels[0] == labels[1] == labels[2]
    assert len({labels[3], labels[4], labels[0]}) == 3


def test_grouped_folds_never_split_a_regime_but_random_folds_do():
    memberships = [(i % 6,) for i in range(60)]
    grouped = make_folds("grouped", memberships, 3, np.random.default_rng(0))
    random_ = make_folds("random", memberships, 3, np.random.default_rng(0))
    reg = overlap_matrix(memberships) > 0
    np.fill_diagonal(reg, False)
    assert leakage(reg, grouped)[0] == 0
    assert leakage(reg, random_)[0] > 0


def test_grouped_folds_infeasible_when_components_fewer_than_folds():
    with pytest.raises(ValueError, match="cannot form"):
        make_folds("grouped", [(0,), (0, 1), (1,)] * 4, 3, np.random.default_rng(0))


def test_grouped_folds_do_not_separate_shared_calendar_dates():
    # events at adjacent dates share calendar-factor dates but have no regime
    memberships = [()] * 40
    t0 = np.arange(40)
    share = calendar_share_matrix(t0, 5)
    fold = make_folds("grouped", memberships, 5, np.random.default_rng(0))
    cross, total = leakage(share, fold)
    assert total > 0 and cross > 0
