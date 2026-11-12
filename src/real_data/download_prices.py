"""Download adjusted daily prices for the Week 3 benchmark candidates.

Yahoo Finance is a convenience source for exploratory data preparation. It may
not retain complete history for delisted securities, so all coverage is
reported and no missing observations are silently filled.

Run from the repository root, for example:
    python src/real_data/download_prices.py --start 2007-01-01 --end 2021-01-01
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys
from typing import Iterable

import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "processed" / "week3_benchmark_candidates.csv"
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "week3_adjusted_prices.csv"
DEFAULT_DIAGNOSTICS = ROOT / "data" / "processed" / "week3_price_diagnostics.csv"
BENCHMARK = "^GSPC"


def _date_arg(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from exc


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help="candidate CSV (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="adjusted price CSV (default: %(default)s)")
    parser.add_argument("--diagnostics", type=Path, default=DEFAULT_DIAGNOSTICS,
                        help="coverage report CSV (default: %(default)s)")
    parser.add_argument("--start", type=_date_arg, default=None,
                        help="inclusive window start (YYYY-MM-DD); defaults to earliest dated event minus 1 year")
    parser.add_argument("--end", type=_date_arg, default=None,
                        help="exclusive window end (YYYY-MM-DD); defaults to today")
    parser.add_argument("--lookback-days", type=int, default=365,
                        help="calendar days before earliest event when --start is omitted (default: 365)")
    parser.add_argument("--benchmark", default=BENCHMARK,
                        help="market benchmark ticker (default: %(default)s)")
    parser.add_argument("--min-observations", type=int, default=20,
                        help="minimum observations for a ticker to be marked usable (default: %(default)s)")
    args = parser.parse_args(argv)
    if args.start and args.end and args.start >= args.end:
        parser.error("--start must be earlier than --end")
    if args.lookback_days < 0 or args.min_observations < 1:
        parser.error("--lookback-days must be nonnegative and --min-observations positive")
    return args


def resolve_window(events: pd.DataFrame, start: str | None, end: str | None,
                   lookback_days: int) -> tuple[str, str]:
    event_dates = pd.to_datetime(events.get("effective_date", pd.Series(dtype=str)), errors="coerce").dropna()
    earliest = event_dates.min().date() if not event_dates.empty else date.today()
    start_date = date.fromisoformat(start) if start else earliest - pd.Timedelta(days=lookback_days)
    end_date = date.fromisoformat(end) if end else date.today() + pd.Timedelta(days=1)
    if start_date >= end_date:
        raise ValueError("resolved start date must be earlier than end date")
    return start_date.isoformat(), end_date.isoformat()


def normalize_download(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Return a flat Date-indexed adjusted-close panel across yfinance versions."""
    if raw.empty:
        return pd.DataFrame(columns=tickers, index=pd.DatetimeIndex([], name="Date"))
    if isinstance(raw.columns, pd.MultiIndex):
        # yfinance has emitted both (Price, Ticker) and (Ticker, Price).
        if "Adj Close" in raw.columns.get_level_values(0):
            prices = raw.xs("Adj Close", axis=1, level=0, drop_level=True)
        elif "Adj Close" in raw.columns.get_level_values(-1):
            prices = raw.xs("Adj Close", axis=1, level=-1, drop_level=True)
        elif "Close" in raw.columns.get_level_values(0):
            prices = raw.xs("Close", axis=1, level=0, drop_level=True)
        elif "Close" in raw.columns.get_level_values(-1):
            prices = raw.xs("Close", axis=1, level=-1, drop_level=True)
        else:
            return pd.DataFrame(index=raw.index)
    else:
        # auto_adjust=True means Close is split/dividend adjusted; older yfinance
        # versions with auto_adjust=False provide Adj Close directly.
        col = "Adj Close" if "Adj Close" in raw.columns else "Close"
        if col not in raw.columns:
            return pd.DataFrame(index=raw.index)
        prices = raw[[col]].copy()
        prices.columns = [tickers[0]] if len(tickers) == 1 else prices.columns
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()
    prices.index = pd.to_datetime(prices.index).tz_localize(None).normalize()
    prices.index.name = "Date"
    prices = prices.loc[:, ~prices.columns.duplicated()]
    return prices.apply(pd.to_numeric, errors="coerce").sort_index()


