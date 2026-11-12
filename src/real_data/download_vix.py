
"""Download historical VIX observations for regime labeling."""

from pathlib import Path

import pandas as pd
import yfinance as yf


def download_vix(
    start="2000-01-01",
    end="2026-11-01",
    output="data/processed/vix_history.csv",
):
    """Download and save daily VIX closing values."""
    prices = yf.download(
        "^VIX",
        start=start,
        end=end,
        auto_adjust=False,
        progress=False,
    )

    if prices.empty:
        raise RuntimeError("No VIX data returned")

    close = prices["Close"]

    # yfinance may return a MultiIndex column.
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    vix = close.dropna().rename("vix_close")
    vix.index.name = "date"

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    vix.to_csv(output_path)

    print(f"Saved {len(vix)} VIX observations")
    print(f"Date range: {vix.index.min()} to {vix.index.max()}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    download_vix()
