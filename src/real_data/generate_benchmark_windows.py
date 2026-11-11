
"""Generate approved benchmark windows using NYSE sessions."""

from pathlib import Path

import exchange_calendars as xc
import pandas as pd


INPUT = Path("data/processed/week3_event_day_zero.csv")
OUTPUT = Path("results/benchmarks/week3_benchmark_windows.csv")

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
    events = pd.read_csv(INPUT)
    calendar = xc.get_calendar("XNYS")

    rows = []

    for _, event in events.iterrows():
        event_date = pd.Timestamp(event["event_day_zero"])

        if not calendar.is_session(event_date):
            raise ValueError(f"Invalid trading date: {event_date}")

        for window_name, (start, end) in WINDOWS.items():
            start_date = calendar.session_offset(event_date, start)
            end_date = calendar.session_offset(event_date, end)

            rows.append({
                "ticker": event["ticker"],
                "event_day_zero": event_date.date().isoformat(),
                "window": window_name,
                "start_offset": start,
                "end_offset": end,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "trading_sessions": end - start + 1,
            })

    result = pd.DataFrame(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    print(result.to_string(index=False))
    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
