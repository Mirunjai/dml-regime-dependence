# Week 3 Synthetic Control Donor Screening: Status and Evidence Gaps

## Decision as of 2026-11-11

The team lead has approved the remaining post-November 8 SCM work conditionally: screening and validated data must precede execution; no scope expansion is authorized. This is permission to proceed once gates pass, not permission to bypass them.

No donor is certified eligible and no empirical donor pool is frozen. The tracked `week3_donor_candidates.csv` is a schema template with seven treated-firm rows and no donor evidence. The validator requires security type, US domicile, point-in-time S&P 500 status and source, industry, date-specific market capitalization, beta and estimation window, liquidity, pre-event return correlation, price coverage, adjustment method, and contamination evidence. Those fields are not available from the checked-in files.

The branch does not contain `data/raw/week3_adjusted_prices.csv` or any donor-price panel. The terminal transcript reports that the user's working copy had the treated/index price file but no donor-price file, and the download-input CSV was empty. Consequently, we cannot compute pre-event return correlation, beta, dollar volume, or pre-event RMSPE here. A missing observation in the community membership history is not proof of nonmembership or tradability. Do not mark any proposed name eligible from that source alone.

## Preliminary research leads (not donor nominations)

These names are leads from the existing research notes only. They are not screened, have no point-in-time eligibility finding, and must not be downloaded into the benchmark input until listing dates, historical security identity, index membership, industry and contamination are checked.

| Treated firm | Date | Research lead(s) from notes | Why investigated | Status |
|---|---|---|---|---|
| CRM | 2008-09-09 announcement | NOW, WDAY | Enterprise software comparison | Pending; notes already flag they were not public in 2008, so exclude for this event unless primary listing evidence disproves that chronology |
| FAST | 2008-09-09 | GWW, MSM | Industrial distribution | Pending; verify common-stock identity, membership, industry and all dated metrics |
| ADS | 2013-12-11 | SYF, COF | Consumer finance / payments | Pending; verify security/listing history, index status and comparability |
| MHK | 2013-12-11 | TILE, LEG | Flooring / furnishings | Pending; verify security/listing history, index status and comparability |
| SWKS | 2015-03-09 | QRVO, CRUS | Semiconductor components | Pending; notes flag QRVO ticker did not exist under that identity in March 2015; verify and exclude if confirmed |
| ETSY | 2020-09-04 | EBAY, SHOP | E-commerce | Pending; verify point-in-time membership and contamination; SHOP must be checked against its IPO date |
| TER | 2020-09-04 | COHU, FORM | Semiconductor test equipment | Pending; verify point-in-time membership and contamination |

The lead rationale is a search queue, not evidence of industry equivalence. The date and issuer checks must use dated primary or archival sources. Market cap, beta, liquidity, returns, and price adjustments must be measured using information and data available before the relevant announcement, with the precise lookback window and provider recorded.

## Event timing and contamination

The treated events are announcement clusters, with effective dates later: CRM/FAST (2008-09-09 / 2008-09-12), ADS/MHK (2013-12-11 / 2013-12-20), SWKS (2015-03-09 / 2015-03-11), and ETSY/TER/CTLT (2020-09-04 / 2020-09-21). Screen to the announcement information cutoff and preserve the separate trading-session day-zero convention in `week3_event_day_zero.csv`.

Exclude other treated firms and firms exposed to the same announcement or a material confounding event during the estimation/event/post windows, unless the frozen protocol explicitly defines another treatment. Record the event, date range, source, and decision. Do not use post-announcement characteristics to choose donors.

## Required completion sequence

1. Obtain an archival US common-stock universe and point-in-time identifiers/ticker histories for each event period.
2. Exclude treated units, units without full aligned pre/post price coverage, and any units with same-event or material-window contamination.
3. Check dated S&P 500 membership using an authoritative dated source where possible. The checked-in community snapshots are preliminary screens only; nearest prior snapshots were 1 day before the 2008 and 2013 announcements, 6 days before 2015, and 74 days before 2020 (as reported in the attached terminal transcript). These observations do not establish completeness or nonmembership.
4. For surviving candidates, record industry, market capitalization, beta, median dollar volume and pre-event return correlation, with definitions, windows, data source, retrieval date, and currency/adjustment conventions.
5. Run `python -m src.real_data.validate_week3_donors`; resolve all missing evidence. Only an independent reviewer should change a row to `eligible`.
6. Freeze the eligible pool and date-aligned panel before any approved benchmark run. Keep a copy/hash of the frozen inputs.

## Catalent (CTLT)

CTLT is excluded from the existing classical event-study output because its historical adjusted-price series is unavailable in the working data, as explicitly reported by `run_week3_classical.py`. One alternative-source attempt was made on 2026-11-11: Quiver's public CTLT historical page states that adjusted close includes splits and dividends, and advertises daily history back to 2014, which covers this event. However, the page exposes only a short current-date slice here; its API requires a key, and no downloadable event-window panel or source approval for project use is available in this workspace. Thus no price file was obtained or validated. Treat CTLT as missing and exclude it from the complete-case SCM unless the approved source provides a complete, documented series consistent with the other panel prices. Do not treat it as zero, impute it, or infer an effect. Source: https://www.quiverquant.com/stock/CTLT/historical-prices/ .

## SCM methods and limits

The helper `src/benchmarks/synthetic_control.py` estimates nonnegative weights summing to one by minimizing pre-period mean squared outcome error. It reports weights, pre-period RMSPE, post gaps, and weight concentration diagnostics. It does not select donors or predictor weights, define time windows, run in-space or in-time placebos, calculate placebo p-values, or provide confidence intervals. These omissions are deliberate; choices must be frozen before outcome inspection.

Report fit and weight concentration alongside gaps. A good pre-fit does not prove the no-interference/no-confounding assumptions. Placebo comparisons require a credible exchangeable donor pool and careful treatment of poor-fitting placebo units; a placebo rank is not a conventional randomized-experiment p-value. The benchmark is descriptive/contextual and cannot establish the project's primary DML coverage claim.

Primary methods references: Abadie, Diamond & Hainmueller (2010), https://doi.org/10.1198/jasa.2009.ap08746; Abadie (2021), “Using Synthetic Controls: Feasibility, Data Requirements, and Methodological Aspects,” https://economics.mit.edu/sites/default/files/publications/jel.20191450.pdf.

## Approval gate

The team lead's explicit approval was received on 2026-11-11, conditional on donor screening and price validation. Do not invoke the SCM benchmark or report post-November 8 SCM results until both prerequisites are satisfied.