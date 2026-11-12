# Week 3 Historical Data Source Audit

**Status updated 2026-11-11:** Institutional CRSP/WRDS access has been confirmed unavailable by the team. The prior CRSP/WRDS recommendation below is therefore not actionable for this project. No purchase has been made and no historical donor eligibility is certified.

## Current source review

See [Alternative Historical Data Sources Review](alternative_data_sources_review.md) and [Norgate Access and SEC Point-in-Time Validation Status](norgate_sec_validation_status.md) for the current evaluation.

Norgate Platinum is the leading conditional candidate for historical daily prices and point-in-time S&P 500 membership. Its published price coverage begins in 1990 and its S&P 500 constituent history begins in 1957; the plan costs USD $346.50 for six months and USD $630 for twelve months. Historical membership requires a supported integration (Python on Windows is listed); simple CSV export includes price/volume/turnover, but not membership. The trial history is limited to two years, so an event-period sample for 2008 requires a separate purchase decision. The lead has expressly said not to purchase yet.

Norgate does not supply historical industry classification or historical fundamentals/market capitalization. The team has proposed contemporaneous SEC filing SIC as the industry proxy, and point-in-time market cap using the latest pre-cutoff filing's shares outstanding multiplied by the approved provider's cutoff-date close, adjusted for intervening splits. That method still requires source validation. Current/future fundamentals must not be used retrospectively.

## Former CRSP/WRDS path (unavailable)

The earlier plan proposed CRSP U.S. Stock Database through WRDS because its documented active/delisted security history, permanent identifiers and historical index membership appeared to fit the event dates. Institutional access is unavailable, so this is recorded only as a screened-out route, not the current recommendation. Reconsider it only if the team later obtains legitimate institutional access.

## Required evidence and current status

| Required field | Proposed evidence/construction | Status |
|---|---|---|
| Security identity and point-in-time S&P membership | Norgate security history and supported membership query, after access; preserve stable identity and daily event-date membership | Not acquired or validated |
| Adjusted daily prices | One consistently configured provider across treated firms and donors, including delisted securities and all frozen windows | Not acquired from Norgate; tracked branch lacks raw adjusted prices |
| Industry | SEC SIC in latest EDGAR submission header publicly filed by the offset -21 pre-event cutoff | Method agreed in principle; sample not complete |
| Market capitalization | Latest available filing shares, split-aligned through cutoff, × approved provider close at cutoff | No cutoff-date approved prices; no cap value calculated |
| Beta, liquidity, pre-event returns | Calculate from price/market data only using the frozen pre-event period and definitions | Not calculated for donors |
| Contamination | Dated announcement, membership and issuer-event evidence for each candidate | No donor decisions complete |

## CTLT

One alternative-source check was recorded in `synthetic_control_donor_screening.md`: Quiver's public page describes adjusted close including splits and dividends and advertises price history back to 2014, but no usable complete event panel was obtained in the workspace. CTLT remains a documented missing-data case unless an approved source yields a complete, comparable series.

## Scope and execution gate

Frozen windows remain fit [-252, -21], validation [-20, -1], primary post [0, +20], and extended post [0, +60]. No donor pool has been frozen. The SCM helper has no placebo inference; the team lead requires screening and data validation before execution. Keep the benchmark formally blocked until the sample, donor evidence, and source decision are accepted.

## Prior CRSP/WRDS source references

- CRSP database layout: https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/
- WRDS S&P 500 query: https://wrds-www.wharton.upenn.edu/pages/classroom/the-sp-500/
- WRDS historical constituent download: https://wrds-www.wharton.upenn.edu/pages/grid-items/downloading-the-sp-500-constituents/
