import copy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from src.dgp.independence import (
    conditional_randomization_check, dependence_statistics, positive_control,
    regime_reference,
)
from src.dgp.validate_volatility import component_rng, plot_results, run_independence, run_stability, squared_return_acf, validate_config
from src.dgp.volatility import simulate_volatility

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())["independence"]["regime_ref"]


def mock_regimes(n, density, n_regimes, rng):
    """Test fixture only; actual-component runs use the exact teammate source."""
    active = rng.random(n) < density
    ids = np.where(active, rng.integers(n_regimes, size=n), -1)
    values = rng.standard_normal(n_regimes)
    shocks = np.where(active, values[np.maximum(ids, 0)], 0)
    return ids, shocks


def test_acf_uses_within_firm_boundaries_and_matches_manual_formula():
    returns = np.array([[1, 2, 0, 3], [5, 1, 2, 0]])
    centered = returns**2 - (returns**2).mean(axis=1, keepdims=True)
    expected = np.mean(np.sum(centered[:, 1:] * centered[:, :-1], axis=1) / np.sum(centered**2, axis=1))
    assert squared_return_acf(returns, 1)[1] == pytest.approx(expected)
    assert squared_return_acf(returns, 1)[1] != pytest.approx(squared_return_acf(returns.reshape(1, -1), 1)[1])


def test_degenerate_acf_is_undefined_and_bad_shapes_fail():
    assert np.isnan(squared_return_acf(np.ones((2, 10)), 3)).all()
    with pytest.raises(ValueError):
        squared_return_acf(np.ones((2, 3)), 3)


def test_seed_addressing_is_replayable_and_order_independent():
    first = component_rng(91, 1, 4).standard_normal(10)
    component_rng(91, 2, 4).standard_normal(5000)
    np.testing.assert_array_equal(first, component_rng(91, 1, 4).standard_normal(10))
    assert not np.array_equal(first, component_rng(91, 1, 5).standard_normal(10))
    assert not np.array_equal(first, component_rng(91, 2, 4).standard_normal(10))


def test_dependent_magnitude_can_have_zero_signed_correlation():
    u = np.tile([-2.0, -1, 1, 2], 50)
    h = np.tile(1 + u**2, (2, 1))
    stats = dependence_statistics(h, np.zeros(u.size, dtype=int), u)
    assert abs(stats["signed_shock_lag0"]) < 1e-14
    assert stats["squared_shock_lag0"] > 0.99
    assert stats["exposure_lag0"] is None


def test_positive_control_does_not_mutate_valid_state_and_is_detected():
    sigma, _ = simulate_volatility(8, 256, 0.9, component_rng(19, 1, 0), burn_in=200)
    h = sigma**2
    original = h.copy()
    ids, u = mock_regimes(256, 0.5, 8, component_rng(19, 2, 0))
    dependent = positive_control(h, u)
    np.testing.assert_array_equal(h, original)
    check = conditional_randomization_check(dependent, ids, u, mock_regimes,
        density=0.5, n_regimes=8, rng=component_rng(19, 3, 0), randomizations=39)
    assert check["p_value"] == 1 / 40
    assert check["null_at_least_observed"] == 0
    assert check["associations"]["squared_shock_lag0"] > 0.8


def test_conditional_null_check_replays_and_uses_plus_one_denominator():
    h = np.exp(component_rng(71, 1, 0).standard_normal((3, 128)))
    ids, u = mock_regimes(128, 0.5, 8, component_rng(71, 2, 0))
    kwargs = dict(density=0.5, n_regimes=8, randomizations=19)
    a = conditional_randomization_check(h, ids, u, mock_regimes, rng=component_rng(71, 3, 0), **kwargs)
    b = conditional_randomization_check(h, ids, u, mock_regimes, rng=component_rng(71, 3, 0), **kwargs)
    assert a == b
    assert a["p_value"] == (1 + a["null_at_least_observed"]) / 20


def test_no_variation_is_not_reported_as_independence_pass():
    result = conditional_randomization_check(np.ones((2, 10)), np.full(10, -1),
        np.zeros(10), mock_regimes, density=0, n_regimes=2,
        rng=np.random.default_rng(0), randomizations=19)
    assert result["status"] == "undefined"
    assert result["p_value"] is None
    assert result["randomizations"] == 0
    with pytest.raises(ValueError, match="all-zero"):
        positive_control(np.ones((2, 10)), np.zeros(10))


