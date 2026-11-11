
"""Run the approved Week 3 classical event-study benchmarks."""

from pathlib import Path

import pandas as pd

from src.benchmarks.event_study import estimate_market_model_event_study


PRICES = Path("data/raw/week3_adjusted_prices.csv")
EVENTS = Path("data/processed/week3_event_day_zero.csv")
OUTPUT = Path("results/benchmarks/week3_classical_event_study.csv")

TICKERS = ["CRM", "FAST", "ADS", "MHK", "SWKS", "ETSY", "TER"]

EVENT_WINDOWS = {
    "primary": (-1, 1),
    "short": (0, 1),
    "wide": (-5, 5),
}

ESTIMATION_WINDOW = (-250, -31)


def main():
    prices = pd.read_csv(PRICES, parse_dates=["Date"])
    prices = prices.set_index("Date").sort_index()
    events = pd.read_csv(EVENTS)

    results = []

    for ticker in TICKERS:
        event_row = events.loc[events["ticker"] == ticker]

        if len(event_row) != 1:
            raise ValueError(
                f"Expected exactly one event for {ticker}"
            )

        event_date = event_row.iloc[0]["event_day_zero"]

        returns = prices[
            [f"{ticker}_return", "^GSPC_return"]
        ].rename(
            columns={f"{ticker}_return": ticker,
                     "^GSPC_return": "^GSPC"}
        )

        row = {
            "ticker": ticker,
            "event_day_zero": event_date,
        }

        for name, window in EVENT_WINDOWS.items():
            result = estimate_market_model_event_study(
                returns,
                stock_ticker=ticker,
                market_ticker="^GSPC",
                event_session=event_date,
                estimation_window=ESTIMATION_WINDOW,
                event_window=window,
            )

            row[f"car_{name}"] = result["car"]

            if name == "primary":
                row["alpha"] = result["alpha"]
                row["beta"] = result["beta"]
                row["estimation_observations"] = (
                    result["estimation_observations"]
                )

        results.append(row)

    output = pd.DataFrame(results)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT, index=False)

    print(output.to_string(index=False))
    print(f"\nSaved: {OUTPUT}")
    print("CTLT excluded: historical prices unavailable.")


if __name__ == "__main__":
    main()
