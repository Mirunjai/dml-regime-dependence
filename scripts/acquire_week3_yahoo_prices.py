"""Fetch the frozen Week 3 treated panel from Yahoo Finance through yfinance.

This script does not select donors or run the Synthetic Control benchmark.
Donor tickers must be added only after their eligibility evidence is reviewed.
"""
from __future__ import annotations

import csv
import json
import platform
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "week3_yahoo"
OUT.mkdir(parents=True, exist_ok=True)

import pandas as pd
import yfinance as yf

# Frozen per-event coverage spans already used in the Week 3 data-access request.
EVENTS = [
    ("CRM", "2008-09-10", "2007-09-11", "2008-12-04", "2008-09-12"),
    ("FAST", "2008-09-10", "2007-09-11", "2008-12-04", "2008-09-12"),
    ("ADS", "2013-12-11", "2012-12-11", "2014-03-11", "2013-12-20"),
    ("MHK", "2013-12-11", "2012-12-11", "2014-03-11", "2013-12-20"),
    ("SWKS", "2015-03-09", "2014-03-07", "2015-06-03", "2015-03-11"),
    ("ETSY", "2020-09-08", "2019-09-09", "2020-12-02", "2020-09-21"),
    ("TER", "2020-09-08", "2019-09-09", "2020-12-02", "2020-09-21"),
    ("CTLT", "2020-09-08", "2019-09-09", "2020-12-02", "2020-09-21"),
]

# Candidate names already present in the research queue. These are price-coverage
# probes only and remain unverified, ineligible leads until the screening gates pass.
CANDIDATES = [
    ("CRM", "NOW"), ("CRM", "WDAY"),
    ("FAST", "GWW"), ("FAST", "MSM"),
    ("ADS", "SYF"), ("ADS", "COF"),
    ("MHK", "TILE"), ("MHK", "LEG"),
    ("SWKS", "QRVO"), ("SWKS", "CRUS"),
    ("ETSY", "EBAY"), ("ETSY", "SHOP"),
    ("TER", "COHU"), ("TER", "FORM"),
]

