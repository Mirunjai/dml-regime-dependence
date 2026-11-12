# Week 3 Synthetic Control Donor Screening

**Updated:** 2026-11-12  
**Decision:** all event clusters blocked; no Synthetic Control benchmark was executed.

## Current status supersedes earlier screening notes

The frozen treated roster is eight firms: CRM, FAST, ADS, MHK, SWKS, ETSY, TER and CTLT. Earlier text describing a seven-case donor template as the treated sample was incorrect. CTLT remains the required missing-data case. The branch donor CSV remains its blank template; it has not been populated with unverified names.

Fresh Yahoo/yfinance acquisition produced full 313-session panels for CRM, FAST, MHK, SWKS, ETSY and TER. ADS and CTLT returned no history. Nine exploratory price leads have complete price panels and five returned no history. The lead names and evidence are listed in `docs/week3/donor_eligibility_report.md`; those prices are exploratory data, not approved donors.

The public community membership history provisionally indicates four price-complete leads in an available S&P snapshot: GWW for FAST, COF for ADS, and EBAY for ETSY; LEG is listed in the MHK snapshot but has no Yahoo panel. Official S&P membership corroboration is incomplete. SEC archive index/document access returned HTTP 403, leaving point-in-time SIC, shares outstanding and market capitalization unverified. Contamination review is also incomplete. No candidate clears the eligibility requirements.

For September 2020, the branch snapshot is dated June 22, 74 days before the September 4 announcement. The community changes log records no change between those dates and records September 18 and 21 changes later. Official S&P releases corroborate the June and September endpoints but the whole intervening announcement archive has not been reconciled. Do not treat the June 22 snapshot as conclusive September 4 membership evidence.

## Existing donor queue and evidence

The previously researched lead pairs remain: CRM→NOW/WDAY; FAST→GWW/MSM; ADS→SYF/COF; MHK→TILE/LEG; SWKS→QRVO/CRUS; ETSY→EBAY/SHOP; TER→COHU/FORM. They are a screening queue only. In particular, the presence of a current ticker in an old snapshot does not validate company identity, security type, SIC comparability, market-cap match or freedom from contamination.

Price-only beta versus SPY, median raw close × volume and fit-window adjusted return have been calculated for available lead panels and are saved in `data/processed/week3_price_screening_metrics.csv`. These values are descriptive. ADS has no treated price panel, so its matched treated-relative fit comparison cannot be calculated. Market-cap, SIC, complete treated-relative return matching, official membership and contamination fields remain unresolved.

## Event decisions

- **CRM/FAST, 2008:** blocked. SEC original filing fields, official donor membership and contamination are unresolved; CRM's candidate price leads returned no price history.
- **ADS/MHK, 2013:** blocked. ADS has no Yahoo history; donor SEC/membership/contamination evidence is incomplete.
- **SWKS, 2015:** blocked. The membership snapshot is six days before announcement; authoritative point-in-time donor screening and SEC fields are unresolved.
- **ETSY/TER/CTLT, 2020:** blocked. CTLT has no Yahoo history; June–September membership transition is not fully corroborated; SEC fields and contamination remain unresolved.

The conditional team-lead approval does not permit execution before donor and price validation. Therefore no SCM weights, RMSPE, placebo inference, post/pre RMSPE or concentration result is reported. Do not add firms, alter the frozen sample or change the locked event windows. No data purchase was made.

## Synthetic Control methods limitation

The current helper estimates nonnegative weights summing to one from pre-period outcome fit and reports RMSPE, gaps and weight concentration. It does not choose the donors, set predictor weights, run in-space/in-time placebos, calculate placebo p-values or confidence intervals. These inferential limitations remain even if the data gate later passes. A good pre-fit alone does not establish no-confounding or no-interference assumptions. See `docs/week3/synthetic_control_methods.md` and Abadie, Diamond & Hainmueller (2010), https://doi.org/10.1198/jasa.2009.ap08746; Abadie (2021), https://economics.mit.edu/sites/default/files/publications/jel.20191450.pdf.

## Reproducible evidence

See [the donor eligibility and data quality report](donor_eligibility_report.md) and [the free-source coverage matrix](free_source_coverage_matrix.md). Price extraction and metrics can be regenerated with `scripts/acquire_week3_yahoo_prices.py` and `scripts/build_week3_screening_metrics.py`, respectively.
