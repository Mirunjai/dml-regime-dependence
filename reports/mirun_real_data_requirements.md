# Real-data integration contract (Mirun -> Preksha) — DRAFT, no data fabricated

**State of the repo:** `data/processed/sp500_events_verified.csv` holds a seven-event S&P 500 list (`src/real_data/sp500_schema.py`, 7 columns). There is **no** daily return/residual panel and **no** regime-label file. Preksha owns both. Nothing here supplies, simulates, or implies them. Validation logic: `src/real_data/panel_contract.py`; tests (`tests/test_real_data_contract.py`, 9 tests) use explicitly synthetic fixtures (`SYN*` ids, `example.invalid` URLs, evidence kind `synthetic_fixture`). The seven-event sample is a qualitative check, not Monte Carlo coverage evidence.

## 1. Inputs (what the existing code already fixes)
| Item | Requirement | Source of the rule |
|---|---|---|
| Event table | columns `firm_id, ticker, company_name, announcement_date, effective_date, event_type, source_url`; `event_type` in {addition, removal}; ISO `YYYY-MM-DD`; announcement <= effective; http(s) source URL | `validate_event` |
| Panel | columns `date, firm_id, value, regime`; one row per (date, firm_id); empty `value` = missing | `analyze_dependence`, `validate_panel_contract` |
| Regime label | currently exactly `calm` or `turbulent`; **one label per calendar date** (market-wide) | `analyze_dependence` |
| Value kind | declared as `return`, `abnormal_return` or `residual`; never mixed in one file | `analyze_dependence` |
| Label provenance | non-empty external definition/source (location + version) supplied with the panel | `--label-source` |

## 2. Decisions the repo does not contain (AWAITING ORIGINAL DOCUMENT / TEAM CONFIRMATION)
1. **Security identifier:** `firm_id` stability across ticker changes (PERMNO/CRSP-style vs ticker); the repo only requires a non-empty string.
2. **Return definition:** simple vs log, total vs price, dividend/split adjustment, data vendor, trading calendar.
3. **Market return series** and **abnormal-return/residual definition** (market model, estimation window length, gap before the event). The only repo benchmark is a descriptive OLS market model (`src/benchmarks/event_study.py`, no inference).
4. **Event date:** announcement vs effective date as day 0, and window length `window_days` (the validator takes it as an explicit argument).
5. **Regime labels:** who defines them, from what (volatility threshold, NBER, VIX ...), and whether they use only information available at the date (no look-ahead). Preksha must record this in `label_source`.
6. **Mapping from labels to DML regimes — the key open gap.** The DGP's clustering unit is a set of K regime blocks, with each event window possibly belonging to several (`cluster_memberships`). Real labels are binary market-day labels. Required, undecided: how K regimes and per-event memberships are derived from labels (e.g. maximal runs of `turbulent` days as regimes; an event belongs to every run its window overlaps). The validator does not derive this.
7. **Missing-data rule:** minimum non-missing share per event window (explicit argument `min_nonmissing_share`), and whether missing values are dropped, flagged, or exclude the event.
8. **Exclusion rules:** overlapping windows for the same firm, removals vs additions, delistings, confounding events.

## 3. Validation requirements (implemented, structural only)
Duplicate (date, firm) rows; non-ISO dates; labels outside {calm, turbulent}; conflicting labels for one date; non-finite or non-numeric values; empty panel; event schema errors; event firm absent from panel; effective date not a panel trading date; window running past the panel; non-missing share below the explicit threshold (errors), partial missingness (warnings). It cannot verify that a source URL supports an event, that labels are look-ahead free, or that returns are correct; those need Preksha's audit trail.

## 4. Expected output (proposed; for the team to confirm)
Per event: `event_id` (firm_id + effective_date), `firm_id`, day-0 convention, `window_start`, `window_end`, `value_kind`, `regime_ids` (semicolon-separated, possibly several), `label_source`, `n_missing`, `excluded` with a reason code. Regime-level table: `regime_id`, `start`, `end`, `label`. Plus a frozen-snapshot hash of the panel and the label file so `dependence.py`'s changed-while-reading check applies.

## 5. Not allowed
Using synthetic fixtures, simulated returns, or `evidence_kind=mock` outputs as real-data results; fitting labels on outcomes; reporting coverage from the seven-event sample.
