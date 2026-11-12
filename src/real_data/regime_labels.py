"""Leakage-safe VIX market regime classification."""

import numpy as np
import pandas as pd


def classify_regimes(
    events: pd.DataFrame,
    vix: pd.Series,
    reference_start: str | None = None,
    reference_end: str | None = None,
    window: int = 20,
    reference_years: int | None = None,
) -> pd.DataFrame:
    """Classify events using only pre-announcement VIX history.

    reference_years: optional trailing historical reference length.
    If omitted, use history starting at reference_start or
    the beginning of the available VIX series.
    """

    if isinstance(window, (bool, np.bool_)) or not isinstance(window, (int, np.integer)) or window < 1:
        raise ValueError("window must be positive")
    if reference_years is not None and (isinstance(reference_years, (bool, np.bool_)) or not isinstance(reference_years, (int, np.integer)) or reference_years < 1):
        raise ValueError("reference_years must be positive")

    series = vix.copy()
    series.index = pd.to_datetime(series.index)
    series = series.sort_index()

    if series.index.hasnans:
        raise ValueError("Invalid VIX dates")
    if series.index.has_duplicates:
        raise ValueError("Duplicate VIX dates")
    if series.empty or not np.isfinite(series.to_numpy(dtype=float)).all():
        raise ValueError("VIX contains missing or invalid values")
    if (series <= 0).any():
        raise ValueError("VIX must be positive")

    output = events.copy()
    output["announcement_date"] = pd.to_datetime(
        output["announcement_date"], errors="coerce"
    )

    if output["announcement_date"].isna().any():
        raise ValueError("All events require announcement dates")

    labels = []
    averages = []
    lows = []
    highs = []

    for event_date in output["announcement_date"]:
        # Never use observations from the event date or later.
        history = series.loc[series.index < event_date]

        if reference_start is not None:
            history = history.loc[
                history.index >= pd.Timestamp(reference_start)
            ]

        if reference_end is not None:
            history = history.loc[
                history.index <= pd.Timestamp(reference_end)
            ]

        if reference_years is not None:
            cutoff = event_date - pd.DateOffset(
                years=reference_years
            )
            history = history.loc[history.index >= cutoff]

        # Historical distribution of trailing VIX averages.
        rolling = history.rolling(window).mean().dropna()

        # Reserve the latest window for the event's VIX measure.
        # Earlier windows determine percentile thresholds.
        if len(rolling) < 2:
            labels.append("insufficient_data")
            averages.append(np.nan)
            lows.append(np.nan)
            highs.append(np.nan)
            continue

        event_avg = float(rolling.iloc[-1])
        reference = rolling.iloc[:-1]

        low = float(reference.quantile(0.25))
        high = float(reference.quantile(0.75))

        if event_avg < low:
            label = "calm"
        elif event_avg > high:
            label = "turbulent"
        else:
            label = "mixed"

        labels.append(label)
        averages.append(event_avg)
        lows.append(low)
        highs.append(high)

    output["pre_event_vix20"] = averages
    output["vix_p25"] = lows
    output["vix_p75"] = highs
    output["regime_label"] = labels

    return output
