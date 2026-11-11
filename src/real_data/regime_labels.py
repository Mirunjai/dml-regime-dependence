
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
