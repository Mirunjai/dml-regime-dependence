
"""Tests for the classical market-model event study."""

import numpy as np
import pytest

from src.benchmarks.event_study import market_model_event_study


def test_known_market_model():
    """Perfect market-model data should have zero abnormal returns."""
    market = np.linspace(-0.02, 0.02, 100)
    stock = 0.001 + 1.5 * market

    result = market_model_event_study(
        stock, market, 70, 80, 85
    )

    assert result["alpha"] == pytest.approx(0.001)
    assert result["beta"] == pytest.approx(1.5)
    np.testing.assert_allclose(
        result["abnormal_returns"],
        0,
        atol=1e-12,
    )
    assert result["car"] == pytest.approx(0, abs=1e-12)


def test_known_event_effect():
    """An injected 2% effect over 6 days gives CAR = 12%."""
    market = np.linspace(-0.02, 0.02, 100)
    stock = 0.001 + 1.5 * market
    stock[80:86] += 0.02

    result = market_model_event_study(
        stock, market, 70, 80, 85
    )

    np.testing.assert_allclose(
        result["abnormal_returns"],
        0.02,
        atol=1e-12,
    )
    assert result["car"] == pytest.approx(0.12)


def test_cumulative_returns():
    """Cumulative abnormal returns must equal cumulative AR."""
    market = np.linspace(-0.02, 0.02, 100)
    stock = 0.001 + 1.5 * market
    stock[80:86] += 0.02

    result = market_model_event_study(
        stock, market, 70, 80, 85
    )

    np.testing.assert_allclose(
        result["cumulative_abnormal_returns"],
        np.cumsum(result["abnormal_returns"]),
    )


def test_mismatched_lengths():
    with pytest.raises(ValueError):
        market_model_event_study(
            np.ones(50),
            np.ones(40),
            20,
            30,
            35,
        )


def test_invalid_window():
    with pytest.raises(ValueError):
        market_model_event_study(
            np.ones(100),
            np.linspace(-0.02, 0.02, 100),
            90,
            80,
            85,
        )


def test_zero_market_variance():
    with pytest.raises(ValueError):
        market_model_event_study(
            np.ones(100),
            np.zeros(100),
            70,
            80,
            85,
        )


def test_nonfinite_returns():
    market = np.linspace(-0.02, 0.02, 100)
    stock = 0.001 + 1.5 * market
    stock[10] = np.nan

    with pytest.raises(ValueError):
        market_model_event_study(
            stock, market, 70, 80, 85
        )
