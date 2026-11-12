# Preksha Week 3 integration review — 12 November 2026

Reviewed `preksha/week3-benchmarks` at `21b9e385276def6959a6089bf40befc83219e743`
against main `e6d55d1`. Her branch is preserved. This review permits integration
of the documented exploratory implementation, not scientific completion or team
approval of its numerical settings.

## Delivery and actual completion

The branch adds dated OLS event studies, a convex-weight Synthetic Control helper,
VIX classification, acquisition/window/coverage tools, membership evidence and
source/donor audits. The benchmark roster is eight historical additions across
four event clusters; it is distinct from the existing seven-event 2024/2025
example, which is preserved unchanged.

The incoming saved price responses contain 313 sessions each for CRM, FAST, MHK,
SWKS, ETSY and TER; ADS and CTLT have zero. Counts and finite positive adjusted
prices reconcile with the saved SPY session records and quality table. This
checks the saved extraction, not security identity, exchange-calendar completeness,
provider accuracy or point-in-time adjustment provenance. No download or purchase
was performed. Raw inputs, hashes and manifests are preserved locally under
`results/raw/preksha_week3_review_20261112/incoming_raw/`. Raw provider prices are
excluded from the squash-merge tree under the repository's existing raw-data rule;
they remain on her source branch and in local evidence. Reacquisition commands
are in her coverage matrix. Reacquisition is not bytewise archival reproduction.

All eight saved event-level VIX labels, rolling averages and thresholds regenerate
from the provided VIX series. A separate NumPy rolling-convolution/quantile
calculation agrees for every event. This verifies the calculation, not the source
series' provenance or team ratification of the label design. See Cboe's
[historical-data page](https://www.cboe.com/tradable-products/vix/vix-historical-data).

The labels are **event-specific calm/mixed/turbulent**, not daily market-wide
binary labels. They must not be silently fed into `src/real_data/dependence.py`
or mapped to simulation regime IDs. No daily labelled return/residual panel
meeting that diagnostic contract is supplied.

The seven historical classical CAR rows remain **unverified legacy results**:
`data/raw/week3_adjusted_prices.csv` with their original market (^GSPC) inputs is
absent. The fresh SPY-based responses are a different input/benchmark and omit ADS;
they cannot be substituted to claim reproduction of those values. Window and
coverage outputs referring to the absent original combined panel likewise remain
archived claims, not fresh validated outcomes.

No actual Synthetic Control benchmark has run. The donor table is empty and
source/contamination evidence remains unresolved. The helper's known-weight toy
tests are software checks only. Its convex pre-period objective follows the
structure in [Abadie, Diamond and Hainmueller (2010)](https://business.baylor.edu/scott_cunningham/teaching/abadie-diamond-and-hainmuel.pdf);
it implements outcome matching, not the full predictor-selection/inference design.

## Integration corrections

- Preserve main's complete `.gitignore`, Boolean/ID validation, atomic event CSV
  writes, diagnostics and tested positional event-study API. Add the dated API
  alongside it instead of replacing earlier fixes.
- Reject fractional/Boolean offsets and nonfinite selected returns; reject invalid
  prices instead of silently coercing them to missing or producing infinite returns.
- Allow an explicit trading-session index; the classical runner passes the NYSE
  calendar so a missing input row becomes missing, not a shifted event window.
- Validate optimizer weights directly; never clip/renormalize an infeasible
  successful optimizer result into a seemingly valid Synthetic Control.
- Remove an overwritten duplicate VIX classifier and reject invalid dates and
  noninteger/Boolean window settings. Existing valid labels remain unchanged.
- Keep missing-price returns missing in screening calculations, and avoid pandas
  view mutation warnings. Treat empty donor templates as incomplete, preserve
  CTLT in the treated roster, and require the accessed exclusion-reason column.
- Declare pandas for benchmark/test imports and optional acquisition/calendar
  dependencies in `requirements-data.txt`. Existing environment packages are not
  changed. Calendar/acquisition tools need that optional installation.

## Validation and boundaries

The integrated pre-fix suite passed 381 tests. The reviewed suite passes **395
with warnings as errors**, including 14 new integration regression cases. Existing
main's 365 tests remain present, as do Preksha's 16 new tests. Local Python 3.13,
NumPy 2.3.5, pandas 3.0.5, SciPy 1.16.3. Platform/provider reproduction elsewhere
is unverified. Acquisition and external calendar scripts were not executed here;
exchange-calendars/yfinance are not installed in the local test environment.
The calendar reindexing logic is tested with explicit fixture sessions.

The report distinguishes runnable code, archived results and external data gaps.
Full scientific Week 3 completion still requires valid donor evidence/SCM runs,
original classical inputs, an agreed label-to-daily-panel convention and team
Gate 2/3 decisions. No synthetic observations, imputed prices, new event sample,
or silently chosen experimental settings were introduced by this review.
