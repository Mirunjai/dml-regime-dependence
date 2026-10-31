import math

import numpy as np
import pytest

from src.evaluation.metrics import (
    binomial_summary, empirical_size, paired_binary_difference,
    replication_budget, summarize_csv, summarize_intervals,
)


def test_exact_known_coverage_and_null_size():
    lower = np.r_[np.full(95, -1.0), np.full(5, 0.1)]
    result = summarize_intervals(lower, np.ones(100), 0)
    assert result.coverage.rate == 0.95
    assert result.size.rate == 0.05
    assert result.coverage.mcse == pytest.approx(math.sqrt(0.95 * 0.05 / 100))
    assert result.size.mcse == pytest.approx(result.coverage.mcse)
    assert result.power is None
    assert result.coverage_bounds_all_attempted == (0.95, 0.95)


def test_closed_boundaries_and_zero_width_intervals():
    result = summarize_intervals([-1, 0, 0], [0, 1, 0], 0)
    assert result.coverage.rate == 1
    assert result.size.rate == 0
    assert result.mean_width == pytest.approx(2 / 3)
    assert result.width_mcse == pytest.approx(1 / 3)


def test_nonzero_truth_rejection_is_power_not_size():
    result = summarize_intervals([-1, 1], [1, 3], 2)
    assert result.coverage.rate == 0.5
    assert result.power.rate == 0.5
    assert result.size is None
    with pytest.raises(ValueError, match="zero true effect"):
        empirical_size([-1], [1], 1)


def test_failures_are_explicit_and_not_null_rejections():
    with pytest.raises(ValueError, match="failed replications"):
        summarize_intervals([-1, np.nan], [1, np.nan], 0, success=[True, False])
    result = summarize_intervals(
        [-1, np.nan, 0.1], [1, np.nan, 1], 0,
        success=[True, False, True], failure_policy="report",
    )
    assert (result.attempted, result.valid, result.failed) == (3, 2, 1)
    assert result.coverage.rate == result.size.rate == 0.5
    assert result.coverage_bounds_all_attempted == (1 / 3, 2 / 3)
    assert result.conditional_on_success


def test_all_failed_is_undefined_not_zero():
    result = summarize_intervals([np.nan], [np.nan], 0, success=[False], failure_policy="report")
    assert result.coverage is result.size is result.mean_width is None
    assert result.coverage_bounds_all_attempted == (0, 1)


@pytest.mark.parametrize("lower,upper,kwargs", [
    ([], [], {}), ([1], [0], {}), ([[0]], [[1]], {}),
    ([0], [1, 2], {}), ([np.nan], [1], {}), ([0], [np.inf], {}),
    ([0], [1], {"success": [1]}), ([0], [1], {"success": [True, True]}),
    ([0], [1], {"failure_policy": "drop"}),
    ([np.nan], [1], {"success": [True], "failure_policy": "report"}),
])
def test_malformed_successful_intervals_are_never_silently_dropped(lower, upper, kwargs):
    with pytest.raises(ValueError):
        summarize_intervals(lower, upper, 0, **kwargs)


@pytest.mark.parametrize("truth", [np.nan, np.inf, True, [0]])
def test_invalid_truth(truth):
    with pytest.raises((TypeError, ValueError)):
        summarize_intervals([-1], [1], truth)


@pytest.mark.parametrize("successes,n", [(0, 10), (10, 10)])
def test_binomial_boundary_mcse_is_not_certainty(successes, n):
    result = binomial_summary(successes, n)
    assert result.mcse == 0
    assert result.wilson95[1] - result.wilson95[0] > 0
    assert 0 <= result.wilson95[0] <= result.wilson95[1] <= 1


@pytest.mark.parametrize("successes,n", [(1, 0), (-1, 3), (4, 3), (True, 3), (1.0, 3)])
def test_binomial_invalid_counts(successes, n):
    with pytest.raises((TypeError, ValueError)):
        binomial_summary(successes, n)


def test_paired_mcse_uses_covariance_and_id_alignment():
    a = {"r1": True, "r2": False, "r3": True, "r4": False}
    b = {"r4": False, "r3": False, "r2": True, "r1": True}
    result = paired_binary_difference(a, b)
    # Paired differences [0,-1,1,0]: sample variance=2/3, mean variance=1/6.
    assert result.difference == 0
    assert result.mcse == pytest.approx(math.sqrt(1 / 6))
    identical = paired_binary_difference(a, a)
    assert identical.difference == identical.mcse == 0