def main() -> None:
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows: list[dict] = []
    spy_rows: list[dict] = []
    logs: list[dict] = []
    gaps: list[dict] = []
    calendars: dict[str, set[str]] = {}

    # SPY supplies the exchange-session calendar used only for missingness checks.
    for start, end in sorted({(e[2], e[3]) for e in EVENTS}):
        end_exclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            cal = yf.Ticker("SPY").history(
                start=start, end=end_exclusive, interval="1d",
                auto_adjust=False, actions=True,
            )
            calendars[start] = {pd.Timestamp(x).date().isoformat() for x in cal.index}
            for date, r in cal.iterrows():
                spy_rows.append({"ticker":"SPY", "window_start":start, "window_end_inclusive":end,
                    "date":pd.Timestamp(date).date().isoformat(), "close_raw":r.get("Close"),
                    "adj_close":r.get("Adj Close"), "volume_raw":r.get("Volume"),
                    "dividends":r.get("Dividends"), "stock_splits":r.get("Stock Splits")})
            logs.append({
                "ticker": "SPY", "role": "calendar_only", "window_start": start,
                "window_end_inclusive": end, "requested_end_exclusive": end_exclusive,
                "retrieved_utc": retrieved, "yfinance_version": yf.__version__,
                "python_version": platform.python_version(), "auto_adjust": False,
                "actions": True, "rows": len(cal), "first_date": min(calendars[start], default=""),
                "last_date": max(calendars[start], default=""), "status": "ok",
            })
        except Exception as exc:  # calendar failures are recorded, never silently ignored
            calendars[start] = set()
            logs.append({
                "ticker": "SPY", "role": "calendar_only", "window_start": start,
                "window_end_inclusive": end, "requested_end_exclusive": end_exclusive,
                "retrieved_utc": retrieved, "yfinance_version": yf.__version__,
                "python_version": platform.python_version(), "auto_adjust": False,
                "actions": True, "rows": 0, "first_date": "", "last_date": "",
                "status": f"error:{type(exc).__name__}:{str(exc)[:180]}",
            })
        time.sleep(0.8)

    for ticker, event_day, start, end, effective in EVENTS:
        end_exclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        status = "ok"
        error = ""
        try:
            hist = yf.Ticker(ticker).history(
                start=start, end=end_exclusive, interval="1d",
                auto_adjust=False, actions=True,
            )
            hist.index = pd.to_datetime(hist.index).date
            if hist.empty:
                status = "no_rows"
                error = "Yahoo/yfinance returned no historical rows for requested window"
            elif hist.index.has_duplicates:
                status = "duplicate_dates"
            for date, r in hist.iterrows():
                rows.append({
                    "ticker": ticker, "event_day_zero": event_day,
                    "effective_date": effective, "window_start": start,
                    "window_end_inclusive": end, "date": date.isoformat(),
                    "open_raw": r.get("Open"), "high_raw": r.get("High"),
                    "low_raw": r.get("Low"), "close_raw": r.get("Close"),
                    "adj_close": r.get("Adj Close"), "volume_raw": r.get("Volume"),
                    "dividends": r.get("Dividends"), "stock_splits": r.get("Stock Splits"),
                })
            calendar = calendars.get(start, set())
            observed = {pd.Timestamp(x).date().isoformat() for x in hist.index}
            missing = sorted(calendar - observed)
            for date in missing:
                gaps.append({"ticker": ticker, "window_start": start,
                             "window_end_inclusive": end, "missing_session": date})
        except Exception as exc:
            hist = pd.DataFrame()
            error = f"{type(exc).__name__}:{str(exc)[:250]}"
            status = "download_error"
        if status == "ok" and len(hist) != len(calendars.get(start, set())):
            status = "partial_coverage"
        logs.append({
            "ticker": ticker, "role": "frozen_treated", "event_day_zero": event_day,
            "effective_date": effective, "window_start": start,
            "window_end_inclusive": end, "requested_end_exclusive": end_exclusive,
            "retrieved_utc": retrieved, "yfinance_version": yf.__version__,
            "python_version": platform.python_version(), "auto_adjust": False,
            "actions": True, "rows": len(hist),
            "first_date": min((pd.Timestamp(x).date().isoformat() for x in hist.index), default=""),
            "last_date": max((pd.Timestamp(x).date().isoformat() for x in hist.index), default=""),
            "missing_spy_sessions": len(calendar - {pd.Timestamp(x).date().isoformat() for x in hist.index}),
            "status": status, "error": error,
        })
        time.sleep(1.0)

    event_lookup = {ticker: (day0, start, end, eff) for ticker, day0, start, end, eff in EVENTS}
    candidate_rows: list[dict] = []
    candidate_logs: list[dict] = []
    candidate_gaps: list[dict] = []
    for treated, ticker in CANDIDATES:
        event_day, start, end, effective = event_lookup[treated]
        end_exclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        status = "ok"
        error = ""
        try:
            hist = yf.Ticker(ticker).history(
                start=start, end=end_exclusive, interval="1d",
                auto_adjust=False, actions=True,
            )
            hist.index = pd.to_datetime(hist.index).date
            if hist.empty:
                status = "no_rows"
                error = "Yahoo/yfinance returned no historical rows for requested window"
            elif hist.index.has_duplicates:
                status = "duplicate_dates"
            for date, r in hist.iterrows():
                candidate_rows.append({
                    "treated_ticker": treated, "ticker": ticker,
                    "event_day_zero": event_day, "effective_date": effective,
                    "window_start": start, "window_end_inclusive": end,
                    "date": date.isoformat(), "open_raw": r.get("Open"),
                    "high_raw": r.get("High"), "low_raw": r.get("Low"),
                    "close_raw": r.get("Close"), "adj_close": r.get("Adj Close"),
                    "volume_raw": r.get("Volume"), "dividends": r.get("Dividends"),
                    "stock_splits": r.get("Stock Splits"),
                    "evidence_status": "exploratory_price_only_not_donor_eligible",
                })
            calendar = calendars.get(start, set())
            observed = {pd.Timestamp(x).date().isoformat() for x in hist.index}
            missing = sorted(calendar - observed)
            for date in missing:
                candidate_gaps.append({"treated_ticker": treated, "ticker": ticker,
                                       "window_start": start, "window_end_inclusive": end,
                                       "missing_session": date})
        except Exception as exc:
            hist = pd.DataFrame()
            missing = sorted(calendars.get(start, set()))
            for date in missing:
                candidate_gaps.append({"treated_ticker": treated, "ticker": ticker,
                                       "window_start": start, "window_end_inclusive": end,
                                       "missing_session": date})
            error = f"{type(exc).__name__}:{str(exc)[:250]}"
            status = "download_error"
        if status == "ok" and len(hist) != len(calendars.get(start, set())):
            status = "partial_coverage"
        candidate_logs.append({
            "treated_ticker": treated, "ticker": ticker,
            "event_day_zero": event_day, "effective_date": effective,
            "window_start": start, "window_end_inclusive": end,
            "requested_end_exclusive": end_exclusive,
            "retrieved_utc": retrieved, "yfinance_version": yf.__version__,
            "python_version": platform.python_version(), "auto_adjust": False,
            "actions": True, "rows": len(hist),
            "first_date": min((pd.Timestamp(x).date().isoformat() for x in hist.index), default=""),
            "last_date": max((pd.Timestamp(x).date().isoformat() for x in hist.index), default=""),
            "missing_spy_sessions": len(missing), "price_coverage_status": status,
            "eligibility": "not_assessed", "error": error,
        })
        time.sleep(1.0)

    pd.DataFrame(rows).sort_values(["ticker", "date"]).to_csv(OUT / "treated_prices.csv", index=False)
    pd.DataFrame(spy_rows).sort_values(["window_start", "date"]).to_csv(OUT / "spy_market_prices.csv", index=False)
    pd.DataFrame(logs).to_csv(OUT / "retrieval_log.csv", index=False)
    pd.DataFrame(gaps, columns=["ticker", "window_start", "window_end_inclusive", "missing_session"]).to_csv(
        OUT / "missing_sessions.csv", index=False
    )
    pd.DataFrame(candidate_rows).sort_values(["treated_ticker", "ticker", "date"]).to_csv(
        OUT / "candidate_prices_exploratory.csv", index=False
    )
    pd.DataFrame(candidate_logs).to_csv(OUT / "candidate_price_coverage.csv", index=False)
    pd.DataFrame(candidate_gaps, columns=["treated_ticker", "ticker", "window_start",
        "window_end_inclusive", "missing_session"]).to_csv(OUT / "candidate_missing_sessions.csv", index=False)
    prices_df = pd.DataFrame(rows)
    quality: list[dict] = []
    for log in logs:
        if log.get("role") != "frozen_treated":
            continue
        ticker, start = log["ticker"], log["window_start"]
        subset = prices_df[(prices_df.ticker == ticker) & (prices_df.window_start == start)] if not prices_df.empty else pd.DataFrame()
        quality.append({
            "ticker": ticker, "window_start": start, "window_end_inclusive": log["window_end_inclusive"],
            "expected_spy_sessions": len(calendars.get(start, set())), "observed_rows": len(subset),
            "duplicate_dates": int(subset.date.duplicated().sum()) if len(subset) else "",
            "missing_close_raw": int(subset.close_raw.isna().sum()) if len(subset) else "",
            "missing_adj_close": int(subset.adj_close.isna().sum()) if len(subset) else "",
            "missing_volume_raw": int(subset.volume_raw.isna().sum()) if len(subset) else "",
            "dividend_event_rows": int((pd.to_numeric(subset.dividends, errors="coerce").fillna(0) != 0).sum()) if len(subset) else "",
            "split_event_rows": int((pd.to_numeric(subset.stock_splits, errors="coerce").fillna(0) != 0).sum()) if len(subset) else "",
            "price_coverage_status": log["status"], "retrieved_utc": retrieved,
        })
    pd.DataFrame(quality).to_csv(OUT / "data_quality.csv", index=False)
    manifest = {
        "retrieved_utc": retrieved, "python_version": platform.python_version(),
        "yfinance_version": yf.__version__, "interval": "1d",
        "auto_adjust": False, "actions": True,
        "requested_end": "exclusive; CSV report stores inclusive requested window",
        "calendar": "SPY observed sessions per date range; missingness check only",
        "scope": "frozen treated roster plus price-only research leads; no donor eligibility implied",
        "tickers": [e[0] for e in EVENTS],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out_dir": str(OUT), "retrieved_utc": retrieved,
        "rows": len(rows), "statuses": {x["ticker"]: x["status"] for x in logs if x["role"] == "frozen_treated"},
        "candidate_price_leads": len(candidate_rows),
        "candidate_statuses": {x["ticker"]: x["price_coverage_status"] for x in candidate_logs},
        "yfinance_version": yf.__version__, "missing_session_rows": len(gaps),
    }, indent=2))

if __name__ == "__main__":
    main()

