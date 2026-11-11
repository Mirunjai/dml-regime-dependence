# Collaborator Data-Access Request: CRSP/WRDS

**Status:** Prepared for team review and sharing with a potential licensed collaborator. This is not an authorization to send data, request credentials, or run the benchmark. Synthetic Control remains blocked.

## Request in brief

Could a university or research-lab collaborator with an active, institutionally licensed CRSP/WRDS account confirm whether their licence permits them to run a small academic validation extract for this project? We need historical U.S. daily stock prices/returns and point-in-time S&P 500 membership, including inactive/delisted securities, for the event periods below. We are not asking the collaborator to transfer raw licensed data unless their licence expressly permits that. First, please confirm permitted access, derived-output sharing, and the exact data fields available.

The initial validation sample should cover the 2008 CRM event and 3–5 potential donor securities selected by the licensed collaborator from the historical S&P 500 roster. These are sample candidates only; the selection does not establish donor eligibility. If access and output sharing are permitted, the sample will include the data and evidence fields below and be reviewed before a full donor pool is constructed.

## Treated securities and frozen event periods

Event-day zero and exact price windows are taken from the branch's `week3_event_day_zero.csv` and `week3_benchmark_windows.csv`. The broad date spans below include fit, validation, primary post-event, and extended post-event windows.

| Announcement cluster | Treated securities | Announcement date | Event day zero | Effective date | Required daily price/return span |
|---|---|---|---|---|---|
| 2008-09 | CRM (Salesforce), FAST (Fastenal) | 2008-09-09 | 2008-09-10 | 2008-09-12 | 2007-09-11 through 2008-12-04 |
| 2013-12 | ADS (Alliance Data Systems), MHK (Mohawk Industries) | 2013-12-11 | 2013-12-11 | 2013-12-20 | 2012-12-11 through 2014-03-11 |
| 2015-03 | SWKS (Skyworks Solutions) | 2015-03-09 | 2015-03-09 | 2015-03-11 | 2014-03-07 through 2015-06-03 |
| 2020-09 | ETSY (Etsy), TER (Teradyne), CTLT (Catalent) | 2020-09-04 | 2020-09-08 | 2020-09-21 | 2019-09-09 through 2020-12-02 |

CTLT is included only as a coverage/availability check. It is currently a documented missing-data case. Do not substitute a different series if a comparable adjusted history cannot be supplied.

## Membership evidence dates

For an initial point-in-time roster, please provide membership as of the last trading close strictly before each announcement:

- CRM and FAST: 2008-09-08
- ADS and MHK: 2013-12-10
- SWKS: 2015-03-06
- ETSY, TER, and CTLT: 2020-09-03

Please include the official member roster on those dates and daily membership flags or dated join/leave intervals for the sample securities over their required price spans. Retain announcement and effective dates separately. If the provider's membership convention is “effective prior to market open,” state how it handles the prior session and effective date.

The full donor universe will be defined only after source validation. For the first sample, the collaborator should select 3–5 securities from the 2008-09-08 S&P 500 roster for data-path validation, identify the selection as illustrative, and include their historical identifiers and evidence. Do not label them eligible or final donors.

## Requested price, membership, and identity fields

For CRM plus the illustrative 2008 sample securities:

1. Historical security identifiers: permanent identifier (e.g. PERMNO/PERMCO), historical ticker, CUSIP if licensed to share, security name, share/exchange code, and dated ticker/name changes.
2. Daily data for every trading session across 2007-09-11 to 2008-12-04: date, raw close, total-return adjusted close or daily total return, volume, shares outstanding if licensed, and corporate-action/adjustment information. State whether returns include ordinary dividends and how splits, distributions, delistings, missing sessions, and terminal returns are handled.
3. Point-in-time S&P 500 membership: roster on 2008-09-08; daily in-index indicator or effective-dated membership intervals; source and effective-date convention.
4. Provenance: database/module and release/version, access date, extraction date/time, extraction query or script/config, field definitions, calendar, adjustment setting, and file hashes.
5. A missingness and validation summary: expected/observed trading days by security and window; duplicates; missing prices; adjustment/corporate-action flags; delisted or renamed security coverage; and any reconciliation with index announcements.

For full screening (only after the sample is reviewed), the same price and membership fields will be needed for treated securities and all candidate securities in each historical roster. SEC SIC and point-in-time market-cap evidence will be assembled from filings as specified below; do not use current industry or fundamentals.

## SEC fields assembled by our team

The team's approved proposed screen uses:

- SIC from the latest SEC filing submission header publicly available by the offset -21 pre-event cutoff.
- Common shares outstanding from that same latest available filing, adjusted for intervening splits/capital actions through the cutoff.
- Cutoff-date price from the approved price provider.
- Market capitalization = split-aligned shares outstanding × cutoff-date close.

For the older 2008 event, we will inspect the original SEC EDGAR filings/headers because SEC XBRL financial-statement data sets begin in 2009. Filing date and period end must remain distinct. SEC-derived values are point-in-time fields, not present-day company profile data.

## Frozen windows and screening characteristics

Relative to the listed event day zero, the unchanged SCM windows are:

- Fit: [-252, -21]
- Validation: [-20, -1]
- Primary post-event: [0, +20]
- Extended post-event: [0, +60]

Beta, liquidity, and pre-event return matching will be calculated only after approved daily data are available and the locked definitions are confirmed. Report observation counts and missingness; no look-ahead data or imputation.

## Licence and permitted-sharing questions

Before any transfer or extract, please confirm in writing with the licensee/data administrator:

1. Does the licence cover non-commercial academic research by this project team, including contributors who are not employed/enrolled at the license-holding institution?
2. May the collaborator run the analysis on their institution's licensed environment and share derived evidence (membership flags, security/date-level screening fields, computed returns/market caps, diagnostics, tables, and hashes) with the team?
3. Are raw daily observations, price histories, identifier crosswalks, or membership rosters allowed to be shared externally? If not, what outputs may be shared and what must remain on the licensed system?
4. Are there restrictions on publishing derived results, retaining outputs after access ends, or sharing code/configuration that queries the database?
5. Which exact CRSP/WRDS subscriptions/modules and date coverage are included? Does access include delisted securities and daily S&P 500 membership for all periods in this request?
6. Can the collaborator export the needed adjusted-price/return fields and membership evidence, or must the analysis remain on their licensed instance?

Do not send licensed raw data to the project until those terms are clear. A collaborator can instead run approved calculations on their licensed environment and share only permitted derived evidence.

## Current decision gates

- No internal university/research-lab contact directory is connected to this task workspace, and no collaborator contact is listed in the repository. No outreach has been sent.
- If an eligible collaborator is identified, first share this request and receive their institution's licensing answer.
- Then review the small CRM sample, data provenance, and derived-output permissions.
- Only after the team approves the source and evidence may full donor screening begin.
- SCM remains blocked; no benchmark or placebo analysis is authorized until donor eligibility, data coverage, and review gates pass.
