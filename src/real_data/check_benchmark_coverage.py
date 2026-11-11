
"""Check complete return coverage on approved benchmark sessions."""

from pathlib import Path

import exchange_calendars as xc
import numpy as np
import pandas as pd


PRICES = Path("data/raw/week3_adjusted_prices.csv")
EVENTS = Path("data/processed/week3_event_day_zero.csv")
OUTPUT = Path("results/benchmarks/week3_window_coverage.csv")

WINDOWS = {
    "classical_estimation": (-250, -31),
    "classical_primary": (-1, 1),
    "classical_short": (0, 1),
    "classical_wide": (-5, 5),
    "scm_fit": (-252, -21),
    "scm_validation": (-20, -1),
    "scm_post_primary": (0, 20),
    "scm_post_long": (0, 60),
}


def main():
    prices = pd.read_csv(PRICES, parse_dates=["Date"])
    prices = prices.set_index("Date").sort_index()

    if prices.index.has_duplicates:
        raise ValueError("Duplicate price dates")

    events = pd.read_csv(EVENTS)
    calendar = xc.get_calendar("XNYS")

    rows = []

    for event in events.itertuples(index=False):
        ticker = event.ticker
        event_day = pd.Timestamp(event.event_day_zero)

        for name, (start, end) in WINDOWS.items():
            start_day = calendar.session_offset(event_day, start)
            end_day = calendar.session_offset(event_day, end)

            sessions = calendar.sessions_in_range(
                start_day, end_day
            ).tz_localize(None)

            stock_col = f"{ticker}_return"
            market_col = "^GSPC_return"

            stock = (
                prices[stock_col].reindex(sessions)
                if stock_col in prices
                else pd.Series(np.nan, index=sessions)
            )

            market = prices[market_col].reindex(sessions)

            stock_valid = np.isfinite(
                stock.to_numpy(dtype=float)
            )
            market_valid = np.isfinite(
                market.to_numpy(dtype=float)
            )

            complete = bool(
                stock_valid.all() and market_valid.all()
            )

            rows.append({
                "ticker": ticker,
                "window": name,
                "expected_sessions": len(sessions),
                "stock_return_observations": int(
                    stock_valid.sum()
                ),
                "market_return_observations": int(
                    market_valid.sum()
                ),
                "missing_stock_returns": int(
                    (~stock_valid).sum()
                ),
                "missing_market_returns": int(
                    (~market_valid).sum()
                ),
                "complete": complete,
            })

    result = pd.DataFrame(rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    print(
        result.pivot(
            index="ticker",
            columns="window",
            values="complete",
        ).to_string()
    )

    print(f"\nComplete windows: {result.complete.sum()}/{len(result)}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
