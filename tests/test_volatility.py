"""Deterministic recurrence, numerical boundaries and population-level checks."""

import numpy as np
import pytest

from src.dgp.volatility import garch_parameters, simulate_volatility


@pytest.mark.parametrize("rho", [0.0, 0.3, 0.9, 0.98])
@pytest.mark.parametrize("variance", [0.0004, 1.0, 9.0])
def test_mapping_preserves_unconditional_variance(rho, variance):
    params = garch_parameters(rho, unconditional_variance=variance)
    assert params.alpha + params.beta == pytest.approx(rho)
    assert params.omega / (1 - params.persistence) == pytest.approx(variance)
    assert params.fourth_moment_factor == pytest.approx(rho**2 * 1.02)


def test_exact_recurrence_and_rng_draw_order():
    seed, firms, periods = 78, 3, 9
    params = garch_parameters(0.8, unconditional_variance=4)
    sigma, eps = simulate_volatility(
        firms, periods, 0.8, np.random.default_rng(seed),
        unconditional_variance=4, burn_in=0,
    )
    expected_eps = np.random.default_rng(seed).standard_normal((periods, firms)).T
    np.testing.assert_array_equal(eps, expected_eps)
    expected_h = np.full((firms, periods), 4.0)
    for time in range(1, periods):
        previous_e = np.sqrt(expected_h[:, time - 1]) * expected_eps[:, time - 1]
        expected_h[:, time] = params.omega + params.alpha * previous_e**2 + params.beta * expected_h[:, time - 1]
    np.testing.assert_allclose(sigma**2, expected_h, rtol=2e-15)


def test_burn_in_is_exact_prefix_discard_and_period_extension_is_stable():
    full = simulate_volatility(4, 38, 0.9, np.random.default_rng(2), burn_in=0)
    burned = simulate_volatility(4, 30, 0.9, np.random.default_rng(2), burn_in=8)
    longer = simulate_volatility(4, 40, 0.9, np.random.default_rng(2), burn_in=8)
    for original, trimmed, extended in zip(full, burned, longer):
        np.testing.assert_array_equal(original[:, 8:], trimmed)
        np.testing.assert_array_equal(extended[:, :30], trimmed)


def test_replay_scale_and_firm_innovations():
    base = simulate_volatility(12, 200, 0.9, np.random.default_rng(3))
    replay = simulate_volatility(12, 200, 0.9, np.random.default_rng(3))
    scaled = simulate_volatility(12, 200, 0.9, np.random.default_rng(3), unconditional_variance=4)
    assert base[0].shape == base[1].shape == (12, 200)
    assert np.all(np.isfinite(base[0])) and np.all(base[0] > 0)
    for a, b in zip(base, replay):
        np.testing.assert_array_equal(a, b)
    np.testing.assert_allclose(scaled[0], 2 * base[0], rtol=1e-15)
    np.testing.assert_array_equal(scaled[1], base[1])
    assert not np.array_equal(base[1][0], base[1][1])


def test_zero_persistence_is_homoskedastic_even_after_burn_in():
    sigma, _ = simulate_volatility(3, 100, 0, np.random.default_rng(4), unconditional_variance=4)
    np.testing.assert_array_equal(sigma, np.full((3, 100), 2.0))


@pytest.mark.parametrize("kwargs", [
    {"persistence": -0.1}, {"persistence": 1}, {"persistence": np.nan},
    {"persistence": np.inf}, {"unconditional_variance": 0},
    {"unconditional_variance": -1}, {"unconditional_variance": np.inf},
    {"arch_share": 0}, {"arch_share": 1.1}, {"arch_share": np.nan},
])
def test_invalid_coefficients(kwargs):
    args = {"persistence": 0.9} | kwargs
    with pytest.raises(ValueError):
        garch_parameters(**args)


