"""Hand-computed and adversarial cases for the independent Week 3 verifier."""
import copy
import json
import math
import random

import pytest

from src.evaluation.verification import (
    CELLS, audit_results, audit_stability, compare_claims, mean_mcse,
    normalize_records, read_csv, validate_plan,
)
from src.evaluation.week3_audit import (
    audit_manipulation, audit_trace, compare_paired_claims, main, read_json,
)


def fixture(count=4, truth=0.):
    plan = {"schema_version": 1, "evidence_kind": "mock", "failure_policy": "raise",
            "confidence_level": .95, "scenarios": [{"id": "case", "truth": truth,
                "replication_ids": list(range(count)), "role": "primary"}]}
    rows = [{"scenario": "case", "replication": str(i), "cell": cell,
             "panel_id": f"panel-{i}", "truth": truth, "estimate": truth,
             "lower": truth - 1, "upper": truth + 1, "confidence_level": .95,
             "status": "ok", "error": "", "seconds": .1}
            for i in range(count) for cell in CELLS]
    return plan, rows


def test_exact_95_coverage_5_size_and_mcse():
    plan, rows = fixture(100)
    for row in rows:
        if int(row["replication"]) >= 95:
            row.update(lower=.1, upper=1.)
    result = audit_results(rows, plan)
    for summary in result["summaries"]:
        assert summary["coverage95"] == .95
        assert summary["empirical_size"] == .05
        assert summary["coverage_mcse"] == pytest.approx(math.sqrt(.95 * .05 / 100))
        assert summary["size_mcse"] == pytest.approx(math.sqrt(.05 * .95 / 100))
        assert summary["power"] is None
    assert len(result["comparisons"]) == 12


def test_hand_computed_paired_mcse_bias_rmse_and_width():
    plan, rows = fixture()
    flags = {CELLS[1]: [1, 1, 0, 0], CELLS[3]: [1, 0, 1, 0]}
    for row in rows:
        i = int(row["replication"])
        row["estimate"] = [-2., -1., 1., 2.][i]
        if row["cell"] in flags and not flags[row["cell"]][i]:
            row.update(lower=.1, upper=1.)
    result = audit_results(rows, plan)
    summary = result["summaries"][0]
    assert summary["bias"] == 0
    assert summary["bias_mcse"] == pytest.approx(math.sqrt(5 / 6))
    assert summary["rmse"] == pytest.approx(math.sqrt(2.5))
    assert summary["rmse_mcse_delta"] == pytest.approx(math.sqrt(3 / 4) / (2 * math.sqrt(2.5)))
    assert summary["mean_ci_width"] == 2
    assert summary["width_mcse"] == 0
    central = next(item for item in result["comparisons"] if item["central_comparison"] and item["outcome"] == "coverage")
    assert central["difference"] == 0
    assert central["mcse"] == pytest.approx(math.sqrt(1 / 6))
    assert central["valid_pairs"] == 4


def test_endpoints_zero_width_and_nonzero_truth_power():
    plan, rows = fixture(3, truth=2.)
    for row in rows:
        row.update(lower=2., upper=2.)
    result = audit_results(rows, plan)
    for row in result["summaries"]:
        assert row["coverage95"] == row["power"] == 1
        assert row["empirical_size"] is None
        assert row["size_mcse"] is None
        assert row["mean_ci_width"] == 0
        assert row["rmse_mcse_delta"] is None  # delta method undefined at zero MSE
        assert row["coverage_wilson95"][0] < 1


def test_failures_missing_records_and_all_planned_bounds():
    plan, rows = fixture()
    rows[0].update(status="failed", estimate=float("nan"), lower=float("nan"),
                   upper=float("inf"), error="fit failed")
    del rows[4]
    result = audit_results(rows, plan)
    row = result["summaries"][0]
    assert (row["planned"], row["attempted"], row["valid"], row["failed"], row["missing"]) == (4, 3, 2, 1, 1)
    assert row["coverage95"] == 1
    assert row["coverage_lower_all_planned"] == .5
    assert row["coverage_upper_all_planned"] == 1
    assert row["conditional_on_success"]
    assert not result["all_planned_records_present"]
    central = next(item for item in result["comparisons"] if item["a"] == CELLS[0] and item["b"] == CELLS[1])
    assert central["valid_pairs"] == 2
    assert central["excluded_pairs"] == 2


