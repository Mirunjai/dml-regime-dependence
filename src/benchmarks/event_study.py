
"""Descriptive market-model OLS abnormal returns, without inferential intervals.

Returns must be aligned, in the same units and use the same return convention.
CAR is the arithmetic sum of abnormal returns, not a compounded buy/hold return.
See MacKinlay (1997), Event Studies in Economics and Finance, Sections 3-4.
"""

import numpy as np
import pandas as pd


def market_model_event_study(
    stock_returns,
    market_returns,
    estimation_end,
    event_start,
    event_end,
):
    """
    Estimate market-model abnormal and cumulative abnormal returns.

    The estimation window is [0, estimation_end).
    The event window is [event_start, event_end], inclusive.
    """
    stock = np.asarray(stock_returns, dtype=float)
    market = np.asarray(market_returns, dtype=float)

    if stock.ndim != 1 or market.ndim != 1:
        raise ValueError("Returns must be one-dimensional")

    if len(stock) != len(market):
        raise ValueError("Stock and market lengths must match")

    if not np.all(np.isfinite(stock)) or not np.all(np.isfinite(market)):
        raise ValueError("Returns must contain only finite values")

    for value in (estimation_end, event_start, event_end):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
            raise ValueError("Window indices must be integers")

    if not (2 <= estimation_end <= event_start <= event_end < len(stock)):
        raise ValueError("Invalid estimation or event window")

    # Estimate alpha and beta from the pre-event period.
    x = market[:estimation_end]
    y = stock[:estimation_end]

    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            market_variance = np.var(x)
            if market_variance == 0:
                raise ValueError("Market returns have zero estimation variance")
            beta = np.cov(x, y, ddof=0)[0, 1] / market_variance
            alpha = y.mean() - beta * x.mean()
            event_slice = slice(event_start, event_end + 1)
            abnormal_returns = stock[event_slice] - (alpha + beta * market[event_slice])
            cumulative_abnormal_returns = np.cumsum(abnormal_returns)
    except FloatingPointError as exc:
        raise ValueError("Market-model calculation is not representable in float64") from exc
    if (not np.isfinite([alpha, beta]).all() or not np.isfinite(abnormal_returns).all()
            or not np.isfinite(cumulative_abnormal_returns).all()):
        raise ValueError("Nonfinite market-model output")

    return {
        "alpha": float(alpha),
        "beta": float(beta),
        "abnormal_returns": abnormal_returns,
        "cumulative_abnormal_returns": cumulative_abnormal_returns,
        "car": float(cumulative_abnormal_returns[-1]),
    }


def main():
    """Run a reproducible toy event-study demonstration."""
    rng = np.random.default_rng(42)

    n_periods = 250

    # Simulated daily market returns.
    market_returns = rng.normal(
        loc=0.0005,
        scale=0.01,
        size=n_periods,
    )

    # Simulated company returns following a market model.
    stock_returns = (
        0.0002
        + 1.2 * market_returns
        + rng.normal(0, 0.005, n_periods)
    )

    # Introduce a known positive event effect for six periods.
    stock_returns[200:206] += 0.02

    results = market_model_event_study(
        stock_returns=stock_returns,
        market_returns=market_returns,
        estimation_end=180,
        event_start=200,
        event_end=205,
    )

    print("\nCLASSICAL EVENT-STUDY PROTOTYPE")
    print("-" * 55)

    print(f"Estimated alpha: {results['alpha']:.6f}")
    print(f"Estimated beta:  {results['beta']:.4f}")

    print("\nAbnormal returns:")
    print(results["abnormal_returns"])

    print("\nCumulative abnormal returns:")
    print(results["cumulative_abnormal_returns"])

    print(f"\nFinal CAR: {results['car']:.6f}")

    print("\nExpected injected event effect: approximately 0.12")
    print("Note: CAR differs slightly because of random noise.")


if __name__ == "__main__":
    main()


