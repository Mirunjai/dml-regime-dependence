
"""Unit tests for the Synthetic Control estimator."""

import numpy as np
import pytest

from src.benchmarks.synthetic_control import fit_synthetic_control


def sample_data():
    donor_pre = np.array([
        [1.0, 3.0],
        [2.0, 1.0],
        [3.0, 4.0],
        [4.0, 2.0],
        [5.0, 3.0],
    ])

    donor_post = np.array([
        [6.0, 4.0],
        [7.0, 5.0],
    ])

    # Known synthetic weights: 0.7 and 0.3
    treated_pre = donor_pre @ np.array([0.7, 0.3])

    # Add a known post-event effect of 2
    treated_post = donor_post @ np.array([0.7, 0.3]) + 2.0

    return treated_pre, donor_pre, treated_post, donor_post


def fit_sample():
    return fit_synthetic_control(
        *sample_data(),
        donor_ids=["Donor_A", "Donor_B"],
    )


def test_weights_sum_to_one():
    result = fit_sample()
    assert np.isclose(result["weights"].sum(), 1.0)


def test_weights_nonnegative():
    result = fit_sample()
    assert (result["weights"] >= 0).all()


def test_known_weights():
    result = fit_sample()
    np.testing.assert_allclose(
        result["weights"].to_numpy(),
        [0.7, 0.3],
        atol=1e-4,
    )


def test_pre_event_fit():
    result = fit_sample()
    assert result["pre_rmspe"] < 1e-4


def test_known_post_event_effect():
    result = fit_sample()
    np.testing.assert_allclose(
        result["post_gap"],
        [2.0, 2.0],
        atol=1e-4,
    )


def test_missing_values_rejected():
    treated_pre, donor_pre, treated_post, donor_post = sample_data()
    donor_pre[0, 0] = np.nan

    with pytest.raises(ValueError):
        fit_synthetic_control(
            treated_pre,
            donor_pre,
            treated_post,
            donor_post,
            donor_ids=["A", "B"],
        )


def test_mismatched_donor_count_rejected():
    with pytest.raises(ValueError):
        fit_synthetic_control(
            *sample_data(),
            donor_ids=["A"],
        )


def test_duplicate_donor_ids_rejected():
    with pytest.raises(ValueError):
        fit_synthetic_control(
            *sample_data(),
            donor_ids=["A", "A"],
        )