def test_all_failed_never_zero_coverage():
    plan, rows = fixture()
    for row in rows:
        row.update(status="failed", estimate=None, lower=None, upper=None, error="failure")
    result = audit_results(rows, plan)
    for row in result["summaries"]:
        assert row["coverage95"] is row["empirical_size"] is row["bias"] is row["rmse"] is None
        assert row["coverage_lower_all_planned"] == 0
        assert row["coverage_upper_all_planned"] == 1
    assert all(row["mcse"] is None and row["valid_pairs"] == 0 for row in result["comparisons"])


@pytest.mark.parametrize("field,value", [
    ("lower", float("nan")), ("upper", float("inf")), ("estimate", True),
    ("truth", 1.), ("confidence_level", .9), ("status", "success"),
    ("cell", "cell_1"), ("replication", 99), ("scenario", "unknown"),
    ("panel_id", ""), ("seconds", -1), ("estimate", "nonsense"),
])
def test_bad_successful_records_rejected(field, value):
    plan, rows = fixture()
    rows[0][field] = value
    with pytest.raises(ValueError):
        audit_results(rows, plan)


def test_wrong_pairing_duplicate_panel_and_duplicate_record_rejected():
    plan, rows = fixture()
    bad = copy.deepcopy(rows)
    bad[0]["panel_id"] = "different"
    with pytest.raises(ValueError, match="different panel"):
        audit_results(bad, plan)
    bad = copy.deepcopy(rows)
    for row in bad:
        row["panel_id"] = "reused"
    with pytest.raises(ValueError, match="reuse a panel"):
        audit_results(bad, plan)
    with pytest.raises(ValueError, match="Duplicate saved"):
        audit_results(rows + [rows[0]], plan)


@pytest.mark.parametrize("change", [
    lambda p: p.update(schema_version=True),
    lambda p: p.update(evidence_kind="real_data"),
    lambda p: p.update(failure_policy="drop"),
    lambda p: p.update(confidence_level=.90),
    lambda p: p["scenarios"][0].update(replication_ids=[]),
    lambda p: p["scenarios"][0].update(replication_ids=[1, "1"]),
    lambda p: p["scenarios"][0].update(truth=True),
    lambda p: p["scenarios"][0].update(role="invented"),
])
def test_invalid_plans_rejected(change):
    plan, _ = fixture()
    change(plan)
    with pytest.raises(ValueError):
        validate_plan(plan)


def test_no_production_metric_functions_called(monkeypatch):
    from src.evaluation import metrics
    def forbidden(*args, **kwargs):
        raise AssertionError("Production metric implementation called")
    for name in ("summarize_intervals", "binomial_summary", "paired_binary_difference"):
        monkeypatch.setattr(metrics, name, forbidden)
    plan, rows = fixture()
    assert audit_results(rows, plan)["summaries"][0]["coverage95"] == 1


def test_crosscheck_against_existing_metrics_on_randomized_saved_inputs():
    from src.evaluation.metrics import summarize_intervals
    generator = random.Random(4821)
    for truth in (0., .4):
        plan, rows = fixture(51, truth)
        for row in rows:
            estimate = generator.gauss(truth, 1)
            row.update(estimate=estimate, lower=estimate - .8, upper=estimate + .8)
        generator.shuffle(rows)
        result = audit_results(rows, plan)
        for cell in CELLS:
            selected = [r for r in rows if r["cell"] == cell]
            reference = summarize_intervals([r["lower"] for r in selected], [r["upper"] for r in selected], truth)
            independent = next(r for r in result["summaries"] if r["cell"] == cell)
            assert independent["coverage95"] == reference.coverage.rate
            assert independent["coverage_mcse"] == pytest.approx(reference.coverage.mcse)
            assert independent["mean_ci_width"] == pytest.approx(reference.mean_width)
            assert independent["width_mcse"] == pytest.approx(reference.width_mcse, abs=1e-15)


def test_claims_check_counts_and_numbers_and_undefined_values():
    plan, rows = fixture()
    report = audit_results(rows, plan)
    claims = copy.deepcopy(report["summaries"])
    assert compare_claims(report, claims)["status"] == "matched"
    claims[0]["coverage95"] = .9
    claims[0]["valid"] = 3
    claims[1]["coverage_mcse"] = float("nan")
    result = compare_claims(report, claims)
    assert {row["field"] for row in result["discrepancies"]} == {"coverage95", "valid", "coverage_mcse"}
    with pytest.raises(ValueError):
        compare_claims(report, claims + [claims[0]])
    assert compare_claims(report, [])['status'] == "discrepancies"


