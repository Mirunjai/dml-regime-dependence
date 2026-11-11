# Free Data Acquisition Coverage Matrix

**As of:** 2026-11-12  
**Branch:** `preksha/week3-benchmarks`  
**Decision:** Free-source acquisition completed as far as accessible data permits. The original treated sample remains frozen at **8 firms**. No purchase was made and no Synthetic Control benchmark was executed.

## Frozen sample reconciliation

The two event files in the branch identify the same eight treated firms: CRM, FAST, ADS, MHK, SWKS, ETSY, TER and CTLT. The earlier seven-firm donor-screen template omitted CTLT; that was a template defect, not authority to alter the treated sample. The previous local diagnostics contained rows for seven firms and none for CTLT. The fresh Yahoo/yfinance acquisition on 2026-11-11 returned 313/313 expected sessions for six firms (CRM, FAST, MHK, SWKS, ETSY and TER), and no history for ADS or CTLT. The two missing cases remain in all coverage records.

## Event-level coverage

| Treated firm(s) | Announcement / event day zero | Effective | Frozen cases | Fresh Yahoo coverage | Membership snapshot available | Status |
|---|---|---|---:|---|---|---|
| CRM, FAST | 2008-09-09 / 2008-09-10 | 2008-09-12 | 2 | CRM 313/313; FAST 313/313 | 2008-09-08 | **Blocked:** SEC filings inaccessible for SIC/shares extraction; official donor membership and contamination unresolved. |
| ADS, MHK | 2013-12-11 / 2013-12-11 | 2013-12-20 | 2 | ADS 0/313; MHK 313/313 | 2013-12-10 | **Blocked:** ADS missing-price case; donor evidence and SEC fundamentals unresolved. |
| SWKS | 2015-03-09 / 2015-03-09 | 2015-03-11 | 1 | SWKS 313/313 | 2015-03-03 (6 days earlier) | **Blocked:** donor membership and point-in-time SEC fundamentals unresolved. |
| ETSY, TER, CTLT | 2020-09-04 / 2020-09-08 | 2020-09-21 | 3 | ETSY 313/313; TER 313/313; CTLT 0/313 | 2020-06-22 (74 days earlier) | **Blocked:** CTLT missing-price case; intervening membership reconstruction and donor evidence not independently validated. |

The locked windows remain unchanged: fit [-252,-21], validation [-20,-1], primary post [0,+20], extended post [0,+60]. The requested event-window panels contain 313 SPY sessions (from day -252 to +60).

## Price acquisition

The reproducible extraction is in `scripts/acquire_week3_yahoo_prices.py`. It uses yfinance 1.8.0, Python 3.14.8, daily interval, `auto_adjust=False`, `actions=True`, and exclusive end dates. SPY supplies the session calendar and is also saved for beta calculations. Raw OHLC/volume, Yahoo adjusted close, dividends and split fields are retained. The run retrieved at 2026-11-11 23:24:02 UTC (2026-11-12 in India) returned:

- Six treated firms with complete 313-session panels and no missing raw close, adjusted close or volume values.
- ADS and CTLT with no returned history; their 626 expected ticker-session observations are listed as missing.
- Nine exploratory price leads with complete panels, five leads with no history. Price availability is not donor eligibility.
- No split event was reported within the requested event windows. Dividend events are recorded in the raw files (FAST 3, SWKS 5, TER 5 among treated panels).

Yahoo `Adj Close` is provider-adjusted and may reflect later distributions/corporate actions; the raw close, adjusted close, dividends and splits are retained separately. This is a reproducible extraction, not a point-in-time adjustment validation or approval of Yahoo as the final research source.

## September 2020 membership reconstruction

The local S&P membership file had its last pre-announcement snapshot on 2020-06-22, 74 days before the 2020-09-04 announcement. The downloaded public `fja05680/sp500` change log records no constituent change from 2020-06-22 through 2020-09-04. Its next listed change is 2020-09-18 (LUMN/CTL label change), followed by the 2020-09-21 treated additions ETSY, TER and CTLT and removals COTY, KSS and HRB. S&P's 2020-09-04 release confirms the September 21 changes; its 2020-06-12 release documents the June 22 snapshot updates. These dated releases support the endpoints, but do not constitute a complete official announcement archive for every possible intervening change. Therefore the community log and current treated/donor statuses remain provisional pending a complete official cross-check.

