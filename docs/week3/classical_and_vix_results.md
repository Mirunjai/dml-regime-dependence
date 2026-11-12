# Week 3 Classical Event Study and VIX Results

## Classical market-model estimates

The saved `results/benchmarks/week3_classical_event_study.csv` contains seven firms. Each market-model regression uses 220 estimation observations from trading sessions -250 through -31. The primary CAR is the three-session window [-1,+1]; the short and wide windows are [0,+1] and [-5,+5].

| Firm | Day zero | Primary CAR [-1,+1] | Short CAR [0,+1] | Wide CAR [-5,+5] |
|---|---|---:|---:|---:|
| CRM | 2008-09-10 | +6.92% | +8.10% | +5.88% |
| FAST | 2008-09-10 | +4.03% | +0.63% | +14.24% |
| ADS | 2013-12-11 | +1.08% | +0.39% | +3.14% |
| MHK | 2013-12-11 | +0.87% | +2.01% | +4.19% |
| SWKS | 2015-03-09 | +3.98% | +2.42% | +8.82% |
| ETSY | 2020-09-08 | -2.40% | +0.70% | -7.91% |
| TER | 2020-09-08 | -4.73% | -1.51% | -7.92% |

These are point estimates, not statistical significance tests. The CSV does not report CAR standard errors or confidence intervals. Firms announced together share an event shock and must not be counted as independent event replications. Window sensitivity is visible in the differing CARs, especially for FAST and ETSY. No causal conclusion follows from these descriptive estimates alone.

CTLT is absent because its historical adjusted-price series was unavailable in the working data, as stated by the benchmark runner. No value is imputed.

## VIX regime labels

The saved `results/benchmarks/week3_regime_labels.csv` applies the generator's trailing 20-session VIX average and event-specific five-year reference thresholds, with data strictly before the announcement cutoff. The thresholds use the 25th and 75th percentiles of eligible historical rolling averages. Firms in the same announcement cluster receive the same label.

| Announcement cluster | Pre-event VIX20 | Historical p25 | Historical p75 | Label |
|---|---:|---:|---:|---|
| 2008-09-09 | 20.926 | 12.560 | 17.797 | Turbulent |
| 2013-12-11 | 13.337 | 16.485 | 25.289 | Calm |
| 2015-03-09 | 15.030 | 14.353 | 19.924 | Mixed |
| 2020-09-04 | 23.664 | 12.646 | 18.634 | Turbulent |

Labels are relative to each event's historical reference distribution; they are not fixed VIX regimes. They are descriptive classifications and do not identify causal effects. Alternative reference lengths or windows could change the labels.

## Reproducibility status

Scripts: `src/benchmarks/run_week3_classical.py`, `src/real_data/generate_regime_labels.py`. Outputs: the two CSVs above. Window definitions are recorded in `results/benchmarks/week3_benchmark_windows.csv`.

The branch does not track `data/raw/week3_adjusted_prices.csv`, and the VIX history's download date/source snapshot is not encoded in the output table. A clean checkout therefore cannot regenerate these outputs byte-for-byte from tracked inputs alone. Preserve the authorized input data or its documented retrieval procedure, record retrieval date and package versions, and regenerate in the actual checkout before making a strong reproducibility claim.
