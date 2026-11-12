# Week 3 Donor Eligibility and Data Quality Report

**Review date:** 2026-11-12  
**Branch:** `preksha/week3-benchmarks`  
**Status:** donor eligibility and SCM remain blocked; no Synthetic Control benchmark was run.

## Scope and frozen sample

The treated roster remains CRM, FAST, ADS, MHK, SWKS, ETSY, TER and CTLT (8 firms across 4 event clusters). The seven-case donor-screen template omitted CTLT; it did not define the treated sample. No firm was added to or removed from the frozen sample. The historical donor-candidate CSV remains the project template and was not populated with exploratory, unverified companies.

Locked fit/validation/post windows remain [-252,-21], [-20,-1], [0,+20], and [0,+60].

## Yahoo/yfinance acquisition

The reproducible extractor is `scripts/acquire_week3_yahoo_prices.py`. Run metadata: Python 3.14.8, yfinance 1.8.0, retrieval timestamp 2026-11-11 23:24:02 UTC, interval 1d, auto_adjust=False, actions=True, end-exclusive date requests. Raw OHLC and volume, adjusted close, dividends and splits are preserved separately. SPY is saved as the exchange-calendar and market-return series. The provider's adjusted series may be retroactively adjusted; it is not established as a point-in-time adjustment series.

| Treated ticker | Event window sessions | Observed | Missing sessions | Result |
|---|---|---:|---:|---|
| CRM | 313 | 313 | 0 | complete |
| FAST | 313 | 313 | 0 | complete |
| ADS | 313 | 0 | 313 | no Yahoo history returned |
| MHK | 313 | 313 | 0 | complete |
| SWKS | 313 | 313 | 0 | complete |
| ETSY | 313 | 313 | 0 | complete |
| TER | 313 | 313 | 0 | complete |
| CTLT | 313 | 0 | 313 | no Yahoo history returned; retain missing-data case |

Among 6 successful treated panels, there are no missing close, adjusted-close, or volume values and no duplicate dates. Dividends are recorded for FAST (3 sessions), SWKS (5), and TER (5); no in-window split was returned. Missingness counts for ADS and CTLT are blank in the quality report where they are not observable and are represented by 626 explicit missing-session rows.

The price-only lead queue contains 14 ticker/event pairs. Nine have complete 313-session panels (GWW, MSM, COF, TILE, CRUS, EBAY, SHOP, COHU, FORM); five returned no history (NOW, WDAY, SYF, LEG, QRVO). None is established as an eligible donor.

## Point-in-time S&P membership evidence

The public community history file was used as a screening source. It places GWW for FAST (2008), COF for ADS (2013), LEG for MHK (2013), and EBAY for ETSY (2020) in the available prior snapshots and excludes other current exploratory leads from those snapshots. All treated names are outside their prior snapshots. Membership evidence is **provisional**: it is community maintained, snapshots are stale for SWKS by 6 days and the 2020 event by 74 days, and treated/donor-specific official S&P membership confirmation is incomplete.

For September 2020, the local membership snapshot is 2020-06-22. The community change log contains no recorded constituent change from that date through the 2020-09-04 announcement. It lists LUMN/CTL on September 18 and the treated additions ETSY, TER and CTLT with removals COTY, KSS and HRB on September 21. The official S&P June 12 and September 4 releases support the June 22 and September 21 endpoints. A search of S&P's press archive for July/August 2020 found no S&P 500 constituent-change release between those notices; the August 24 index change was for the Dow Jones Industrial Average. This supports, but does not by itself prove, no intervening S&P 500 membership change, so the June snapshot is still not treated as an individual security-level membership certificate. See `data/processed/week3_membership_evidence.csv` and `week3_2020_membership_change_log.csv`.

## SEC and matching variables

The SEC submissions API identified filing accessions strictly before the pre-event cutoffs for FAST/GWW, ADS/COF and ETSY/EBAY. EDGAR archive index and filing-document requests returned HTTP 403 during this run. Consequently, there is no verified SIC, shares-outstanding value, split-aligned share count or historical market capitalization in this deliverable. The attempt trace preserves the accession, filing date/type, URL and fetch error in `data/processed/week3_sec_filing_access_attempts.csv`. No current SIC or future filing was substituted. The 2008 SEC field checks require original filings and remain unresolved.

Price-based matching statistics were calculated descriptively from adjusted-close daily returns and raw close × volume for the fit window, with beta estimated against SPY over the same aligned sessions. These values do not establish industry match, market-cap match, or eligibility. There is no full matched pre-event return correlation across all cases (ADS treated prices are missing), and no event contamination review has been completed. See `data/processed/week3_price_screening_metrics.csv`.

