# Free Historical Data Source Coverage Matrix

**Review date:** 2026-11-11  
**Scope:** frozen Week 3 S&P 500 addition events only. No dataset was purchased and no Synthetic Control benchmark was run.

## Decision status

The free-source review is not sufficient to admit a donor pool or run SCM. The repository price diagnostics show historical rows for six of the seven treated firms, with CTLT missing. They do not document a complete, sourced donor panel. The repository donor screening template is blank. The committed membership file's provenance is not recorded, and the available snapshot evidence is stale for the September 2020 events. SEC point-in-time evidence has been demonstrated for one 2008 issuer only.

The public GitHub membership history is a useful free lead for event-date reconstruction. Its year coverage includes all five event periods, but it is a community-maintained reconstruction, not official S&P evidence. Each candidate's event-date status still needs corroboration against dated S&P announcements or another defensible contemporaneous record.

## Locked events and price-window coverage

The event dates below are from `week3_benchmark_candidates.csv` and `week3_event_day_zero.csv`. The documented target price windows in the prior Week 3 work span approximately the pre-event fitting, validation, and post-event periods; frozen specifications remain fit [-252, -21], validation [-20, -1], primary post [0, +20], and extended post [0, +60].

| Cluster / treated ticker | Announcement | Event day zero | Effective date | Existing local price diagnostics | Free-source status |
|---|---:|---:|---:|---|---|
| CRM | 2008-09-09 | 2008-09-10 | 2008-09-12 | 3,525 rows; 2007-01-03–2020-12-31 | Contains the full event windows. Provider extraction provenance is not present in the committed diagnostics. |
| FAST | 2008-09-09 | 2008-09-10 | 2008-09-12 | 3,525 rows; 2007-01-03–2020-12-31 | Contains the full event windows. Provider extraction provenance is not present in the committed diagnostics. |
| ADS | 2013-12-11 | 2013-12-11 | 2013-12-20 | 3,525 rows; 2007-01-03–2020-12-31 | Contains the event windows in the existing local diagnostics; ADS later delisted, so do not infer Yahoo coverage for other delisted donors from this one file. |
| MHK | 2013-12-11 | 2013-12-11 | 2013-12-20 | 3,525 rows; 2007-01-03–2020-12-31 | Contains the full event windows. Provider extraction provenance is not present in the committed diagnostics. |
| SWKS | 2015-03-09 | 2015-03-09 | 2015-03-11 | 3,525 rows; 2007-01-03–2020-12-31 | Contains the full event windows. Provider extraction provenance is not present in the committed diagnostics. |
| ETSY | 2020-09-04 | 2020-09-08 | 2020-09-21 | 1,440 rows; 2015-04-16–2020-12-31 | IPO history starts in 2015, but includes the event windows. |
| TER | 2020-09-04 | 2020-09-08 | 2020-09-21 | 3,525 rows; 2007-01-03–2020-12-31 | Contains the full event windows. Provider extraction provenance is not present in the committed diagnostics. |
| CTLT | 2020-09-04 | 2020-09-08 | 2020-09-21 | 0 rows; no first/last price date | Missing. Keep as a missing-data case unless a reliable, comparable adjusted series is obtained. |

The source for those observation counts is the branch's `data/processed/week3_price_diagnostics.csv`. The data itself is not present in the branch's raw-data directory, and the committed diagnostics do not identify the downloader, exact Yahoo query, retrieval timestamp, or adjustment checks. The terminal transcript supplied earlier showed one local `week3_adjusted_prices.csv`, but that is not a reproducible, branch-tracked donor dataset. Thus this table reports existing observed coverage, not certification that Yahoo is a suitable uniform source.

## Source-by-source coverage

