# Alternative Historical Data Sources: Review Before Donor Construction

**Status:** Preliminary source evaluation for team review. No provider has yet been approved for the donor pool. No donor eligibility is asserted here, and no Synthetic Control benchmark was run.

## Decision requested

Evaluate **Norgate Data Platinum** as the leading candidate for the core daily price and point-in-time S&P 500 membership layer. It is the only reviewed source whose published coverage appears to span all four events and their frozen fitting windows while also documenting daily historical membership and delisted securities. This is a conditional candidate, not a completed source recommendation: the free trial is limited to the last two years, so we have not obtained or validated an actual historical sample from Norgate. Norgate also does not provide historical industry classifications or historical fundamentals/market capitalization. Those gaps mean it does not, by itself, meet all locked donor-screening requirements.

**Recommendation for review:** authorize a small, reproducible Norgate data-access evaluation (subscription or other legitimate access) and require a dated export for one event’s treated firm plus a few candidate firms, alongside membership and adjustment checks, before choosing the source. Do not construct the donor pool until that sample and its evidence have been reviewed and accepted. The reviewed provider documentation does not establish historical industry or point-in-time market-cap values from Norgate; those criteria require an approved dated source or must be reported as unsatisfied under the frozen rules.

## Coverage and fit

Frozen event windows are fit [-252, -21], validation [-20, -1], primary post [0, +20], and extended post [0, +60]. Event dates span 2008, 2013, 2015, and 2020. The 2008 fit window requires price data beginning in 2007.

| Source | Adjusted daily prices and event-window coverage | Point-in-time S&P 500 membership | Screening fields and limitations | Assessment |
|---|---|---|---|---|
| **Norgate Data Platinum** | Published coverage: daily US price history from 1990, including delisted securities. It documents four price settings: raw, capital reconstructions, capital reconstructions plus special distributions, and total return including normal distributions. Coverage span is sufficient on paper. | Daily exact-date membership, including intra-period changes; S&P 500 membership starts March 1957. Historical constituent access requires Platinum or Diamond and a supported interface. | Historical industry classification and historical fundamentals are explicitly unavailable; only latest classifications/fundamentals are supplied. It does not provide index-change announcement dates. Its database is corrected continuously without versioning. Trial has only two years of prices, so it cannot sample the 2008 event. | **Leading core-data candidate, conditional.** Strongest published fit for the combined price/membership dates, but not yet sample-validated and not sufficient for all frozen matching fields. |
| **EOD Historical Data (EODHD)** | Daily raw OHLC, split-adjusted volume, and adjusted close for splits and dividends. The API documentation describes long historical coverage; exact symbol-by-symbol availability must be checked. | S&P 500 change history is reliable for survivorship-bias-free reconstruction from April 2012. Earlier snapshots are incomplete; the vendor documents that former constituents that exited before April 2012 are missing. | API data are revised and adjusted closes can change after newly recorded actions. Vendor states source acquisition from exchanges, market makers and CFD sources. This membership gap prevents a complete 2008 donor universe. | **Not suitable as the sole source for the full event set.** Useful as a price cross-check or for later events, but cannot establish 2008 membership. |
| **Tiingo** | Official EOD API describes raw and adjusted OHLC, adjusted close/volume and split/dividend fields; historical asset coverage must be checked per symbol and access requires a token. | No integrated point-in-time S&P constituent history was identified in the reviewed documentation. | Would require a separately approved membership source and documented identifier matching. | **Not a standalone solution.** |
| **OHLC.io** | Describes raw, split-adjusted and total-return series, but published plan history limits do not cover the oldest event on lower tiers. | No point-in-time S&P 500 membership product was identified in the reviewed material. | Would require a separate historical membership source. | **Not a standalone solution.** |
| **S&P DJI / Xpressfeed** | Licensed institutional data product. | Direct index product includes historical constituent identifiers and index data. | Cost/access through our institution has not been established. | **Potential authoritative source if institutional access can be confirmed; not presently accessible.** |

## Sample shown for review (illustrative alternative, not the recommendation)

We do not have a Norgate historical export or authorized Norgate historical sample to show. The free trial is explicitly restricted to two years and does not provide a custom sample outside that period. To avoid inventing values, the table below reproduces a short **EODHD documentation example** only. It shows the vendor's field schema and adjustment convention; it is not project data, not a Norgate sample, not an event-window validation, and not evidence of data quality for CRM, FAST, ADS, MHK, SWKS, ETSY, TER, or CTLT.

