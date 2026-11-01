# Four-cell mock infrastructure summary

**Engine:** mock

| cell | cross_fitting | variance | attempted | valid | failed | coverage95 | coverage_mcse | empirical_size | size_mcse | power | power_mcse | mean_ci_width | width_mcse | coverage_lower_all_attempted | coverage_upper_all_attempted | conditional_on_success |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_xfit__naive_var | random | naive | 12 | 12 | 0 | 0.9167 | 0.0798 | 0.0833 | 0.0798 | N/A | N/A | 0.2000 | 0.0000 | 0.9167 | 0.9167 | False |
| random_xfit__robust_var | random | robust | 12 | 12 | 0 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | N/A | N/A | 0.3000 | 0.0000 | 1.0000 | 1.0000 | False |
| grouped_xfit__naive_var | grouped | naive | 12 | 12 | 0 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | N/A | N/A | 0.2200 | 0.0000 | 1.0000 | 1.0000 | False |
| grouped_xfit__robust_var | grouped | robust | 12 | 12 | 0 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | N/A | N/A | 0.3200 | 0.0000 | 1.0000 | 1.0000 | False |

Rates are conditional on successful replications if failures occurred. See failed counts and all-attempted coverage bounds.