def test_paired_claims_catch_direction_and_mcse_errors():
    plan, rows = fixture()
    report = audit_results(rows, plan)
    claims = [copy.deepcopy(row) for row in report["comparisons"] if row["central_comparison"]]
    assert compare_paired_claims(report, claims)["status"] == "matched"
    claims[0]["direction"] = "b_minus_a"
    claims[1]["mcse"] = .01
    assert {row["field"] for row in compare_paired_claims(report, claims)["discrepancies"]} == {"direction", "mcse"}


def test_extreme_numerics_stable_or_explicitly_rejected():
    assert mean_mcse([1e308, 1e308]) == (1e308, 0.)
    assert mean_mcse([-1e308, 1e308]) == pytest.approx((0., 1e308))
    plan, rows = fixture()
    rows[0].update(lower=-1e308, upper=1e308)
    with pytest.raises(ValueError, match="width"):
        audit_results(rows, plan)
    screen = audit_stability(rows)
    assert screen["counts"]["unrepresentable_interval_width"] == 1


def test_stability_counts_and_trace_examples_do_not_drop_extremes():
    plan, rows = fixture(120)
    for row in rows:
        row["estimate"] = 1000
    screen = audit_stability(rows, absolute_estimate_limit=10)
    assert screen["counts"]["extreme_estimate_review_flag"] == 480
    assert screen["flagged_records"] == 480
    assert len(screen["examples"]) == 100
    assert screen["examples_truncated"]
    trace = [{"scenario": "case", "replication": "0", "cell": CELLS[0],
              "component": "garch", "quantity": "variance", "value": value}
             for value in (1, -1, 0, "nan")]
    result = audit_trace(trace)
    assert result["counts"]["nonpositive_variance"] == 2
    assert result["counts"]["nonfinite_or_malformed"] == 1
    assert len(result["examples"]) == 3


def test_manipulation_checks_are_per_cell_and_use_supplied_thresholds_only():
    plan, _ = fixture()
    assert audit_manipulation([], plan)["status"] == "pending"
    plan["manipulation_checks"] = [{"name": "mock_correlation", "operator": ">=",
                                    "threshold": .5, "scenarios": ["case"]}]
    rows = [{"scenario": "case", "cell": cell, "diagnostic": "mock_correlation", "value": .6} for cell in CELLS]
    assert audit_manipulation(rows, plan)["status"] == "evaluated"
    rows[0]["value"] = .4
    result = audit_manipulation(rows[:-1], plan)
    assert result["status"] == "review"
    assert {row["status"] for row in result["records"]} == {"pass", "review", "missing"}


def write_case(tmp_path):
    import csv
    plan, rows = fixture()
    plan_path, raw_path = tmp_path / "plan.json", tmp_path / "raw.csv"
    plan_path.write_text(json.dumps(plan))
    with raw_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return plan, rows, plan_path, raw_path


def test_cli_preserves_inputs_and_writes_partial_denominators(tmp_path):
    plan, rows, plan_path, raw_path = write_case(tmp_path)
    before = raw_path.read_bytes()
    output = tmp_path / "out"
    assert main(["--plan", str(plan_path), "--raw", str(raw_path), "--output", str(output)]) == 0
    report = read_json(output / "audit.json")
    assert report["all_records_successful"]
    assert report["claims_comparison"]["status"] == "not_supplied"
    assert report["gate_approval"] == "Not granted by this verifier"
    assert raw_path.read_bytes() == before
    assert (output / "audit.md").exists()


def test_cli_allow_incomplete_cannot_hide_claim_discrepancy(tmp_path):
    plan, rows, plan_path, raw_path = write_case(tmp_path)
    claims_path = tmp_path / "claims.json"
    claims = audit_results(rows, plan)["summaries"]
    claims[0]["coverage95"] = .2
    claims_path.write_text(json.dumps({"summaries": claims}))
    assert main(["--plan", str(plan_path), "--raw", str(raw_path), "--claims", str(claims_path),
                 "--allow-incomplete", "--output", str(tmp_path / "out")]) == 2