| Source | Event-period coverage | Company coverage actually established | What it can support | Gaps / decision |
|---|---|---|---|---|
| Yahoo Finance historical prices | Existing diagnostics span the needed 2008–2020 windows for six treated firms. | Six treated tickers have rows in the existing diagnostics; CTLT has none. No systematic potential-donor or delisted-donor panel has been saved or audited. | Free candidate price source for currently available histories; existing data suggests useful event-window coverage for six treated tickers. | Not sufficient for the donor universe. Yahoo's own help page describes data as informational; export availability varies by instrument, and the repository contains no dated reproducible export log or verified adjustment comparison. ADS's existing rows do not establish reliable coverage for all delisted symbols. Keep CTLT excluded from any complete-case benchmark. |
| GitHub historical S&P 500 membership, fja05680/sp500 | The public lifecycle file is described as covering S&P 500 history from 1996 onward, so its nominal date span includes 2008-09, 2013-12, 2015-03, and 2020-09. | Date-year coverage exists for every event cluster; exact candidate donor membership has not been screened against this source. | Free point-in-time membership candidate list and reconstruction aid, with dated changes and ticker lifecycle records. | Maintainer states the baseline was obtained from a book-associated file through 2019 and later changes were manually maintained using Wikipedia/searches. It is not an official S&P feed. Reconcile each required date and ticker identity against dated S&P announcements. The repo's `sp500_membership_history.csv` currently has no cited source/version in the audit record; the prior terminal check found a preceding snapshot 1 day before 2008 and 2013 events, 6 days before SWKS, and 74 days before 2020-09-04. That 2020 snapshot cannot certify September membership. |
| SEC EDGAR filings and data | Filings exist across all five periods; the structured Company Facts data series is not a complete source for the 2008 event, so inspect original filings for 2008. | Evidence sampled for CRM only: a 2008 SEC filing reports about 120.1 million shares outstanding as of 2008-04-30. A filing detail page filed 2008-08-20 reports SIC 7372, but that filing is after the 2008 pre-event information cutoff and must not be used for that event. Full contemporaneous SIC and share-count extraction is not yet done for CRM/FAST, ADS/MHK, SWKS, ETSY/TER, or any donors. | Point-in-time SIC proxy from the latest eligible SEC filing header; shares outstanding from the latest eligible pre-cutoff filing. For 2008, original filings and filing index/header evidence are available. | SEC supplies no historical adjusted daily prices, beta, or liquidity. Shares counts need stock-split alignment through the cutoff and a price from the approved price source to calculate cap. Do not use a filing submitted after the applicable information cutoff. |
| HistoricalData.net free stock sample | Only July–December 2022 (127 trading dates; TWTR ends 2022-10-27); it overlaps none of the project event windows. | Sample tickers are TSLA, KO, SPY, TWTR. It includes no treated firm and no selected donor. | Inspect CSV schema and adjustment conventions, including a split, dividends, and a delisted series. Provider's page exposes representative real rows and all column definitions. | The sample cannot prove project-company coverage. A binary ZIP download was attempted but this environment could not resolve the provider hostname; the browser handoff also could not safely determine the current browser URL. The sample inspection below is from the provider's published page, not a locally downloaded ZIP. |
| HistoricalData.net paid daily archive (fallback only) | Provider advertises daily archive dates from 2003-10-01 through 2026-11-06, which spans all project periods. | Provider says stock history includes active and delisted names, but security-specific dates vary. No coverage lookup for CRM, FAST, ADS, MHK, SWKS, ETSY, TER, CTLT or donors was completed; therefore individual missing coverage remains unknown. | If approved later, one-time single-user daily archive is USD $199, includes two months of updates, and contains raw and split/dividend-adjusted series in per-security CSVs. | Do not purchase at this stage. Before any final purchase decision, obtain the provider's security-by-security coverage lookup for all treated firms and a pre-screened donor list, verify CTLT, and confirm project-use license terms. No security-specific missing-data rate can currently be stated. |

### SEC point-in-time sample

For the CRM event, day zero is 2008-09-10. The frozen pre-event fitting/validation cutoff at event day -21 is 2008-08-11. Salesforce's 10-Q for the quarter ended 2008-04-30 states approximately 120.1 million common shares outstanding as of 2008-04-30; the report was filed before that cutoff. This is a usable share-count observation subject to checking for any subsequent share issuance/split and documenting its availability date. The SEC filing detail page for an 8-K filed 2008-08-20 displays SIC 7372, but because it was filed after 2008-08-11 it is not eligible for this event's point-in-time classification. Use the latest filing detail/header published on or before the cutoff instead. No market capitalization is calculated here because the cutoff-date price series and split alignment have not been validated.

