
"""Generate VIX-based labels for Week 3 benchmark candidates."""

from pathlib import Path

import pandas as pd

from src.real_data.regime_labels import classify_regimes


EVENTS_PATH = Path(
    "data/processed/week3_benchmark_candidates.csv"
)
VIX_PATH = Path("data/processed/vix_history.csv")
OUTPUT_PATH = Path(
    "results/benchmarks/week3_regime_labels.csv"
)


def main():
    events = pd.read_csv(EVENTS_PATH)

    vix_data = pd.read_csv(
        VIX_PATH,
        parse_dates=["date"],
    )

    vix = pd.Series(
        vix_data["vix_close"].to_numpy(),
        index=vix_data["date"],
        name="vix_close",
    )

    result = classify_regimes(
        events=events,
        vix=vix,
        window=20,
        reference_years=5,
    )

    # Companies in the same announcement cluster
    # must receive the same market-regime label.
    cluster_counts = result.groupby("cluster_id")[
        "regime_label"
    ].nunique()

    if (cluster_counts > 1).any():
        raise ValueError(
            "Inconsistent regime labels within a cluster"
        )

    if (
        result["regime_label"] == "insufficient_data"
    ).any():
        raise ValueError(
            "Insufficient historical VIX data for some events"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(OUTPUT_PATH, index=False)

    print(
        result[
            [
                "ticker",
                "announcement_date",
                "pre_event_vix20",
                "vix_p25",
                "vix_p75",
                "regime_label",
            ]
        ].to_string(index=False)
    )

    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