| Treated → lead | Yahoo panel | Community snapshot member? | Beta vs SPY | Median fit dollar volume (USD/day) | Fit adjusted return | Decision |
|---|---:|---:|---:|---:|---:|---|
| FAST → GWW | 313/313 | yes | 0.954 | 67.2m | 6.7% | not eligible: official membership, SEC fundamentals, contamination unresolved |
| FAST → MSM | 313/313 | no | 0.957 | 22.8m | -4.0% | not eligible: snapshot screen and other gates |
| ADS → COF | 313/313 | yes | 1.183 | 217.7m | 21.4% | not eligible: ADS treated prices missing; SEC/membership unresolved |
| ADS → SYF | 0/313 | no | — | — | — | not eligible: no candidate or treated price panel |
| MHK → TILE | 313/313 | no | 1.622 | 5.0m | 40.5% | not eligible: snapshot screen and other gates |
| MHK → LEG | 0/313 | yes | — | — | — | not eligible: no Yahoo price panel |
| SWKS → CRUS | 313/313 | no | 0.673 | 25.7m | 44.6% | not eligible: snapshot screen and other gates |
| SWKS → QRVO | 0/313 | no | — | — | — | not eligible: no Yahoo price panel |
| ETSY → EBAY | 313/313 | yes | 0.624 | 418.1m | 35.0% | not eligible: official membership, SEC fundamentals, contamination unresolved |
| ETSY → SHOP | 313/313 | no | 1.127 | 1,237.8m | 193.6% | not eligible: snapshot screen and other gates |
| TER → COHU | 313/313 | no | 1.537 | 4.6m | 30.2% | not eligible: snapshot screen and other gates |
| TER → FORM | 313/313 | no | 1.331 | 12.1m | 55.4% | not eligible: snapshot screen and other gates |
| CRM → NOW | 0/313 | no | — | — | — | not eligible: no price panel |
| CRM → WDAY | 0/313 | no | — | — | — | not eligible: no price panel |

Statistics are rounded; inputs and calculations are in the linked CSVs. Pair-specific pre-event correlation, SIC, market cap and contamination are not reported as verified.



### Treated-relative fit comparisons

For price-complete treated/donor pairs, daily adjusted-close return correlations were calculated over the same fit dates. These metrics are descriptive and do not replace eligibility validation.

| Pair | Donor vs treated fit return correlation | Treated cumulative fit return |
|---|---:|---:|
| FAST / GWW | 0.703 | 19.5% |
| FAST / MSM | 0.580 | 19.5% |
| ADS / COF | unavailable | unavailable (ADS prices missing) |
| MHK / TILE | 0.596 | 65.8% |
| SWKS / CRUS | 0.314 | 124.0% |
| ETSY / EBAY | 0.486 | 167.4% |
| ETSY / SHOP | 0.559 | 167.4% |
| TER / COHU | 0.753 | 53.2% |
| TER / FORM | 0.810 | 53.2% |

## Event decisions and next gate

| Event cluster | Decision | Main blockers |
|---|---|---|
| CRM / FAST (2008) | blocked | official membership, SEC point-in-time SIC/shares and contamination evidence absent; CRM's price lead list has no complete candidate price history |
| ADS / MHK (2013) | blocked | ADS treated price history absent; SEC fundamentals, official membership and contamination unresolved |
| SWKS (2015) | blocked | official membership and SEC fundamentals unresolved; no verified donor passes all gates |
| ETSY / TER / CTLT (2020) | blocked | CTLT remains missing; official reconstruction for June–September transition, SEC fundamentals and contamination unresolved |

No Synthetic Control weights, RMSPE, placebo inference, post/pre RMSPE or donor concentration results are available because the required donor universe did not pass validation. The team lead's conditional approval does not waive these gates. No purchases were made.

## Files

- `data/raw/week3_yahoo/treated_prices.csv`: reproducible treated-price extraction
- `data/raw/week3_yahoo/candidate_prices_exploratory.csv`: exploratory price-only leads; not donor eligibility data
- `data/raw/week3_yahoo/spy_market_prices.csv`: aligned SPY price and return series
- `data/raw/week3_yahoo/retrieval_log.csv`, `candidate_price_coverage.csv`, `missing_sessions.csv`, `candidate_missing_sessions.csv`, `data_quality.csv`, `manifest.json`
- `data/processed/week3_membership_evidence.csv`, `week3_2020_membership_change_log.csv`
- `data/processed/week3_sec_filing_access_attempts.csv`
- `data/processed/week3_price_screening_metrics.csv`
- `scripts/acquire_week3_yahoo_prices.py`, `scripts/build_week3_screening_metrics.py`

## Sources

- S&P Dow Jones Indices, [press-release archive search](https://press.spglobal.com/index.php?Institution=&l=50&news=&o=1400&s=2429); [June 12, 2020 release](https://press.spglobal.com/2020-06-12-S-P-Dow-Jones-Indices-Announces-Tyler-Technologies-Bio-Rad-Laboratories-and-Teledyne-Technologies-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600); [September 4, 2020 release](https://press.spglobal.com/2020-09-04-Etsy-Teradyne-and-Catalent-Set-to-Join-S-P-500-Others-to-Join-S-P-MidCap-400-and-S-P-SmallCap-600).
- [fja05680/sp500 community history](https://github.com/fja05680/sp500); [SEC EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation); [Yahoo Finance historical data notes](https://help.yahoo.com/kb/SLN2310.html).