def test_actual_reference_provenance_and_shapes_without_merging():
    available = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{REFERENCE}:src/dgp/regime_shocks.py"], capture_output=True).returncode == 0
    if not available:
        pytest.skip("Pinned teammate Git object unavailable in this clone")
    with regime_reference(ROOT, REFERENCE) as (simulate, metadata):
        ids, u = simulate(100, 0.5, 5, np.random.default_rng(1))
    assert ids.shape == u.shape == (100,)
    assert (ids >= 0).sum() == 50
    expected = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", f"{REFERENCE}^{{commit}}"], text=True).strip()
    assert metadata["commit"] == expected
    assert len(metadata["source_sha256"]) == 64
    assert "not established" in metadata["team_frozen_status"]


def test_default_reference_works_without_the_original_feature_branch_object(tmp_path):
    source = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{REFERENCE}:src/dgp/regime_shocks.py"])
    repo = tmp_path / "standalone_main"
    target = repo / "src/dgp/regime_shocks.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(source)
    subprocess.run(["git", "init", "--quiet", "--initial-branch=main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "src/dgp/regime_shocks.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Fixture containing only the merged module"], check=True)
    legacy = "17b42c0408b9b512da029f70da3a619706e6649b"
    assert subprocess.run(["git", "-C", str(repo), "cat-file", "-e", legacy], capture_output=True).returncode != 0
    with regime_reference(repo, REFERENCE) as (simulate, metadata):
        ids, shocks = simulate(100, 0.5, 5, np.random.default_rng(1))
    assert ids.shape == shocks.shape == (100,)
    assert (ids >= 0).sum() == 50
    assert metadata["commit"] != legacy


def test_configuration_rejects_typos_and_impossible_regime_checks():
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())
    validate_config(config)
    wrong = copy.deepcopy(config)
    wrong["stability"]["persistnce"] = [0.5]
    with pytest.raises(ValueError, match="Stability keys"):
        validate_config(wrong)
    wrong = copy.deepcopy(config)
    wrong["independence"]["density"] = 0.001
    with pytest.raises(ValueError, match="enough active"):
        validate_config(wrong)


def test_portable_clis_execute_and_metrics_are_known():
    completed = subprocess.run([sys.executable, "-m", "src.evaluation.metrics"], cwd=ROOT, check=True, text=True, capture_output=True)
    output = json.loads(completed.stdout)
    assert output["summary"]["coverage"]["rate"] == 0.95
    assert output["summary"]["size"]["rate"] == 0.05
    completed = subprocess.run([sys.executable, "-m", "src.dgp.volatility", "--n-firms", "2", "--n-periods", "10"], cwd=ROOT, check=True, text=True, capture_output=True)
    assert json.loads(completed.stdout)["shape"] == [2, 10]


def test_single_period_diagnostic_records_undefined_acf_as_json_null():
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())["stability"]
    config.update(n_firms=1, n_periods=1, acf_lags=0, replications=2, persistence=[0.0], burn_in=0, long_burn_in=1)
    rows, summaries, examples = run_stability(config, 0)
    assert len(rows) == 4 and all(row["status"] == "ok" for row in rows)
    assert all(row["acf"] is None for row in rows)
    assert all(summary["mean_acf"] is None for summary in summaries)
    json.dumps(summaries, allow_nan=False)


def test_no_fourth_moment_is_simulated_but_acf_not_interpreted():
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())["stability"]
    config.update(n_firms=2, n_periods=64, acf_lags=3, replications=2, persistence=[0.995], burn_in=10, long_burn_in=20)
    rows, summaries, _ = run_stability(config, 9)
    assert all(row["status"] == "ok" and row["acf"] is None for row in rows)
    assert all(not summary["finite_fourth_moment"] for summary in summaries)


def test_extreme_returns_are_logged_and_preserved_not_clipped():
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())["stability"]
    config.update(n_firms=2, n_periods=16, acf_lags=3, replications=2, persistence=[0.9], burn_in=10, long_burn_in=20, extreme_threshold_sd=0.1)
    rows, _, _ = run_stability(config, 0)
    first = rows[0]
    sigma, eps = simulate_volatility(2, 16, 0.9, component_rng(0, 0, 0), burn_in=10)
    assert first["extreme_return_count"] == np.sum(np.abs(sigma * eps) > 0.1)
    for event in first["extreme_examples"]:
        assert event["return"] == sigma[event["firm"], event["time"]] * eps[event["firm"], event["time"]]


def test_undefined_independence_checks_mark_the_run_incomplete():
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())
    config["independence"].update(n_firms=2, n_periods=64, burn_in=0, persistence=0.0, replications=2, randomizations=9)
    rows, summary = run_independence(config["independence"], config["stability"], 0, mock_regimes)
    assert summary["independent_undefined"] == 2
    assert summary["false_detection_rate"] is None
    assert summary["status"] == "incomplete"


