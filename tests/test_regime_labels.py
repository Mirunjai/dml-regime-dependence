
"""Tests for VIX-based market regime labeling."""

import numpy as np
import pandas as pd
import pytest

from src.real_data.regime_labels import classify_regimes



def sample_vix():
    dates = pd.bdate_range("2020-01-01", periods=120)

    # Gradually increasing values avoid repeated percentile cutoffs.
    values = np.linspace(10.0, 40.0, 120)

    return pd.Series(values, index=dates)



def classify(date, vix=None):
    if vix is None:
        vix = sample_vix()

    events = pd.DataFrame({
        "announcement_date": [date],
    })

    return classify_regimes(
        events,
        vix,
        reference_start="2020-01-01",
        reference_end="2020-06-16",
        window=5,
    )


def test_calm_regime():
    result = classify("2020-02-10")
    assert result.iloc[0]["regime_label"] == "calm"


def test_turbulent_regime():
    result = classify("2020-06-01")
    assert result.iloc[0]["regime_label"] == "turbulent"


def test_mixed_regime():
    result = classify("2020-04-15")
    assert result.iloc[0]["regime_label"] == "mixed"


def test_insufficient_data():
    result = classify("2020-01-03")
    assert result.iloc[0]["regime_label"] == "insufficient_data"
    assert np.isnan(result.iloc[0]["pre_event_vix20"])


def test_missing_event_date_rejected():
    events = pd.DataFrame({"announcement_date": [None]})

    with pytest.raises(ValueError):
        classify_regimes(
            events,
            sample_vix(),
            "2020-01-01",
            "2020-06-16",
            window=5,
        )


def test_invalid_window_rejected():
    with pytest.raises(ValueError):
        classify_regimes(
            pd.DataFrame({"announcement_date": ["2020-02-10"]}),
            sample_vix(),
            "2020-01-01",
            "2020-06-16",
            window=0,
        )