def adjusted_prices_to_returns(
    prices: pd.DataFrame,
    *,
    date_column: str = "Date",
) -> pd.DataFrame:
    """Convert an adjusted-price panel to simple returns without filling gaps.

    ``prices`` may have dates in a column or in its index. Missing prices remain
    missing in the resulting returns; there is no forward filling or imputation.
    """
    frame = prices.copy()
    if date_column in frame.columns:
        frame[date_column] = pd.to_datetime(frame[date_column], errors="raise")
        frame = frame.set_index(date_column)
    else:
        frame.index = pd.to_datetime(frame.index, errors="raise")
    if frame.index.has_duplicates:
        raise ValueError("Price panel contains duplicate dates")
    frame = frame.sort_index()
    frame.index.name = "Date"
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    return numeric.pct_change(fill_method=None)


def estimate_market_model_event_study(
    returns: pd.DataFrame,
    *,
    stock_ticker: str,
    market_ticker: str,
    event_session: str | pd.Timestamp,
    estimation_window: tuple[int, int],
    event_window: tuple[int, int],
) -> dict[str, object]:
    """Estimate a market-model event study on a dated return panel.

    Windows are inclusive trading-session offsets from ``event_session``. For
    example, ``(-250, -30)`` means estimation sessions 250 through 30 before
    the anchor. No window values are supplied by default: they are design
    decisions, not hidden implementation choices.

    ``event_session`` must be the trading session chosen by the frozen event
    timing convention. In particular, an announcement/effective change after
    the close may have its first affected return on the next trading session.
    The returned CAR is descriptive; no inferential test is imposed here.
    """
    if stock_ticker not in returns or market_ticker not in returns:
        missing = [c for c in (stock_ticker, market_ticker) if c not in returns]
        raise KeyError(f"Return panel is missing columns: {', '.join(missing)}")
    if len(estimation_window) != 2 or len(event_window) != 2:
        raise ValueError("Windows must be (start_offset, end_offset) pairs")
    est_start, est_end = map(int, estimation_window)
    evt_start, evt_end = map(int, event_window)
    if est_start > est_end or evt_start > evt_end or est_end >= evt_start:
        raise ValueError("Windows must be ordered and non-overlapping")

    frame = returns[[stock_ticker, market_ticker]].copy()
    frame.index = pd.to_datetime(frame.index, errors="raise").normalize()
    frame = frame.sort_index()
    if frame.index.has_duplicates:
        raise ValueError("Return panel contains duplicate dates")
    anchor = pd.Timestamp(event_session).normalize()
    position = frame.index.get_indexer([anchor])[0]
    if position < 0:
        raise ValueError(f"Event session {anchor.date()} is not in the return panel")

    est_lo, est_hi = position + est_start, position + est_end
    evt_lo, evt_hi = position + evt_start, position + evt_end
    if est_lo < 0 or evt_lo < 0 or est_hi >= len(frame) or evt_hi >= len(frame):
        raise ValueError("Requested windows extend beyond available return dates")
    estimation = frame.iloc[est_lo : est_hi + 1]
    event = frame.iloc[evt_lo : evt_hi + 1]
    if estimation.isna().any().any() or event.isna().any().any():
        raise ValueError("Selected estimation/event windows contain missing returns")

    x = estimation[market_ticker].to_numpy(dtype=float)
    y = estimation[stock_ticker].to_numpy(dtype=float)
    if len(x) < 3:
        raise ValueError("Estimation window must contain at least three sessions")
    design = np.column_stack((np.ones(x.size), x))
    if np.linalg.matrix_rank(design) < 2:
        raise ValueError("Market returns have zero estimation variation")
    alpha, beta = np.linalg.lstsq(design, y, rcond=None)[0]

    event_market = event[market_ticker].to_numpy(dtype=float)
    abnormal = event[stock_ticker].to_numpy(dtype=float) - (alpha + beta * event_market)
    ar = pd.Series(abnormal, index=event.index, name="abnormal_return")
    car = ar.cumsum().rename("cumulative_abnormal_return")
    return {
        "ticker": stock_ticker,
        "market_ticker": market_ticker,
        "event_session": anchor,
        "estimation_dates": estimation.index,
        "event_dates": event.index,
        "alpha": float(alpha),
        "beta": float(beta),
        "estimation_observations": int(len(estimation)),
        "abnormal_returns": ar,
        "cumulative_abnormal_returns": car,
        "car": float(car.iloc[-1]),
    }