def build_diagnostics(events: pd.DataFrame, prices: pd.DataFrame, start: str,
                      end: str, min_observations: int) -> pd.DataFrame:
    records = []
    for row in events.to_dict(orient="records"):
        ticker = str(row.get("ticker", "")).strip().upper()
        series = prices[ticker].dropna() if ticker in prices else pd.Series(dtype=float)
        event_value = row.get("effective_date")
        event = pd.to_datetime(event_value, errors="coerce")
        in_window = bool(pd.notna(event) and pd.Timestamp(start) <= event < pd.Timestamp(end))
        has_event_price = bool(in_window and event.normalize() in series.index)
        records.append({
            "ticker": ticker,
            "company_name": row.get("company_name", ""),
            "cluster_id": row.get("cluster_id", ""),
            "effective_date": event_value or "",
            "window_start": start,
            "window_end_exclusive": end,
            "observations": int(series.size),
            "first_price_date": series.index.min().date().isoformat() if not series.empty else "",
            "last_price_date": series.index.max().date().isoformat() if not series.empty else "",
            "event_date_in_window": in_window,
            "event_date_has_price": has_event_price,
            "status": "usable" if series.size >= min_observations else "insufficient_or_unavailable",
        })
    return pd.DataFrame(records)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.is_file():
        print(f"ERROR: candidate CSV not found: {args.input}", file=sys.stderr)
        return 2
    events = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    required = {"ticker", "company_name", "cluster_id", "effective_date"}
    missing = required - set(events.columns)
    if missing:
        print(f"ERROR: input CSV is missing columns: {', '.join(sorted(missing))}", file=sys.stderr)
        return 2
    events["ticker"] = events["ticker"].astype(str).str.strip().str.upper()
    events = events[events["ticker"].ne("")].drop_duplicates("ticker", keep="first")
    if events.empty:
        print("ERROR: input CSV contains no tickers", file=sys.stderr)
        return 2

    start, end = resolve_window(events, args.start, args.end, args.lookback_days)
    tickers = list(events["ticker"]) + ([args.benchmark] if args.benchmark not in events["ticker"].tolist() else [])
    print(f"Requesting {len(tickers)} symbols from {start} through {end} (end exclusive).")
    print("Using auto-adjusted Yahoo Finance Close prices; this does not guarantee complete delisted-firm history.")
    prices = pd.DataFrame()
    for ticker in tickers:
      try:
        download_ticker = "BFH" if ticker == "ADS" else ticker
        raw = yf.download(
              download_ticker,
              start=start,
              end=end,
              auto_adjust=True,
              actions=False,
              progress=False,
              threads=False,
        )
        one = normalize_download(raw, [ticker])

        if ticker in one.columns:
            prices[ticker] = one[ticker]
        elif one.shape[1] == 1:
            prices[ticker] = one.iloc[:, 0]
        else:
            print(f"No usable price column returned for {ticker}")
      except Exception as exc:
        print(f"Download failed for {ticker}: {exc}")

    for ticker in tickers:
        if ticker not in prices.columns:
            prices[ticker] = np.nan
    prices = prices.reindex(columns=tickers).dropna(how="all")
    prices.index.name = "Date"
    returns = prices.pct_change(fill_method=None).add_suffix("_return")
    output = pd.concat([prices, returns], axis=1).reset_index()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False, date_format="%Y-%m-%d")

    diagnostics = build_diagnostics(events, prices, start, end, args.min_observations)
    diagnostics.to_csv(args.diagnostics, index=False)
    print(f"Saved prices and daily returns: {args.output}")
    print(f"Saved coverage diagnostics: {args.diagnostics}")
    print(diagnostics[["ticker", "observations", "first_price_date", "last_price_date", "event_date_has_price", "status"]].to_string(index=False))
    unavailable = diagnostics.loc[diagnostics["observations"].eq(0), "ticker"].tolist()
    if unavailable:
        print("No price observations returned for: " + ", ".join(unavailable))
    missing_dates = diagnostics.loc[diagnostics["effective_date"].eq(""), "ticker"].tolist()
    if missing_dates:
        print("Event-date coverage cannot be checked for rows with blank effective_date: " + ", ".join(missing_dates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