| Date | Raw close | Adjusted close | Volume |
|---|---:|---:|---:|
| 2024-01-02 | 297.04 | 277.9465 | 4,458,400 |
| 2024-01-03 | 294.39 | 275.4668 | 3,118,400 |
| 2024-01-04 | 291.74 | 272.9872 | 4,615,400 |
| 2024-01-05 | 288.99 | 270.4139 | 3,407,300 |

The values above are the provider's documented MCD.US example. EODHD specifies that its adjusted close incorporates splits and dividends, while its OHLC fields are raw and its volume is split-adjusted. This is not a compliant substitute for a Norgate sample or for actual project input data.

## Required validation before a source can be approved

1. Obtain an authorized sample from the proposed source for a treated firm and a small, identified set of potential securities at one frozen event date. Preserve original files, retrieval time, query/configuration, provider/product, license/access route, and file hashes.
2. Confirm the exact security identifiers across prices and membership; do not assume ticker alone is stable through mergers, renames, or ticker reuse.
3. Confirm daily observations cover each required offset for the selected treated security and each proposed donor. Record missing days, duplicate rows, adjusted-price nulls, and delisting handling.
4. Choose one adjustment convention and apply it consistently to treated firms and donors. For a total-return outcome, Norgate's “Capital Reconstructions, Special Distributions and Normal Distributions” option is the documented total-return setting. Confirm this is consistent with the outcome definition before use. Never mix adjusted close from one provider with raw close or another provider's return series.
5. Verify the point-in-time membership response on the treatment/event date and preserve the security-by-day output. Norgate documents effective-date membership, but its history of S&P 500 constituent changes before March 2000 is synthetic monthly rebalancing; this does not cover the project's 2008–2020 dates, but must be stated in the provenance record.
6. The frozen matching criteria require industry, market capitalization, beta, liquidity and pre-event returns. Beta, liquidity and pre-event returns may be calculated from validated daily series using locked definitions. Norgate says historical industry and historical fundamentals are not supplied, so historical industry and market capitalization still need a separately reviewed, point-in-time source. Current values must not be used as historical proxies.
7. Compare CTLT adjusted prices against the approved alternative source in one attempt. If reliable adjusted history cannot be obtained, retain CTLT as a documented missing-data case and exclude it from any complete-case benchmark as directed.
8. Freeze provider version/export date and hashes. Since providers may revise history, save the exact source files used for any later approved analysis.

## Blockers and scope

- No complete donor universe or eligibility decisions have been built.
- No Norgate historical sample has been acquired or validated.
- No verified point-in-time market-cap or historical-industry source has been established for the locked screening criteria.
- CTLT remains a missing-data case pending one authorized alternative-source attempt.
- Benchmark remains **blocked** until the source/sample and donor evidence satisfy the lead's conditions and the team approves them.
- The frozen matching criteria and event windows are unchanged. No new firms or experiments are proposed.

## Sources reviewed

- Norgate, [Data Package FAQ](https://norgatedata.com/data-package-faq.php) — trial restrictions; historical membership semantics; available adjustment methods; no historical industry/fundamentals; revision/versioning limitations.
- Norgate, [Data Content Tables](https://norgatedata.com/data-content-tables.php) — S&P 500 constituent history start (March 1957), price coverage details, and note that pre-March-2000 constituent changes are synthetic monthly rebalancing.
- Norgate, [Stock Market Packages](https://norgatedata.com/stockmarketpackages.php) — Platinum and Diamond published coverage.
- EODHD, [Historical EOD API documentation](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes) — sample rows and field definitions.
- EODHD, [Data Methodology](https://eodhd.com/help/methodology) — raw OHLC, adjusted close, split-adjusted volume, adjustments and later corrections.
- EODHD, [Fundamentals and index components documentation](https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds) — S&P 500 historical membership coverage and pre-April-2012 survivorship gap.
- Tiingo, [End-of-day documentation](https://www.tiingo.com/documentation/end-of-day).
- OHLC.io, [Historical stock prices](https://ohlc.io/data/historical-stock-prices).
- S&P Global Marketplace, [S&P DJI via Xpressfeed](https://www.marketplace.spglobal.com/en/datasets/s-p-dow-jones-indices-via-xpressfeed-%28116%29).

## Review outcome to record

Record the team’s decision on: (a) whether to acquire/obtain a Norgate sample, (b) which separately sourced evidence is acceptable for historical industry and market capitalization, and (c) the final adjustment convention. Until then, retain the formal SCM block.
