
"""Tests for leakage-safe VIX regime classification."""

import numpy as np
import pandas as pd
import pytest

from src.real_data.regime_labels import classify_regimes


def sample_vix():
    dates = pd.bdate_range("2020-01-01", periods=150)

    # Different volatility episodes.
    values = np.concatenate([
        np.full(30, 20.0),
        np.full(30, 40.0),
        np.full(30, 10.0),
        np.full(30, 25.0),
        np.full(30, 50.0),
    ])

    return pd.Series(values, index=dates)


def classify_at(position):
    vix = sample_vix()

    event_date = vix.index[position]

    events = pd.DataFrame({
        "announcement_date": [event_date]
    })

    return classify_regimes(
        events,
        vix,
        window=5,
    )


def test_calm_regime():
    result = classify_at(85)
    assert result.iloc[0]["regime_label"] == "calm"


def test_turbulent_regime():
    result = classify_at(145)
    assert result.iloc[0]["regime_label"] == "turbulent"


def test_mixed_regime():
    result = classify_at(115)
    assert result.iloc[0]["regime_label"] == "mixed"


def test_insufficient_data():
    result = classify_at(2)
    assert result.iloc[0]["regime_label"] == "insufficient_data"


def test_missing_event_date_rejected():
    events = pd.DataFrame({
        "announcement_date": [None]
    })

    with pytest.raises(ValueError):
        classify_regimes(
            events,
            sample_vix(),
            window=5,
        )


def test_invalid_window_rejected():
    events = pd.DataFrame({
        "announcement_date": ["2020-02-10"]
    })

    with pytest.raises(ValueError):
        classify_regimes(
            events,
            sample_vix(),
            window=0,
        )


def test_future_data_does_not_change_past_label():
    vix = sample_vix()
    event_date = vix.index[85]

    events = pd.DataFrame({
        "announcement_date": [event_date]
    })

    original = classify_regimes(
        events,
        vix,
        window=5,
    )

    modified = vix.copy()

    # Change every observation on/after the event.
    modified.loc[modified.index >= event_date] = 100.0

    updated = classify_regimes(
        events,
        modified,
        window=5,
    )

    assert (
        original.iloc[0]["regime_label"]
        == updated.iloc[0]["regime_label"]
    )

    assert np.isclose(
        original.iloc[0]["pre_event_vix20"],
        updated.iloc[0]["pre_event_vix20"],
    )
