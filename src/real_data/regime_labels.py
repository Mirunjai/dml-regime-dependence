
"""Pre-event VIX-based market regime classification."""

import numpy as np
import pandas as pd


def classify_regimes(
    events: pd.DataFrame,
    vix: pd.Series,
    reference_start: str,
    reference_end: str,
    window: int = 20,
) -> pd.DataFrame:
    """Classify events using only pre-event VIX observations."""

    if window < 1:
        raise ValueError("window must be positive")

    vix = vix.copy()
    vix.index = pd.to_datetime(vix.index)
    vix = vix.sort_index()

    if vix.index.has_duplicates:
        raise ValueError("Duplicate VIX dates")
    if vix.isna().any() or not np.isfinite(vix.to_numpy()).all():
        raise ValueError("VIX contains missing or invalid values")

    reference = vix.loc[reference_start:reference_end]

    if len(reference) < window:
        raise ValueError("Insufficient reference VIX observations")

    # Reference distribution of trailing VIX averages.
    historical = reference.rolling(window).mean().dropna()

    low = historical.quantile(0.25)
    high = historical.quantile(0.75)

    output = events.copy()
    output["announcement_date"] = pd.to_datetime(
        output["announcement_date"], errors="coerce"
    )

    if output["announcement_date"].isna().any():
        raise ValueError("All events require announcement dates")

    labels = []
    averages = []

    for event_date in output["announcement_date"]:
        # Strictly exclude the announcement date itself.
        previous = vix.loc[vix.index < event_date].tail(window)

        if len(previous) < window:
            labels.append("insufficient_data")
            averages.append(np.nan)
            continue

        avg = float(previous.mean())
        averages.append(avg)

        if avg < low:
            labels.append("calm")
        elif avg > high:
            labels.append("turbulent")
        else:
            labels.append("mixed")

    output["pre_event_vix20"] = averages
    output["regime_label"] = labels
    output["vix_reference_start"] = reference_start
    output["vix_reference_end"] = reference_end

    return output

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

    if window < 1:
        raise ValueError("window must be positive")
    if reference_years is not None and reference_years < 1:
        raise ValueError("reference_years must be positive")

    series = vix.copy()
    series.index = pd.to_datetime(series.index)
    series = series.sort_index()

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