@pytest.mark.parametrize("text", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'])
def test_nonstandard_json_rejected(tmp_path, text):
    path = tmp_path / "bad.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        read_json(path)


@pytest.mark.parametrize("text", ["lower,lower\n1,1\n", "lower,upper\n1\n", "lower,upper\n1,2,3\n"])
def test_malformed_csv_rejected(tmp_path, text):
    path = tmp_path / "bad.csv"
    path.write_text(text)
    with pytest.raises(ValueError):
        read_csv(path)


def test_missing_cli_snapshot_is_not_complete_even_with_monitor_flag(tmp_path):
    plan, rows, plan_path, raw_path = write_case(tmp_path)
    lines = raw_path.read_text().splitlines(keepends=True)
    raw_path.write_text("".join(lines[:-1]))
    for index, extra in enumerate(([], ["--allow-incomplete"])):
        output = tmp_path / f"partial-{index}"
        assert main(["--plan", str(plan_path), "--raw", str(raw_path),
                     "--output", str(output), *extra]) == (2 if not extra else 0)
        report = read_json(output / "audit.json")
        assert not report["all_planned_records_present"]
        assert report["summaries"][-1]["missing"] == 1


def test_changing_inputs_are_rejected_before_successful_report(tmp_path, monkeypatch):
    from src.evaluation import week3_audit as module
    plan, rows, plan_path, raw_path = write_case(tmp_path)
    original = module.audit_results
    def changed(*args, **kwargs):
        raw_path.write_text(raw_path.read_text() + "\n")
        return original(*args, **kwargs)
    monkeypatch.setattr(module, "audit_results", changed)
    output = tmp_path / "out"
    assert main(["--plan", str(plan_path), "--raw", str(raw_path), "--output", str(output)]) == 2
    assert not (output / "audit.json").exists()
    assert "changed" in read_json(output / "input_error.json")["error"]


def test_monitor_preserves_snapshots_and_never_writes_producer(tmp_path, monkeypatch):
    from src.evaluation import monitor
    _, _, plan_path, raw_path = write_case(tmp_path)
    before = raw_path.read_bytes()
    monkeypatch.setattr(monitor.time, "sleep", lambda seconds: None)
    output = tmp_path / "monitor"
    assert monitor.main(["--interval", "1", "--iterations", "2", "--output-root", str(output), "--",
                         "--plan", str(plan_path), "--raw", str(raw_path)]) == 0
    state = read_json(output / "monitor.json")
    assert state["status"] == "stopped"
    assert len(state["snapshots"]) == 2
    assert all((output / f"snapshot-{i:06d}" / "audit.json").exists() for i in (1, 2))
    assert raw_path.read_bytes() == before


def test_empty_and_nonfinite_trace_cannot_look_successful():
    assert audit_trace([])["status"] == "not_supplied"
    plan, rows = fixture()
    rows[0].update(status="failed", error="broken engine")
    assert audit_stability(rows)["flagged_records"] == 1


def runner_fixture(root, count=3):
    from src.infra.experiment_runner import run_experiment
    import yaml
    (root / "configs/dgp").mkdir(parents=True)
    (root / "configs/experiments").mkdir(parents=True)
    (root / "configs/dgp/mock.yaml").write_text("treatment:\n  effect_true: 0.0\n")
    config = {"experiment": {"name": "mock"}, "engine": "mock",
              "provenance": {"seed": 42, "dgp_config": "configs/dgp/mock.yaml"},
              "replications": {"count": count},
              "ablation_cells": [
                  {"id": cell, "cross_fitting": "random" if cell.startswith("random") else "grouped",
                   "variance_estimation": "robust" if "robust" in cell else "naive"}
                  for cell in CELLS]}
    path = "configs/experiments/mock.yaml"
    (root / path).write_text(yaml.safe_dump(config))
    return run_experiment(path, repo_root=root)


def test_existing_runner_json_and_report_are_verified_independently(tmp_path):
    from src.infra.ablation_report import generate_report
    from src.evaluation.week3_audit import load_runner_records
    directory = runner_fixture(tmp_path)
    reference = generate_report(directory, repo_root=tmp_path)
    rows, metadata, paths = load_runner_records(directory, "case")
    plan, _ = fixture(3)
    result = audit_results(rows, plan)
    for independent, original in zip(result["summaries"], reference["cells"]):
        for field in ("coverage95", "coverage_mcse", "empirical_size", "size_mcse", "mean_ci_width", "width_mcse"):
            assert independent[field] == pytest.approx(original[field], abs=1e-14)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    out = tmp_path / "independent"
    assert main(["--plan", str(plan_path), "--runner-dir", str(directory),
                 "--claims", reference["outputs"]["json"], "--output", str(out)]) == 0
    assert read_json(out / "audit.json")["claims_comparison"]["status"] == "matched"
    assert len(paths) == 4
    assert metadata["kind"] == "mock"


@pytest.mark.parametrize("field,value", [("truth", False), ("root_seed", True),
                                          ("seed_addresses", {"factors": [True, 0, 0]})])
def test_runner_provenance_tampering_rejected(tmp_path, field, value):
    from src.evaluation.week3_audit import load_runner_records
    directory = runner_fixture(tmp_path)
    path = directory / "rep_000000.json"
    data = read_json(path)
    data[field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_runner_records(directory, "case")


def test_trace_coverage_wrong_scenario_and_duplicate_coordinates():
    plan, _ = fixture()
    row = {"scenario": "case", "replication": "0", "cell": CELLS[0],
           "component": "garch", "quantity": "variance", "value": 1., "coordinate": "firm-0:time-0"}
    partial = audit_trace([row], plan=plan)
    assert partial["status"] == "partial"
    assert partial["cell_attempts_with_trace"] == 1
    assert partial["cell_attempts_without_trace"] == 15
    with pytest.raises(ValueError, match="Duplicate"):
        audit_trace([row, row], plan=plan)
    with pytest.raises(ValueError, match="Unplanned"):
        audit_trace([{**row, "scenario": "other"}], plan=plan)


@pytest.mark.parametrize("bad", [None, "a string", [1], {"cell": "x"}])
def test_invalid_claim_structures_report_clean_errors(bad):
    plan, rows = fixture()
    report = audit_results(rows, plan)
    with pytest.raises(ValueError):
        compare_claims(report, bad)
    with pytest.raises(ValueError):
        compare_paired_claims(report, bad)


def test_saved_source_snapshot_matches_recorded_hashes(tmp_path):
    import hashlib
    import zipfile
    _, _, plan_path, raw_path = write_case(tmp_path)
    output = tmp_path / "out"
    assert main(["--plan", str(plan_path), "--raw", str(raw_path), "--output", str(output)]) == 0
    report = read_json(output / "audit.json")
    source = report["provenance"]["source_archive"]
    assert hashlib.sha256((output / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    with zipfile.ZipFile(output / source["path"]) as archive:
        for name in archive.namelist():
            expected = report["provenance"]["verifier_source_sha256"][name.rsplit("/", 1)[-1]]
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected


def test_claims_cannot_mislabel_truth_power_or_size():
    plan, rows = fixture()
    result = audit_results(rows, plan)
    claims = copy.deepcopy(result["summaries"])
    claims[0]["truth"] = 1e-14
    claims[0]["power"] = .5
    report = compare_claims(result, claims)
    assert {item["field"] for item in report["discrepancies"]} == {"truth", "power"}


def test_success_conditioned_pair_difference_uses_joint_pairs_not_marginal_rates():
    plan, rows = fixture()
    for row in rows:
        replication = int(row["replication"])
        if row["cell"] == CELLS[1]:
            if replication == 0:
                row.update(status="failed", error="A failed")
            elif replication == 1:
                row.update(lower=.1, upper=1.)
        if row["cell"] == CELLS[3] and replication == 3:
            row.update(status="failed", error="B failed")
    result = audit_results(rows, plan)
    central = next(row for row in result["comparisons"] if row["central_comparison"] and row["outcome"] == "coverage")
    assert central["valid_pairs"] == 2
    assert central["difference"] == -.5
    assert central["mcse"] == .5
    a, b = [next(row for row in result["summaries"] if row["cell"] == cell) for cell in (CELLS[1], CELLS[3])]
    assert a["coverage95"] - b["coverage95"] != central["difference"]


def test_actual_simulation_requires_both_claim_sets_and_manipulation(tmp_path):
    import csv
    plan, rows, plan_path, raw_path = write_case(tmp_path)
    plan["evidence_kind"] = "simulation"
    plan["manipulation_checks"] = [{"name": "test_probe", "operator": ">=", "threshold": .5, "scenarios": ["case"]}]
    plan_path.write_text(json.dumps(plan))
    report = audit_results(rows, plan)
    claims_path, paired_path, probes_path = (tmp_path / name for name in ("claims.json", "paired.csv", "probes.csv"))
    claims_path.write_text(json.dumps({"summaries": report["summaries"]}))
    for path, values in ((paired_path, [row for row in report["comparisons"] if row["central_comparison"]]),
                         (probes_path, [{"scenario": "case", "cell": cell, "diagnostic": "test_probe", "value": .6} for cell in CELLS])):
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0]))
            writer.writeheader()
            writer.writerows(values)
    base = ["--plan", str(plan_path), "--raw", str(raw_path)]
    assert main([*base, "--allow-incomplete", "--output", str(tmp_path / "pending")]) == 2
    assert main([*base, "--claims", str(claims_path), "--paired-claims", str(paired_path),
                 "--manipulation", str(probes_path), "--output", str(tmp_path / "matched")]) == 0
    saved = read_json(tmp_path / "matched/audit.json")
    assert saved["claims_comparison"]["status"] == saved["paired_claims_comparison"]["status"] == "matched"
    assert saved["gate_approval"] == "Not granted by this verifier"


@pytest.mark.parametrize("metadata", [{"known_truth": 1.}, {"engine": "mock"}])
def test_wrong_claim_metadata_rejected_before_verifying(tmp_path, metadata):
    plan, rows, plan_path, raw_path = write_case(tmp_path)
    plan["evidence_kind"] = "simulation"
    plan_path.write_text(json.dumps(plan))
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps({"summaries": audit_results(rows, plan)["summaries"], **metadata}))
    output = tmp_path / "out"
    assert main(["--plan", str(plan_path), "--raw", str(raw_path), "--claims", str(claims),
                 "--output", str(output)]) == 2
    assert (output / "input_error.json").exists()
    assert not (output / "audit.json").exists()