## SEC and price-based matching evidence

An automated SEC submissions search identified the latest filing records strictly before each pre-event cutoff for FAST/GWW, ADS/COF and ETSY/EBAY. Requests to the SEC Archives for filing indexes and filing documents returned HTTP 403 during this acquisition; the extraction therefore yielded **no verified SIC or shares outstanding**. Those fields and market capitalization are blank in the donor dataset, with accession identifiers and failure notes preserved in `data/processed/week3_sec_filing_access_attempts.csv`. The original 2008 SEC filings still need manual retrieval/review; no 2008 SIC or share count is inferred from current data.

For candidate series with prices, the saved screening metrics report beta versus SPY and median daily raw-close × volume over the locked fit window, plus cumulative adjusted-close return over that fit window. These are descriptive price calculations only. No point-in-time shares, market capitalization, validated SIC, treatment-relative return correlation for every pair, or contamination review is available. No candidate is designated eligible.

## Donor and benchmark decision

The donor CSV remains the existing blank template because none of the exploratory names cleared evidence gates. Price-only lead coverage and metrics are summarized in the donor eligibility report and separate price files. No donor was added to the benchmark input, the original eight treated firms were not changed, and no SCM helper was run.

**Event decision:** all four event clusters remain blocked for SCM. This is due to missing or unverified donor membership, SEC matching fields and contamination review; the ADS and CTLT treated-price gaps add separate event-specific blockers. The SCM approval remains conditional on successful validation.

## Data files and reproduction

- Treated, donor-lead and SPY prices: `data/raw/week3_yahoo/`
- Retrieval parameters and per-ticker status: `data/raw/week3_yahoo/manifest.json`, `retrieval_log.csv`, `candidate_price_coverage.csv`
- Missing session and quality reports: `missing_sessions.csv`, `candidate_missing_sessions.csv`, `data_quality.csv`
- Membership status evidence: `data/processed/week3_membership_evidence.csv`
- Dated 2020 community change log excerpt: `data/processed/week3_2020_membership_change_log.csv`
- SEC filing attempt trace: `data/processed/week3_sec_filing_access_attempts.csv`
- Donor screening decision and lead-by-lead evidence: `docs/week3/donor_eligibility_report.md`; the existing `data/processed/week3_donor_candidates.csv` remains unpopulated because no lead is verified eligible.
- Price metric calculation: `scripts/build_week3_screening_metrics.py`, output `data/processed/week3_price_screening_metrics.csv`
- Final limitations and decision log: `docs/week3/donor_eligibility_report.md`

To regenerate prices in a compatible Python environment: install `pandas` and `yfinance==1.8.0`, then run `python scripts/acquire_week3_yahoo_prices.py`. The script stores the provider response panels, request window and retrieval/library metadata. To regenerate the price-derived screening metrics after that run, execute `python scripts/build_week3_screening_metrics.py`.

## Sources

- S&P Dow Jones Indices, [June 12, 2020 announcement](https://press.spglobal.com/2020-06-12-S-P-Dow-Jones-Indices-Announces-Tyler-Technologies-Bio-Rad-Laboratories-and-Teledyne-Technologies-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600), [September 4, 2020 announcement](https://press.spglobal.com/2020-09-04-Etsy-Teradyne-and-Catalent-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600).
- Community membership data: [fja05680/sp500 repository](https://github.com/fja05680/sp500), including [dated change log](https://github.com/fja05680/sp500/blob/master/sp500_changes_since_2019.csv) and [historical snapshots](https://github.com/fja05680/sp500/blob/master/S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv).
- SEC: [EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation); filing index/document URLs and accession identifiers appear in the acquisition trace.
- Yahoo Finance: [historical data help](https://help.yahoo.com/kb/SLN2310.html).