For all event periods, apply the same rule: SIC and shares must come from the latest information publicly filed on or before the relevant pre-event cutoff. Treat SIC as the agreed proxy for industry. Use the pre-cutoff shares count aligned for corporate actions through cutoff, multiplied by the matching provider's cutoff-date close, only after the price source is approved.

## HistoricalData.net sample inspection (published sample rows)

The provider's sample page describes eight stock CSVs: daily and 1-minute files for TSLA, KO, SPY, and TWTR. Daily files have 17 fields: `date, open, high, low, close, volume, vwap, transactions, adj_open, adj_high, adj_low, adj_close, adj_volume, adj_vwap, dividend, dividend_type, split`. Daily rows use US Eastern dates. Empty fields are blank, not zero.

A published TSLA sample around the 2022-08-25 3-for-1 split shows:

| Date | Raw close | Adjusted close | Split |
|---|---:|---:|---|
| 2022-08-24 | 891.29 | 297.0967 | |
| 2022-08-25 | 296.07 | 296.07 | 1:3 |
| 2022-08-26 | 288.09 | 288.09 | |

The provider says the per-security `adj_*` fields adjust historical rows for later split and cash-distribution events; there is no fixed adjustment base date, and an event does not adjust its own effective-date row. This backward-adjusted convention differs from a point-in-time raw daily cross-section, whose adjusted fields equal raw values. The provider's sample includes KO dividend rows and a TWTR series ending before the rest of the sample continues, demonstrating the distribution and delisting file conventions. Its verifier checks file integrity, schema, and adjustment calculations. These provider-published sample rows and checks are useful to assess format, but do not validate the full paid archive or coverage of project tickers.

## Reproducibility and next gate

Before donor screening can be called complete, the project needs: (1) a versioned, sourced membership file with event-date identity checks; (2) a saved, uniformly adjusted price panel for treated firms and each candidate donor over the required windows; (3) a saved company/date coverage report and adjustment/corporate-action checks; (4) SEC filing accession, filing date, SIC, shares, and split-alignment evidence at the same cutoff for treated firms and donors; (5) screening records for industry, market cap, beta, liquidity, pre-event returns, and contamination.

Until those records are complete and reviewed, CTLT remains excluded from the primary complete-case set, the donor pool remains unapproved, no source purchase is authorized, and Synthetic Control remains blocked. Do not expand the frozen firms, criteria, or event windows.

## References

- Project event and price coverage inputs: [Week 3 candidates](../../data/processed/week3_benchmark_candidates.csv), [event day zero](../../data/processed/week3_event_day_zero.csv), [price diagnostics](../../data/processed/week3_price_diagnostics.csv), [donor template](../../data/processed/week3_donor_candidates.csv).
- GitHub membership reconstruction: [fja05680/sp500](https://github.com/fja05680/sp500), [ticker lifecycle file](https://github.com/fja05680/sp500/blob/master/sp500_ticker_start_end.csv), [maintainer's notes on source and updates](https://github.com/damschroder/sp500-components#notes).
- Yahoo: [CRM history page](https://finance.yahoo.com/quote/CRM/history/), [Yahoo data-provider note](https://help.yahoo.com/kb/SLN2310.html).
- SEC: [CRM 2008 Q2 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1108524/000119312508121851/d10q.htm), [CRM 2008-08-20 filing detail (SIC 7372)](https://www.sec.gov/Archives/edgar/data/1108524/000119312508181542/0001193125-08-181542-index.html), [SEC EDGAR APIs](https://www.sec.gov/edgar/sec-api-documentation).
- HistoricalData.net: [free sample page](https://historicaldata.net/samples.html), [sample stock rows and field definitions](https://historicaldata.net/stocks.html), [adjustment methodology](https://historicaldata.net/methodology.html), [daily archive price and coverage notes](https://historicaldata.net/stocks.html), [FAQ and license/pricing](https://historicaldata.net/faq.html).