def test_monitor_interrupt_and_output_protection(tmp_path, monkeypatch):
    from src.evaluation import monitor
    _, _, plan_path, raw_path = write_case(tmp_path)
    monkeypatch.setattr(monitor.time, "sleep", lambda _: (_ for _ in ()).throw(KeyboardInterrupt()))
    output = tmp_path / "monitor"
    assert monitor.main(["--interval", "1", "--iterations", "0", "--output-root", str(output), "--",
                         "--plan", str(plan_path), "--raw", str(raw_path)]) == 0
    assert len(read_json(output / "monitor.json")["snapshots"]) == 1
    with pytest.raises(SystemExit):
        monitor.main(["--interval", "1", "--output-root", str(output), "--", "--plan", str(plan_path)])


def test_trace_preserves_threshold_exceedance_and_distinguishes_negative_sigma():
    base = {"scenario": "case", "replication": "0", "cell": CELLS[0], "component": "mock"}
    rows = [{**base, "quantity": "return", "value": 13},
            {**base, "quantity": "return", "value": 12},
            {**base, "quantity": "sigma", "value": -1}]
    result = audit_trace(rows, limits={"return": 12})
    assert result["counts"]["extreme"] == 1
    assert result["counts"]["nonpositive_standard_deviation"] == 1
    assert result["counts"]["nonpositive_variance"] == 0
    assert result["examples"][0]["value"] == "13"
    assert rows[0]["value"] == 13


