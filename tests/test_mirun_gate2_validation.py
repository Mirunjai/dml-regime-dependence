from types import SimpleNamespace

import pytest

from scripts.mirun_gate2_validation import (
    event_metrics,
    run_known_truth,
    verify_source_hash,
    wilson_interval,
)


def test_event_metrics_counts_exposure_and_pairs_without_double_counting():
    world = {
        "cluster_memberships": [(0,), (0, 1), (1,), tuple()],
        "cfg": SimpleNamespace(n_regimes=2),
    }
    result = event_metrics(world)
    assert result["exposed_event_share"] == pytest.approx(0.75)
    assert result["shared_pair_density"] == pytest.approx(2 / 6)
    assert result["conditional_shared_pair_density_exposed"] == pytest.approx(2 / 3)
    assert result["multi_regime_event_share"] == pytest.approx(0.25)
    assert result["membership_count_distribution"] == {"0": 1, "1": 2, "2": 1}
    assert result["effective_regimes_inverse_hhi"] == pytest.approx(2.0)


def test_source_hash_is_pinned_to_the_audited_generator():
    assert verify_source_hash() == "47e24f88c4724be4708271931f03492eb968f741"


def test_wilson_interval_has_valid_bounds_and_contains_observed_rate():
    interval = wilson_interval(8, 10)
    assert 0 <= interval[0] <= 0.8 <= interval[1] <= 1


def test_known_truth_control_has_exact_structural_tau_contrast():
    result = run_known_truth([14001, 14002, 14003])
    assert result["all_exact_truth_checks_pass"] is True
    assert result["maximum_absolute_error"] <= 1e-12


def test_controls_execute_actual_generator_and_keep_independent_denominators(monkeypatch):
    from scripts import mirun_gate2_validation as gate
    monkeypatch.setattr(gate, 'N', 80)
    monkeypatch.setattr(gate, 'T', 60)
    result = gate.run_controls([12000, 12001], [13000, 13001])
    for k in ('4', '16'):
        assert result[k]['calibration_worlds'] == result[k]['validation_worlds'] == 2
        for evaluation in result[k]['evaluations'].values():
            assert evaluation['null_validation_false_positive']['trials'] == 2


def test_controls_reject_reused_seeds():
    from scripts.mirun_gate2_validation import run_controls
    with pytest.raises(ValueError, match='disjoint'):
        run_controls([1, 2], [2, 3])


def test_invalid_diagnostics_are_not_counted_as_null_successes():
    import numpy as np
    from scripts.mirun_gate2_validation import rate_summary, independence_metrics, corr
    with pytest.raises(ValueError, match='finite'):
        rate_summary([np.nan, .1], .2)
    with pytest.raises(ValueError, match='constant'):
        corr([1., 1.], [2., 3.])
    with pytest.raises(ValueError, match='no clipping'):
        independence_metrics({'sig_event': np.array([0., 1.]), 'U_win': np.array([1., 2.])})


def test_membership_products_do_not_overflow_at_256_shared_regimes():
    result = event_metrics({'cluster_memberships': [tuple(range(256))]*2,
                            'cfg': SimpleNamespace(n_regimes=256)})
    assert result['shared_pair_density'] == 1.
