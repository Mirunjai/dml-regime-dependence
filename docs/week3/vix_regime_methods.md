# Week 3: VIX Market Regime Classification — Methods

## 1. Objective

Market volatility conditions may influence financial event-study outcomes and the behavior of statistical inference procedures. To account for differences in market environments, the benchmark assigns each event to a volatility regime using the CBOE Volatility Index (VIX).

The regime classification is designed to use only information available before the event announcement, thereby avoiding look-ahead bias.

## 2. Data and Event Timing

Daily VIX observations are used to construct historical volatility measures.

For each event, the announcement date is used as the information cutoff. VIX observations on the announcement date or afterward are excluded from the classification procedure.

This is distinct from the event-study trading-day-zero convention, which may assign the following trading session as day zero for announcements released after market close.

## 3. Pre-Event VIX Measure

For each event, the pre-event volatility measure is calculated as the arithmetic mean of the most recent 20 available VIX trading-session observations strictly preceding the announcement date.

This provides a short-term measure of the market's prevailing volatility environment.

## 4. Historical Reference Distribution

A historical reference distribution is constructed from rolling 20-session VIX averages.

In the trailing-reference configuration, only historical observations within the preceding five years and strictly before the announcement date are eligible.

The latest rolling window is reserved as the event's pre-announcement VIX measure. Earlier rolling windows are used to calculate the reference distribution.

The 25th and 75th percentiles of this reference distribution serve as regime classification thresholds.

## 5. Regime Assignment

Each event is assigned to one of three categories:

- **Calm:** Pre-event VIX average is below the historical 25th percentile.
- **Mixed:** Pre-event VIX average is between the 25th and 75th percentiles, inclusive.
- **Turbulent:** Pre-event VIX average exceeds the historical 75th percentile.

These classifications are relative to the event's historical reference period rather than fixed numerical VIX thresholds.

## 6. Leakage Prevention

The implementation applies the following safeguards:

- Excludes announcement-day and post-announcement VIX observations.
- Computes event-specific thresholds from eligible historical observations.
- Excludes the event's latest rolling window from the percentile reference distribution.
- Validates the VIX time series for duplicate dates, missing or nonfinite observations, and nonpositive values.
- Marks events with insufficient historical observations rather than assigning an unsupported regime.

These safeguards reduce the risk of look-ahead bias in the regime-labeling stage.

## 7. Limitations

VIX is a market-wide volatility indicator rather than a firm-specific measure of risk.

Regime labels depend on the selected historical reference length and rolling-window size.

Events sharing the same announcement date may receive identical market-regime labels. Such events should not automatically be treated as statistically independent observations.

The regime labels are descriptive classifications and do not independently identify causal effects.

## 8. Implementation and Reproducibility

Implementation: `src/real_data/regime_labels.py`

Generation script: `src/real_data/generate_regime_labels.py`

VIX input: `data/processed/vix_history.csv`

Benchmark output: `results/benchmarks/week3_regime_labels.csv`

The reported results should be generated using the approved trailing-five-year reference configuration.