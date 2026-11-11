# Week 3 Historical Data Source Audit

Status: source identified; access not confirmed. No data was downloaded and no donor eligibility has been certified.

## Recommended source: CRSP U.S. Stock Database via WRDS

The best fit for the frozen 2008, 2013, 2015, and 2020 event windows is the CRSP daily U.S. Stock Database, accessed through the team's institutional WRDS subscription. CRSP describes daily market data and corporate actions for active and inactive U.S. securities, with survivor-bias-free history, permanent security identifiers (PERMNO/PERMCO), and coverage from 1926. WRDS states its interactive historical S&P 500 constituent query covers any day from 1958 to the latest data update and requires a CRSP subscription.

This is a source recommendation based on published coverage, not evidence that the team has access. It should be confirmed with the team lead / institutional librarian before acquisition. Sources:

- CRSP U.S. Stock Database, coverage and permanent identifiers: https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/
- WRDS S&P 500 constituent query, 1958 to latest and CRSP subscription requirement: https://wrds-www.wharton.upenn.edu/pages/classroom/the-sp-500/
- WRDS historical constituent download, subscription requirement: https://wrds-www.wharton.upenn.edu/pages/grid-items/downloading-the-sp-500-constituents/
- CRSP/Compustat historical identifier linkage: https://wrds-www.wharton.upenn.edu/pages/wrds-research/database-linking-matrix/using-compustat-historical-identifier-notebook/

## Mapping to frozen donor evidence fields

| Required field | Proposed CRSP/WRDS construction | Point-in-time guard |
|---|---|---|
| Security identity / common stock | Historical name/security and share/exchange codes; retain permanent PERMNO and historical ticker/CUSIP | Use security identity effective during the window; do not join by current ticker alone |
| S&P 500 membership | CRSP historical S&P 500 constituent list / index membership | Query membership on announcement cutoff; use historical announcements for discrepancy checks |
| Industry | Historical SIC in CRSP or effective-dated Compustat classification linked through a valid date-specific CCM link | Do not use current industry for past events |
| Market capitalization | Absolute close × shares outstanding using data as of the last session strictly before announcement; document units and adjustment | No post-announcement shares or price |
| Beta | OLS on the frozen pre-event daily return window against the frozen market return series | Estimate using pre-announcement observations only; report observation count |
| Liquidity | Median daily dollar volume over the frozen pre-event window (volume × absolute unadjusted price, subject to corporate-action units) | Do not include event or post-event sessions |
| Pre-event return correlation | Correlation of treated and candidate donor returns over the frozen pre-event window | Common dates only; report n and no imputation |
| Historical adjusted prices / returns | Use one CRSP return convention consistently for treated and donors; document total-return versus price-return definition and corporate-action handling | Full aligned data across fit, validation, primary, and extended windows; no silent backfill |
| Contamination | Dated S&P addition/deletion announcements, issuer filings/news, and treated-event calendar review | Search only for material exposures in the frozen period; record evidence and decision |

CRSP daily total returns may be preferable to reconstructing adjusted prices, but the benchmark's locked outcome definition must be checked before use. Do not mix CRSP total returns with Yahoo adjusted closes or another vendor's price series. If the locked outcome specifically requires adjusted close levels, obtain a consistent panel of adjusted close levels for every treated and donor unit from one source.

## Current blocker and next action

No WRDS/CRSP credentials or local checkout are available in this task workspace, and the repository does not contain the price panel. The donor screening table remains empty. Ask the team lead/institutional librarian to confirm CRSP access for CRSP Stock daily data and S&P 500 constituent history, plus the effective-dated Compustat/CCM fields needed for industry if not present in CRSP. After access is available, extract the full point-in-time U.S. common-stock universe, apply the frozen event-specific matching criteria, and populate evidence for every included and excluded lead before fitting any weights.

If CRSP access is unavailable, do not substitute the current-constituent universe or the community membership snapshots as proof. Obtain team approval for another licensed source that can document delisted securities, total-return adjustments, historical membership, and dated fundamentals.

## CTLT source check

A one-time alternative-source check found Quiver's public historical page states its adjusted close accounts for splits and dividends and advertises daily prices back to 2014. The page/API did not provide a complete event panel to this workspace; the API requires an access key. No price file was retrieved, provider approval/licensing for this project is unconfirmed, and no consistency check against the project's price panel is possible. This attempt therefore did not satisfy the CTLT data requirement. Keep CTLT excluded from complete-case SCM unless a complete, approved, consistently defined adjusted-price/return series is obtained. Source: https://www.quiverquant.com/stock/CTLT/historical-prices/.

## Execution gate

The team lead's conditional approval is recorded in the audit. Benchmark execution remains blocked until the donor universe and complete adjusted-price/return panel pass the evidence and coverage checks. Preserve the locked fit [-252, -21], validation [-20, -1], primary post [0, +20], and extended post [0, +60] windows; do not alter matching criteria or add firms.