def test_paired_failures_and_missing_ids_report_exclusions():
    a = {1: True, 2: False, 3: None, 4: True}
    b = {1: False, 2: False, 3: True, 5: True}
    with pytest.raises(ValueError, match="Missing/failed"):
        paired_binary_difference(a, b)
    result = paired_binary_difference(a, b, failure_policy="report")
    assert (result.attempted_union, result.common_ids, result.valid_pairs) == (5, 3, 2)
    assert (result.only_a, result.only_b, result.failed_a, result.failed_b) == (1, 1, 1, 0)
    assert result.difference == result.mcse == 0.5
    assert result.conditional_on_joint_success


@pytest.mark.parametrize("a,b", [({}, {}), ({1: True}, {1: True}),
    ({1: 1, 2: True}, {1: True, 2: True}), ({True: True, 2: True}, {1: True, 2: True})])
def test_invalid_paired_inputs(a, b):
    with pytest.raises((TypeError, ValueError)):
        paired_binary_difference(a, b)


def test_replication_budgets_match_hand_calculations():
    assert replication_budget(0.005, 0.95) == 1900
    assert replication_budget(0.005, 0.05) == 1900
    assert replication_budget(0.005) == 10000
    assert replication_budget(0.01, 0.95) == 475
    with pytest.raises(ValueError):
        replication_budget(0)
    with pytest.raises(ValueError):
        replication_budget(0.005, 0)


def test_budget_underflow_and_complex_intervals_raise_clear_errors():
    with pytest.raises(ValueError, match="too small"):
        replication_budget(1e-300)
    with pytest.raises(ValueError, match="real, not complex"):
        summarize_intervals(np.array([1j]), np.array([1 + 1j]), 0)


def test_large_representable_widths_do_not_overflow_mcse():
    result = summarize_intervals([0, 0], [1e300, 3e300], 0)
    assert result.mean_width == pytest.approx(2e300)
    assert result.width_mcse == pytest.approx(1e300)


def test_csv_recomputation_requires_explicit_cells_and_failure_handling(tmp_path):
    path = tmp_path / "raw.csv"
    path.write_text("cell,replication,lower,upper,truth,status\na,0,-1,1,0,ok\na,1,,,0,failed\nb,0,1,2,0,ok\n")
    with pytest.raises(ValueError, match="Multiple cells"):
        summarize_csv(path, 0)
    with pytest.raises(ValueError, match="failed replications"):
        summarize_csv(path, 0, cell="a")
    summary = summarize_csv(path, 0, cell="a", failure_policy="report")
    assert (summary.valid, summary.failed) == (1, 1)
    assert summary.coverage_bounds_all_attempted == (0.5, 1)
    assert summarize_csv(path, 0, cell="b").coverage.rate == 0
    with pytest.raises(ValueError, match="truth does not match"):
        summarize_csv(path, 1, cell="a", failure_policy="report")


def test_csv_duplicate_ids_and_ambiguous_status_are_rejected(tmp_path):
    path = tmp_path / "raw.csv"
    path.write_text("replication,lower,upper,success\n0,-1,1,True\n0,-1,1,True\n")
    with pytest.raises(ValueError, match="unique"):
        summarize_csv(path, 0)
    path.write_text("lower,upper,success,status\n-1,1,true,failed\n")
    with pytest.raises(ValueError, match="not both"):
        summarize_csv(path, 0)


@pytest.mark.parametrize("text", [
    "lower,lower,upper\n-1,-1,1\n",
    "lower,upper\n-1,1,extra\n",
    "lower,upper\n-1\n",
])
def test_ambiguous_or_ragged_csv_is_rejected(tmp_path, text):
    path = tmp_path / "raw.csv"
    path.write_text(text)
    with pytest.raises(ValueError, match="unique|number of fields"):
        summarize_csv(path, 0)


def test_omitted_replication_rows_must_be_materialized_before_reporting():
    with pytest.raises(ValueError, match="materialize missing"):
        summarize_intervals([-1], [1], 0, expected_replications=2, failure_policy="report")
    summary = summarize_intervals([-1, np.nan], [1, np.nan], 0,
        success=[True, False], expected_replications=2, failure_policy="report")
    assert summary.attempted == 2 and summary.failed == 1
    assert summary.coverage_bounds_all_attempted == (0.5, 1)
