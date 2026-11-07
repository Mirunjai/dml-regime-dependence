
"""Descriptive market-model OLS abnormal returns, without inferential intervals.

Returns must be aligned, in the same units and use the same return convention.
CAR is the arithmetic sum of abnormal returns, not a compounded buy/hold return.
See MacKinlay (1997), Event Studies in Economics and Finance, Sections 3-4.
"""

import numpy as np


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