def test_json_overflow_in_unused_metadata_is_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"metadata": 1e10000}')
    with pytest.raises(ValueError, match="Unrepresentable"):
        read_json(path)


def test_invalid_bounds_still_save_aggregate_numerical_pathology_log(tmp_path):
    import csv
    _, rows, plan_path, raw_path = write_case(tmp_path)
    rows[0].update(upper="nan", estimate="inf")
    rows[1].update(upper="nan")
    with raw_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    output = tmp_path / "out"
    assert main(["--plan", str(plan_path), "--raw", str(raw_path), "--output", str(output)]) == 2
    failure = read_json(output / "input_error.json")
    assert failure["saved_output_stability"]["counts"]["invalid_upper"] == 2
    assert failure["saved_output_stability"]["counts"]["invalid_estimate"] == 1
    assert failure["saved_output_stability"]["flagged_records"] == 2
    assert not (output / "audit.json").exists()


def test_audit_output_reservation_race_never_writes_into_another_session(tmp_path, monkeypatch):
    from pathlib import Path
    _, _, plan_path, raw_path = write_case(tmp_path)
    output = tmp_path / "other-session"
    output.mkdir()
    (output / "sentinel").write_text("existing result")
    original = Path.exists
    monkeypatch.setattr(Path, "exists", lambda self: False if self == output else original(self))
    with pytest.raises(SystemExit) as caught:
        main(["--plan", str(plan_path), "--raw", str(raw_path), "--output", str(output)])
    assert caught.value.code == 2
    assert sorted(path.name for path in output.iterdir()) == ["sentinel"]