def test_diagnostic_cli_writes_reproducible_outputs_and_protects_existing_runs(tmp_path):
    command = [sys.executable, "-m", "src.dgp.validate_volatility", "--quick", "--skip-independence",
               "--output-root", str(tmp_path), "--run-name", "test"]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    report = json.loads((tmp_path / "tables/test_quick.json").read_text())
    assert report["independence"]["status"] == "skipped by explicit CLI option"
    assert report["mock_metrics"]["intervals"]["coverage"]["rate"] == 0.95
    assert (tmp_path / "raw/test_quick/source_snapshot.zip").is_file()
    assert (tmp_path / "figures/test_quick_paths.png").is_file()
    assert subprocess.run(command, cwd=ROOT, capture_output=True).returncode == 2


def test_unavailable_actual_component_is_recorded_blocked_with_nonzero_exit(tmp_path):
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())
    config["independence"]["regime_ref"] = "missing-reference-for-diagnostic-test"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    completed = subprocess.run([sys.executable, "-m", "src.dgp.validate_volatility", "--quick",
        "--config", str(path), "--output-root", str(tmp_path), "--run-name", "missing"],
        cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 2
    report = json.loads((tmp_path / "tables/missing_quick.json").read_text())
    assert report["independence"]["status"] == "blocked"
    assert "reason" in report["independence"]


def test_all_numerical_failures_are_reported_even_without_example_series(tmp_path):
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())
    config["stability"]["unconditional_variance"] = 1e308
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    completed = subprocess.run([sys.executable, "-m", "src.dgp.validate_volatility", "--quick", "--skip-independence",
        "--config", str(path), "--output-root", str(tmp_path), "--run-name", "overflow"],
        cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 2
    assert "Traceback" not in completed.stderr
    report = json.loads((tmp_path / "tables/overflow_quick.json").read_text())
    assert all(row["valid"] == 0 and row["failed"] == 3 for row in report["stability"])
    assert (tmp_path / "raw/overflow_quick/stability_replications.csv").is_file()
    assert (tmp_path / "figures/overflow_quick_stability.png").is_file()


def test_plot_with_only_one_usable_panel_does_not_invent_an_mcse(tmp_path):
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())
    summary = {"config": config, "independence": {"status": "skipped"}, "stability": [
        {"persistence": 0.9, "burn_in": burn, "valid": 1,
         "mean_acf": None, "mean_e2": {"n": 1, "mean": 1.0, "mcse": None}}
        for burn in (config["stability"]["burn_in"],config["stability"]["long_burn_in"])]}
    plot_results(summary, [], tmp_path / "figures", "single", tmp_path / "cache")
    assert (tmp_path / "figures/single_stability.png").is_file()


def test_overwrite_removes_obsolete_evidence_and_preserves_user_files(tmp_path):
    command = [sys.executable, "-m", "src.dgp.validate_volatility", "--quick", "--skip-independence",
               "--output-root", str(tmp_path), "--run-name", "replace"]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    raw = tmp_path / "raw/replace_quick"
    # Fixtures representing optional outputs from a previous evaluated check.
    (raw / "independence_replications.json").write_text('[{"old_fixture": true}]')
    (raw / "reference").mkdir()
    (raw / "reference/regime_shocks.py").write_text('# old fixture\n')
    (tmp_path / "figures/replace_quick_independence.png").write_bytes(b'old fixture')
    (raw / "user_notes.txt").write_text('preserve me')
    subprocess.run(command + ["--overwrite"], cwd=ROOT, check=True, capture_output=True, text=True)
    assert not (raw / "independence_replications.json").exists()
    assert not (raw / "reference/regime_shocks.py").exists()
    assert not (tmp_path / "figures/replace_quick_independence.png").exists()
    assert (raw / "user_notes.txt").read_text() == 'preserve me'
    assert (raw / "selected_series.csv").exists()
    # A replacement whose simulations all fail must also remove prior examples.
    config = json.loads((ROOT / "configs/experiments/deeptanshu_validation.json").read_text())
    config["stability"]["unconditional_variance"] = 1e308
    path = tmp_path / "overflow_config.json"
    path.write_text(json.dumps(config))
    completed = subprocess.run(command + ["--overwrite", "--config", str(path)], cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 2
    assert not (raw / "selected_series.csv").exists()
    assert not (tmp_path / "figures/replace_quick_paths.png").exists()
    assert (raw / "user_notes.txt").exists()
