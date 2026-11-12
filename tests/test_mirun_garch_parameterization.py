from research.week2_completion.dgp import simulate_volatility as fixed_alpha_sim
from src.dgp.volatility import garch_parameters, simulate_volatility as canonical_sim
import numpy as np


def test_fixed_and_canonical_garch_hold_same_unconditional_variance_at_point_nine():
    canonical = garch_parameters(0.90, arch_share=0.10)
    fixed = garch_parameters(0.90, arch_share=0.10 / 0.90)
    assert canonical.unconditional_variance == fixed.unconditional_variance == 1.0
    assert np.isclose(canonical.omega, 0.10) and np.isclose(fixed.omega, 0.10)
    assert np.isclose(canonical.alpha, 0.09)
    assert fixed.alpha == 0.10
    assert canonical.beta == 0.81
    assert fixed.beta == 0.80
    assert canonical.has_finite_fourth_moment
    assert fixed.has_finite_fourth_moment


def test_rho_point_nine_nine_has_different_fourth_moment_status():
    canonical = garch_parameters(0.99, arch_share=0.10)
    fixed = garch_parameters(0.99, arch_share=0.10 / 0.99)
    assert canonical.unconditional_variance == fixed.unconditional_variance == 1.0
    assert canonical.has_finite_fourth_moment
    assert not fixed.has_finite_fourth_moment
    assert canonical.fourth_moment_margin > 0
    assert fixed.fourth_moment_margin < 0


def test_both_implementations_return_finite_positive_volatility_on_smoke():
    sig_c, eps_c = canonical_sim(12, 200, 0.90, np.random.default_rng(10), burn_in=100)
    sig_f, eps_f = fixed_alpha_sim(12, 200, 0.90, np.random.default_rng(10), burn=100)
    for arr in (sig_c, eps_c, sig_f, eps_f):
        assert np.isfinite(arr).all()
    assert (sig_c > 0).all() and (sig_f > 0).all()