@pytest.mark.parametrize("kwargs", [
    {"n_firms": 0}, {"n_periods": -2}, {"burn_in": -1},
    {"n_firms": True}, {"n_periods": 2.5}, {"burn_in": False},
    {"rng": 4}, {"rng": np.random.RandomState(2)}, {"persistence": True},
])
def test_invalid_dimensions_and_rng(kwargs):
    args = dict(n_firms=2, n_periods=3, persistence=0.9, rng=np.random.default_rng(1))
    with pytest.raises((TypeError, ValueError)):
        simulate_volatility(**(args | kwargs))


def test_finite_variance_does_not_imply_finite_fourth_moment():
    params = garch_parameters(0.995)
    assert params.persistence < 1
    assert not params.has_finite_fourth_moment
    with pytest.raises(ValueError, match="fourth moment"):
        params.squared_return_acf(3)
    sigma, eps = simulate_volatility(3, 100, 0.995, np.random.default_rng(9))
    assert np.isfinite(sigma).all() and np.isfinite(eps).all()


def test_population_acf_matches_arch1_special_case_and_garch_decay():
    arch1 = garch_parameters(0.3, arch_share=1)
    np.testing.assert_allclose(arch1.squared_return_acf(5), 0.3 ** np.arange(6))
    garch = garch_parameters(0.9)
    acf = garch.squared_return_acf(5)
    np.testing.assert_allclose(acf[2:] / acf[1:-1], 0.9)
    np.testing.assert_array_equal(garch_parameters(0).squared_return_acf(3), [1, 0, 0, 0])


def test_smallest_shapes_and_parameter_boundaries():
    for rho, share in ((0, 1), (0.5, 1), (np.nextafter(1.0, 0.0), 0.1)):
        sigma, eps = simulate_volatility(np.int64(1), np.int64(1), rho, np.random.default_rng(5), arch_share=share, burn_in=np.int64(0))
        assert sigma[0, 0] == 1
        assert eps.shape == (1, 1)


def test_intercept_underflow_is_not_silently_accepted():
    with pytest.raises(ValueError, match="underflows"):
        garch_parameters(0.9, unconditional_variance=np.nextafter(0.0, 1.0))


def test_numerical_explosion_raises_with_time_instead_of_clipping():
    with pytest.raises(FloatingPointError, match="time"):
        simulate_volatility(20, 100, 0.8, np.random.default_rng(42), unconditional_variance=1e308, burn_in=0)


def test_moderate_panel_has_correct_variance_and_innovation_scale():
    # Broad deterministic smoke tolerances; full MC uncertainty is in diagnostics.
    sigma, eps = simulate_volatility(100, 2500, 0.8, np.random.default_rng(91))
    assert abs(np.mean(sigma**2) - 1) < 0.03
    assert abs(np.mean((sigma * eps)**2) - 1) < 0.04
    assert abs(eps.mean()) < 0.01
    assert abs(np.mean(eps**2) - 1) < 0.02


@pytest.mark.parametrize("share", [1e-8, 1e-10, 1e-12])
def test_near_unit_boundary_matches_high_precision_coefficient_arithmetic(share):
    from decimal import Decimal, localcontext

    params = garch_parameters(np.nextafter(1.0, 0.0), arch_share=share)
    with localcontext() as context:
        context.prec = 80
        alpha, beta = Decimal.from_float(params.alpha), Decimal.from_float(params.beta)
        rho = alpha + beta
        margin = 1 - (3 * alpha**2 + 2 * alpha * beta + beta**2)
        expected_acf = alpha * (1 - beta * rho) / (1 + beta**2 - 2 * beta * rho)
        expected_variance = Decimal.from_float(params.omega) / (1 - rho)
    assert params.has_finite_fourth_moment == (margin > 0)
    assert params.fourth_moment_margin == pytest.approx(float(margin), rel=1e-14)
    assert float(expected_variance) == pytest.approx(1.0, rel=2e-16)
    assert params.squared_return_acf(2)[1] == pytest.approx(float(expected_acf), rel=1e-14)
