# Week 3: Classical Event-Study Benchmark — Methods

## 1. Objective

The classical event-study benchmark estimates stock-return movements around selected corporate events using a market-model approach. It provides a conventional benchmark for comparison with subsequent causal machine-learning methods.

The benchmark measures cumulative abnormal returns (CARs) around event announcements. These estimates are descriptive and should not be interpreted as identified causal effects without additional assumptions.

## 2. Data

The analysis uses historical adjusted stock prices and S&P 500 index observations, with the S&P 500 (`^GSPC`) serving as the market benchmark.

The implemented benchmark includes seven firms: CRM, FAST, ADS, MHK, SWKS, ETSY, and TER.

CTLT is excluded because the required historical price observations were unavailable in the prepared dataset.

Stock and market returns are calculated from consecutive adjusted price observations.

## 3. Event-Day Definition

The analysis uses the event-day-zero mapping recorded in `data/processed/week3_event_day_zero.csv`.

For announcements occurring after the market closes, event day zero is assigned to the next eligible trading session. For announcements occurring before market opening, the announcement trading session is used.

The event-study analysis uses announcement-related trading dates rather than index inclusion effective dates.

## 4. Estimation Window

The market model is estimated over trading sessions −250 through −31 relative to event day zero.

The model is:

R_it = α_i + β_i R_mt + ε_it

where:

- R_it is the return of firm i on trading session t.
- R_mt is the market benchmark return.
- α_i is the estimated intercept.
- β_i is the estimated market sensitivity.
- ε_it is the residual return.

The estimation period is separated from the event window to reduce contamination from announcement-related returns.

## 5. Abnormal Returns

Expected stock returns are calculated from the estimated market model.

Abnormal return is defined as:

AR_it = R_it − (α̂_i + β̂_i R_mt)

Cumulative abnormal return is calculated by summing abnormal returns across the selected event window:

CAR_i = Σ AR_it

## 6. Event Windows

Three event windows are evaluated:

| Window | Trading sessions | Purpose |
|---|---|---|
| Primary | −1 to +1 | Main announcement-period benchmark |
| Short | 0 to +1 | Immediate announcement response |
| Wide | −5 to +5 | Broader surrounding return movement |

The market model is fitted using the same estimation-window definition for all three CAR calculations.

## 7. Benchmark Output

For each firm, the implementation records:

- Event day zero
- Primary, short, and wide CAR
- Estimated market-model intercept
- Estimated market-model beta
- Number of estimation observations

The output is stored in:

`results/benchmarks/week3_classical_event_study.csv`

## 8. Limitations

The classical event study relies on the selected market model to estimate expected returns.

Abnormal returns may reflect other contemporaneous information or omitted factors rather than only the studied event.

The sample contains a limited number of firms and announcement clusters. Firms exposed to the same announcement or market-wide shock should not automatically be treated as independent observations.

Historical ticker continuity and price-adjustment conventions require careful interpretation.

The benchmark does not by itself establish DML confidence-interval coverage or the validity of causal inference.

## 9. Reproducibility

Runner: `src/benchmarks/run_week3_classical.py`

Market-model implementation: `src/benchmarks/event_study.py`

Price input: `data/raw/week3_adjusted_prices.csv`

Event-date input: `data/processed/week3_event_day_zero.csv`

Output: `results/benchmarks/week3_classical_event_study.csv`

Execution command:

`python -m src.benchmarks.run_week3_classical`

## 10. Conclusion

The classical event-study benchmark provides a reproducible baseline for examining announcement-period abnormal returns. It complements the VIX market-regime classification and provides a reference point for later Synthetic Control and DML comparisons, subject to their respective identification assumptions and data requirements.