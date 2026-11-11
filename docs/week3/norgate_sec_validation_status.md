# Norgate Access and SEC Point-in-Time Validation: Status

**Purpose:** Follow the team lead's review decision. Evaluate Norgate without purchasing it, prepare a limited SEC information-timing example, and define what is still required before any donor pool is constructed.

**Status:** No Norgate subscription was purchased; no Norgate event-period prices or S&P membership were accessed. No potential donor is marked eligible. Synthetic Control remains blocked.

## Norgate cost and access findings

The Norgate US Stocks **Platinum** plan is the minimum plan that includes delisted securities and historical index constituents. The current published price is **USD $346.50 for six months** or **USD $630 for twelve months**. Norgate offers fixed six- or twelve-month subscription terms (not monthly access); twelve months is listed as 10% below two six-month terms. The free trial lasts three weeks but is limited to the last two years of history, so it cannot validate any project's event period. No subscription has been purchased. Confirm price and terms again before any later purchase decision.

Published coverage for Platinum includes daily price history and delisted securities back to 1990, enough in calendar coverage for the 2008 event's pre-event fit window. Historical S&P 500 membership is available from March 1957. Norgate says membership is daily and effective-date aligned. It also states pre-March-2000 S&P constituent change history is synthesized as monthly rebalances; project event dates are later than this caveat.

### Project export feasibility

- Norgate Data Updater can export historical prices, volume and turnover to CSV or text.
- Historical index membership and other features are **not included in those exports**. Those require a supported Norgate-developed integration or vendor plugin. The official integration list includes **Python on Windows**, which is consistent with the team's Windows setup.
- Therefore a project workflow appears technically possible through (1) price export and (2) a Windows Python integration to query membership, then writing our own provenance-preserving output. This is based on provider documentation only; we have not run it or verified the exact required API fields, licensing, or project-side export workflow.
- A free trial can test interface/export mechanics and recent dates, but cannot validate 2008 data or historical membership for the older event.

Sources: [Norgate US package levels and pricing](https://norgatedata.com/stockmarketpackages.php), [access and integrations](https://norgatedata.com/accessibility.php), [trial history limit](https://norgatedata.com/data-package-faq.php), [trial setup and supported methods](https://norgatedata.com/subscribe/freetrial.php).

## SEC point-in-time methodology

Use the event-specific pre-event cutoff corresponding to offset -21 in the frozen trading-day calendar. For every treated firm and candidate, select the latest SEC filing with an accepted/public filing date no later than that cutoff. Use the filing's EDGAR submission-header SIC as the agreed industry proxy. For market cap, combine the share count in that available filing with the price-provider's closing price on the cutoff date, after aligning the share count for any intervening stock split or equivalent capital action documented between the share-count date and cutoff.

`market_cap_at_cutoff = split-aligned shares outstanding from last available filing × approved provider's cutoff-date close`

Keep filing acceptance date distinct from financial statement period date. A later filing cannot be used merely because it reports an earlier quarter-end. Do not substitute weighted-average diluted shares for point-in-time common shares outstanding. SEC XBRL Financial Statement Data Sets start in April 2009; for 2008, inspect the original EDGAR submission and its filing header/cover directly, consistent with the team lead's instruction. The SEC filing archive and its APIs are public; automated use must comply with SEC access policy.

Sources: [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [SEC Financial Statement Data Sets coverage](https://www.sec.gov/dera/data/financial-statement-data-sets.html), [SEC SIC code list](https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list).

## Limited 2008 treated-firm filing check: Salesforce (CRM)

The frozen event file identifies CRM as an addition announced 2008-09-09. Using the project's locked trading-day offset, the -21 cutoff must be confirmed against the project trading calendar before the row is finalized. The 2008-05-23 10-Q for the quarter ended 2008-04-30 is an earlier SEC source that reports approximately **120.1 million common shares outstanding as of 2008-04-30**. The later 2008-08-22 10-Q reports approximately 121.0 million shares as of July 31, but that later filing is after the inferred -21 cutoff and must not be used for this example. This demonstrates why the filing's public date, not only its reporting date, controls.

| Field | Provisional evidence | Status |
|---|---|---|
| Treated firm / event | CRM; event announcement 2008-09-09 | From frozen project event file; not a donor eligibility claim |
| Candidate cutoff | Offset -21 in locked trading-day calendar (approximately 2008-08-08 if trading dates are counted back from 2008-09-09) | Must confirm against project calendar before use |
| Latest filing examined for the example | CRM Form 10-Q, quarter ended 2008-04-30; signature date 2008-05-23; accession 0001193125-08-121851 | [SEC filing](https://www.sec.gov/Archives/edgar/data/1108524/000119312508121851/d10q.htm) |
| Common shares | Approximately 120.1 million as of 2008-04-30 | Stated on filing cover; not weighted-average diluted shares |
| SIC | Must be read from this accession's contemporaneous SEC submission header to fulfill the lead's rule | Not yet verified from the specific accession header; do not copy present-day SIC |
| Cutoff-date price | Requires approved Norgate history | Unavailable; no historical market cap calculated |
| Split alignment / corporate-action check | Requires action history through cutoff | Not complete |
| S&P 500 membership | Requires Norgate membership output on the date prior to announcement, with exact effective-date convention | Not accessed |
| Donor comparators | None selected | Wait for point-in-time universe; no donors screened |

The filing cover's approximate share count is useful as a sample of the SEC source record, but it is not a completed market-cap observation. We deliberately do not multiply by a price from an unapproved provider or use a post-cutoff fact. The later Salesforce 10-Q reports 121.0 million shares for July 31, 2008; it is cited here only to show the timing trap, not as usable cutoff data. [Later SEC filing](https://www.sec.gov/Archives/edgar/data/1108524/000119312508183002/d10q.htm).

## What is ready and what remains blocked

Ready:
- Norgate minimum plan and term cost documented.
- The price-versus-membership export split identified; Python on Windows is the documented membership access route.
- Point-in-time SEC calculation protocol written down.
- One older treated firm's filing located and a share-count datapoint checked.

Blocked:
- The team has not made the separate purchase decision, so we do not have licensed event-period price or point-in-time membership data.
- No real Norgate sample can yet be provided for CRM plus potential donors, so adjustment continuity, coverage gaps, identifiers, corporate actions, and export reproducibility remain untested.
- CRM's SIC in the exact applicable 2008 filing header has not been verified in this review.
- Market cap cannot be calculated without an approved cutoff-date price and completed split check.
- No potential donors have been selected or screened; this is intentionally deferred pending S&P membership evidence.

## Next gated actions

1. If the team chooses to test Norgate, activate the three-week trial **without a purchase** to validate install, Windows Python integration, price CSV export, adjustment options, and recent-date membership access.
2. If the interface test succeeds, present the dated quote/checkout terms and still-unresolved older-history need to the team. The team decides separately whether to buy the minimum six-month Platinum term.
3. Only after explicit purchase approval and data access, produce a small validation extract: CRM plus a few securities selected from the historical member universe; adjusted prices and membership; SEC SIC header; shares outstanding and split alignment; cutoff-date market cap; missingness and corporate-action checks; retrieval metadata and hashes.
4. Submit that validation extract and method for review. Only after approval may full donor screening begin. Benchmark execution remains separately blocked until donor evidence is accepted.

No frozen window, match criterion, treated event, or experiment scope is changed.
