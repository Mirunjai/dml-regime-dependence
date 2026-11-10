"""Regression tests for the integrated research pipeline review."""
from dataclasses import replace

import numpy as np
import pytest

from research.week2_completion.dgp import Config, build_world, simulate_volatility
from research.week2_completion import dml, run_week2


def test_invalid_multiway_does_not_destroy_valid_naive_estimate():
    y = np.array([1., -2., 1.])
    treatment = np.ones(3)
    result = dml.estimate(y, treatment, [(0,), (0, 1), (1,)], allow_invalid_multiway=True)
    assert result["tau"] == 0
    assert result["se_naive"] == pytest.approx(np.sqrt(6) / 3)
    assert result["se_multiway"] is None
    assert "nonpositive" in result["multiway_error"]


def test_scheme_failure_materializes_all_four_cells_and_keeps_valid_cell(monkeypatch):
    def residuals(*args, **kwargs):
        return np.array([1., -2., 1., 1., -2., 1.]), np.ones(6)
    monkeypatch.setattr(dml, "crossfit", residuals)
    data = {"Y": np.arange(6.), "D": np.ones(6), "X": np.ones((6, 1)),
            "cluster_memberships": [(0,)] * 6}
    rows, runtime = dml.run_dml(data, n_folds=2)
    assert len(rows) == 4
    lookup = {(row["folds"], row["variance"]): row for row in rows}
    assert lookup["random", "naive"]["status"] == "ok"
    assert lookup["random", "multiway"]["status"] == "failed"
    assert all(lookup["grouped", variance]["status"] == "failed" for variance in ("naive", "multiway"))
    assert "components" in lookup["grouped", "naive"]["error"]


@pytest.mark.parametrize("memberships", [[(True,)] * 4, [(1.5,)] * 4, [(-1,)] * 4])
def test_membership_ids_must_not_be_silently_coerced(memberships):
    with pytest.raises((TypeError, ValueError)):
        dml._validate_arrays(np.arange(4.), np.ones(4), np.ones((4, 1)), memberships)


def test_monte_carlo_saves_each_planned_cell_and_denominators(monkeypatch):
    def fail(cfg):
        raise FloatingPointError("injected path failure")
    monkeypatch.setattr(run_week2, "build_world", fail)
    result = run_week2.monte_carlo(2, gamma=0, tau=0, density=.5, K=4)
    assert len(result["records"]) == 8
    assert all(row["status"] == "failed" for row in result["records"])
    assert result["reps_failed"] == 2
    for summary in result["results"].values():
        assert summary["attempted_reps"] == summary["failed_reps"] == 2
        assert summary["successful_reps"] == 0
        assert summary["coverage"] is None


def test_calendar_factor_dependency_is_visible_even_without_regimes():
    data = build_world(Config(n=60, T=20, H=5, density=0, n_regimes=0, gamma=0, seed=8))
    folds = dml.make_folds("grouped", data["cluster_memberships"], 3, np.random.default_rng(8))
    info = dml.audit_folds(data, folds)
    assert info["regime_cross_fold_pairs"] == 0
    assert info["calendar_factor_cross_fold_pairs"] > 0
    assert not info["all_known_sources_fold_pure"]


@pytest.mark.parametrize("field,value", [("gamma", True), ("sigma2_bar", float("inf")),
    ("break_vol_independence", "False"), ("break_treat_independence", 1)])
def test_config_rejects_ambiguous_or_nonfinite_inputs(field, value):
    with pytest.raises((TypeError, ValueError)):
        build_world(replace(Config(), **{field: value}))


def test_research_garch_keeps_its_documented_fixed_alpha_recurrence():
    seed, n, periods = 11, 2, 6
    sigma, z = simulate_volatility(n, periods, .9, np.random.default_rng(seed), burn=0)
    expected_z = np.random.default_rng(seed).standard_normal((n, periods))
    np.testing.assert_array_equal(z, expected_z)
    h = np.ones(n)
    for t in range(periods):
        np.testing.assert_allclose(sigma[:, t] ** 2, h, rtol=1e-14)
        h = .1 + .1 * h * z[:, t] ** 2 + .8 * h


def test_overlap_sandwich_handles_many_memberships_without_exponential_subsets():
    meat, pairs = dml._multiway_meat(np.ones(4), [tuple(range(60))] * 4)
    assert meat == 16
    assert pairs == 6


def test_overlap_pair_formula_matches_direct_adjacency():
    rng = np.random.default_rng(81)
    for _ in range(25):
        memberships = [tuple(k for k in range(5) if rng.random() < .3) for i in range(8)]
        score = rng.normal(size=8)
        expected = sum(score[i] * score[j] for i in range(8) for j in range(8)
                       if i == j or set(memberships[i]) & set(memberships[j]))
        actual, _ = dml._multiway_meat(score, memberships)
        assert actual == pytest.approx(expected, abs=1e-13)


def test_persisted_raw_attempts_survive_numeric_failure(tmp_path, monkeypatch):
    import json
    def broken(cfg):
        raise FloatingPointError("test generation failure")
    monkeypatch.setattr(run_week2, "build_world", broken)
    directory = tmp_path / "raw"
    result = run_week2.monte_carlo(2, 0, 0, .5, 4, raw_dir=directory)
    files = sorted(directory.glob("rep_*.json"))
    assert len(files) == 2
    for i, path in enumerate(files):
        record = json.loads(path.read_text())
        assert record["replication"] == i
        assert len(record["cells"]) == 4
        assert all(row["status"] == "failed" for row in record["cells"])
        assert record["rng_streams"]["vol"]["entropy"] == 20000 + i
    assert result["failed_cell_count"] == 8


def test_cli_uses_requested_configs_and_preserves_every_raw_cell(tmp_path):
    import json
    directory = tmp_path / "run"
    code = run_week2.main(["--reps", "1", "--gamma-values", "0", "--tau-values", "0",
                          "--density", "0", "--K", "0", "--n", "40", "--T", "60",
                          "--H", "2", "--folds", "2", "--gate2-seeds", "1", "--seed", "81",
                          "--out", str(directory / "run.json")])
    payload = json.loads((directory / "run.json").read_text())
    gate2 = json.loads((directory / "gate2.json").read_text())
    assert gate2["base_config"]["n"] == 40 and gate2["base_config"]["T"] == 60
    assert gate2["base_config"]["density"] == 0 and gate2["seeds"] == [81]
    assert gate2["default_gamma_records"][0]["corr_D_Uwin"] is None
    assert len(payload["runs"][0]["records"]) == 4
    assert list((directory / "gamma0_tau0").glob("rep_*.json"))
    assert code == (2 if payload["runs"][0]["failed_cell_count"] else 0)
    with pytest.raises(SystemExit):
        run_week2.main(["--out", str(directory / "run.json")])
