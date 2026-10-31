
"""Tests for the regime/common-shock generator."""

import numpy as np
import pytest

from src.dgp.regime_shocks import simulate_regimes


def test_output_shapes():
    ids, shocks = simulate_regimes(
        100, 0.6, 5, np.random.default_rng(42)
    )
    assert ids.shape == (100,)
    assert shocks.shape == (100,)


def test_density():
    ids, _ = simulate_regimes(
        100, 0.6, 5, np.random.default_rng(42)
    )
    assert np.mean(ids >= 0) == pytest.approx(0.6)


def test_number_of_regimes():
    ids, _ = simulate_regimes(
        100, 0.6, 5, np.random.default_rng(42)
    )
    assert len(np.unique(ids[ids >= 0])) == 5


def test_shared_shocks():
    ids, shocks = simulate_regimes(
        100, 0.8, 4, np.random.default_rng(42)
    )

    for regime in np.unique(ids[ids >= 0]):
        values = shocks[ids == regime]
        assert np.all(values == values[0])


def test_inactive_windows():
    ids, shocks = simulate_regimes(
        100, 0.2, 4, np.random.default_rng(42)
    )
    assert np.all(shocks[ids == -1] == 0)


def test_reproducibility():
    result1 = simulate_regimes(
        100, 0.5, 5, np.random.default_rng(42)
    )
    result2 = simulate_regimes(
        100, 0.5, 5, np.random.default_rng(42)
    )

    for a, b in zip(result1, result2):
        np.testing.assert_array_equal(a, b)


def test_zero_density():
    ids, shocks = simulate_regimes(
        100, 0.0, 5, np.random.default_rng(42)
    )
    assert np.all(ids == -1)
    assert np.all(shocks == 0)


def test_invalid_configuration():
    with pytest.raises(ValueError):
        simulate_regimes(
            10, 0.1, 5, np.random.default_rng(42)
        )
