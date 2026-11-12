"""Tests for src/infra/dml_engine.py. Fixtures here are SYNTHETIC test inputs; the 'approvals' below
exist only to exercise the guard logic and are NOT team approvals."""
import copy
import json
import os
import pytest
from src.infra import dml_engine as E

SMALL = {"n": 120, "T": 60}
PROPOSAL = "configs/mirun_gate3.yaml"


@pytest.fixture(scope="module")
def cfg():
    return E.load_proposal(PROPOSAL)


def synthetic_approved(cfg):
    c = copy.deepcopy(cfg)
    c["approval"] = {k: "SYNTHETIC_TEST_FIXTURE" for k in c["approval"]}
    for path in E.awaiting_paths(c):
        node = c
        for part in path.replace("]", "").replace("[", ".").split("."):
            node = node[int(part)] if isinstance(node, list) else node[part]
        node["approved"] = E.APPROVED_AS_PROPOSED
    c["provenance"]["root_seed"]["approved"] = 12345
    return c


def test_proposal_is_not_runnable_in_production(cfg):
    with pytest.raises(E.ApprovalError):
        E.resolve_parameters(cfg, smoke=False)


def test_each_awaiting_parameter_blocks_production(cfg):
    c = synthetic_approved(cfg)
    c["estimator"]["parameters"]["n_folds"]["approved"] = E.AWAITING
    with pytest.raises(E.ApprovalError, match="n_folds"):
        E.resolve_parameters(c, smoke=False)


def test_production_needs_integer_root_seed(cfg, tmp_path):
    c = synthetic_approved(cfg)
    c["provenance"]["root_seed"]["approved"] = E.APPROVED_AS_PROPOSED   # proposed value is the AWAITING string
    cond = E.make_conditions(c, E.resolve_parameters(c))[0]
    with pytest.raises(E.ApprovalError, match="root_seed"):
        E.run_condition(c, cond, tmp_path / "r", 1, 1)


def test_smoke_cap_and_grid(cfg, tmp_path):
    values = E.resolve_parameters(cfg, smoke=True)
    conds = E.make_conditions(cfg, values)
    assert len(conds) == 3 * 2 * 2 * 2 and len({c["name"] for c in conds}) == len(conds)
    assert {c["tau"] for c in conds if c["kind"] == "zero_effect"} == {0.0}
    with pytest.raises(E.ApprovalError):
        E.run_condition(cfg, conds[0], tmp_path / "x", E.SMOKE_MAX_REPS + 1, 1, smoke=True)


def run_small(cfg, tmp_path, reps=2, idx=0, seed=777):
    values = E.resolve_parameters(cfg, smoke=True)
    cond = E.make_conditions(cfg, values)[idx]
    d = tmp_path / cond["name"]
    n = E.run_condition(cfg, cond, d, reps, seed, smoke=True, overrides=SMALL)
    return d, cond, n


def test_record_schema_seed_and_label(cfg, tmp_path):
    d, cond, n = run_small(cfg, tmp_path)
    assert n == 2
    rec = json.loads((d / "rep_000001.json").read_text())
    assert rec["seed"] == 778 and rec["label"] == "smoke_exploratory" and rec["truth"] == cond["tau"]
    assert [c["cell"] for c in rec["cells"]] == list(E.CELL_MAP)
    assert rec["paired_block_id"] == f"{cond['name']}::rep_000001"
    assert rec["paired_block_status"] in ("complete", "incomplete")
    assert rec["world_sha256"] is None or len(rec["world_sha256"]) == 64
    assert all(c["paired_block_id"] == rec["paired_block_id"] for c in rec["cells"])
    assert all(c["world_sha256"] == rec["world_sha256"] for c in rec["cells"])
    for c in rec["cells"]:
        assert c["status"] in ("ok", "failed") and set(c) >= {"estimate", "lower", "upper", "error"}


def test_resume_does_not_overwrite_and_mixing_refused(cfg, tmp_path):
    d, cond, _ = run_small(cfg, tmp_path)
    p = d / "rep_000000.json"
    before, mtime = p.read_text(), os.stat(p).st_mtime_ns
    assert E.run_condition(cfg, cond, d, 2, 777, smoke=True, overrides=SMALL) == 0
    assert p.read_text() == before and os.stat(p).st_mtime_ns == mtime
    with pytest.raises(ValueError, match="root_seed"):
        E.run_condition(cfg, cond, d, 2, 778, smoke=True, overrides=SMALL)


def test_failures_are_retained_and_counted(cfg, tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("injected failure")
    monkeypatch.setattr(E, "run_dml", boom)
    d, cond, n = run_small(cfg, tmp_path)
    assert n == 2
    rec = json.loads((d / "rep_000000.json").read_text())
    assert all(c["status"] == "failed" and "injected failure" in c["error"] for c in rec["cells"])


def test_aggregate_requires_all_planned_replications(cfg, tmp_path):
    d, _, _ = run_small(cfg, tmp_path)
    (d / "rep_000001.json").unlink()
    with pytest.raises(FileNotFoundError):
        E.aggregate(d)


def test_aggregate_reports_size_for_zero_effect(cfg, tmp_path):
    values = E.resolve_parameters(cfg, smoke=True)
    idx = next(i for i, c in enumerate(E.make_conditions(cfg, values)) if c["kind"] == "zero_effect")
    d, cond, _ = run_small(cfg, tmp_path, reps=3, idx=idx)
    out = E.aggregate(d)
    assert out["truth"] == 0.0 and out["reps"] == 3
    cell = out["cells"]["random_xfit__robust_var"]
    assert cell["attempted"] == 3 and cell["size"] is not None
    assert "grouped_robust_minus_random_robust" in out["paired"]


def test_engine_matches_direct_run_dml_bit_for_bit(cfg, tmp_path):
    """The engine must not alter the unmodified DGP/DML pipeline (synthetic small world)."""
    from research.week2_completion.dgp import build_world
    from research.week2_completion.dml import run_dml
    d, cond, _ = run_small(cfg, tmp_path, reps=1, seed=4242)
    rec = json.loads((d / "rep_000000.json").read_text())
    values = E.resolve_parameters(cfg, smoke=True)
    wcfg = E.world_config(cfg, values, cond, 4242, SMALL)
    rows, _ = run_dml(build_world(wcfg), n_folds=5, seed=4242, alpha=0.05)
    by = {(r["folds"], r["variance"]): r for r in rows}
    for cell in rec["cells"]:
        assert cell["point_estimate"] == by[E.CELL_MAP[cell["cell"]]]["tau"]



def test_guard_scans_entire_config_for_unapproved_fields(cfg):
    c = synthetic_approved(cfg)
    assert E.awaiting_paths(c) == []
    c["analysis_tiers"]["negative_controls"][0]["approved"] = E.AWAITING      # a field outside the parameter sections
    assert any("negative_controls[0]" in p for p in E.awaiting_paths(c))
    with pytest.raises(E.ApprovalError, match="still AWAITING_TEAM_APPROVAL"):
        E.resolve_parameters(c, smoke=False)
    assert len(E.awaiting_paths(cfg)) > 20                                      # the real proposal is fully unapproved

@pytest.mark.parametrize('field', ['gate2','gate3','approved_by','approval_date'])
def test_empty_approval_cannot_enable_production(cfg, field):
    c = synthetic_approved(cfg)
    c['approval'][field] = None
    with pytest.raises(E.ApprovalError):
        E.resolve_parameters(c)


def test_production_arguments_cannot_override_approved_seed_or_count(cfg, tmp_path):
    c = synthetic_approved(cfg)
    condition = E.make_conditions(c, E.resolve_parameters(c))[0]
    with pytest.raises(E.ApprovalError, match='match approved'):
        E.run_condition(c, condition, tmp_path/'bad', 1, 999)
    assert not (tmp_path/'bad').exists()


def test_resume_and_aggregate_reject_tampered_seed(cfg, tmp_path):
    d, condition, _ = run_small(cfg, tmp_path, reps=1)
    path = d/'rep_000000.json'
    record = json.loads(path.read_text()); record['seed'] += 1
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='seed'):
        E.run_condition(cfg, condition, d, 1, 777, smoke=True, overrides=SMALL)
    with pytest.raises(ValueError, match='seed'):
        E.aggregate(d)


def test_run_replication_uses_one_shared_world_for_all_four_cells(cfg, monkeypatch):
    import numpy as np

    values = E.resolve_parameters(cfg, smoke=True)
    condition = E.make_conditions(cfg, values)[0]
    world = {
        "Y": np.array([1.0, 2.0, 3.0, 4.0]),
        "D": np.array([0.0, 1.0, 0.0, 1.0]),
        "X": np.arange(8.0).reshape(4, 2),
        "t0": np.array([0, 1, 2, 3]),
        "idx": np.array([[0], [1], [2], [3]]),
        "cluster_memberships": [(0,), (1,), (0,), (1,)],
    }
    calls = {"build": 0, "dml": 0, "world": None}

    def fake_build_world(wcfg):
        calls["build"] += 1
        return world

    def fake_run_dml(data, **kwargs):
        calls["dml"] += 1
        calls["world"] = data
        return [
            {"folds": fold, "variance": variance, "status": "ok", "tau": 0.5,
             "lo": 0.1, "hi": 0.9, "error": None, "se": 0.2, "n_dependency_pairs": 0}
            for fold, variance in E.CELL_MAP.values()
        ], {"random": 0.1, "grouped": 0.1}

    monkeypatch.setattr(E, "build_world", fake_build_world)
    monkeypatch.setattr(E, "run_dml", fake_run_dml)
    record = E.run_replication(cfg, values, condition, 3, 9000, label="smoke_exploratory", overrides=SMALL)

    assert calls["build"] == 1
    assert calls["dml"] == 1
    assert calls["world"] is world
    assert record["paired_block_status"] == "complete"
    assert len(record["world_sha256"]) == 64
    assert len({cell["paired_block_id"] for cell in record["cells"]}) == 1
    assert len({cell["world_sha256"] for cell in record["cells"]}) == 1


def _force_successful_fixture_cells(record):
    """Make deterministic synthetic intervals for aggregation-contract tests only."""
    for cell in record["cells"]:
        cell.update({"status": "ok", "estimate": 0.2, "lower": 0.1, "upper": 0.3,
                     "error": None, "se": 0.1, "point_estimate": 0.2})
    record["paired_block_status"] = "complete"


def test_paired_contrasts_use_only_complete_four_cell_blocks(cfg, tmp_path):
    d, _, _ = run_small(cfg, tmp_path, reps=3, seed=9100)
    for rep in range(3):
        path = d / f"rep_{rep:06d}.json"
        record = json.loads(path.read_text())
        _force_successful_fixture_cells(record)
        if rep == 0:
            failed = next(c for c in record["cells"] if c["cell"] == "grouped_xfit__robust_var")
            failed.update({"status": "failed", "estimate": None, "lower": None, "upper": None,
                           "error": "synthetic aggregation fixture failure", "se": None})
            record["paired_block_status"] = "incomplete"
        path.write_text(json.dumps(record))
    summary = E.aggregate(d)
    assert summary["paired_audit"]["complete_blocks"] == 2
    assert summary["paired_audit"]["incomplete_blocks"] == 1
    assert summary["paired_audit"]["unverified_blocks"] == 0
    assert summary["paired"]["grouped_robust_minus_random_robust"]["valid_pairs"] == 2


def test_partial_aggregate_reports_not_started_replications(cfg, tmp_path):
    d, _, _ = run_small(cfg, tmp_path, reps=3, seed=9200)
    for rep in range(3):
        path = d / f"rep_{rep:06d}.json"
        record = json.loads(path.read_text())
        _force_successful_fixture_cells(record)
        path.write_text(json.dumps(record))
    (d / "rep_000002.json").unlink()
    with pytest.raises(FileNotFoundError, match="Missing planned replications"):
        E.aggregate(d)
    summary = E.aggregate(d, allow_partial=True)
    assert summary["execution_status"] == "partial"
    assert summary["planned_reps"] == 3
    assert summary["saved_reps"] == 2
    assert summary["not_started_reps"] == 1
    assert summary["paired_audit"]["complete_blocks"] == 2
    assert summary["paired_audit"]["not_started_blocks"] == 1
    assert summary["paired"]["grouped_robust_minus_random_robust"]["valid_pairs"] == 2


def test_legacy_records_without_paired_world_fingerprint_are_not_used_for_pairs(cfg, tmp_path):
    d, _, _ = run_small(cfg, tmp_path, reps=2, seed=9300)
    for rep in range(2):
        path = d / f"rep_{rep:06d}.json"
        record = json.loads(path.read_text())
        _force_successful_fixture_cells(record)
        record.pop("paired_block_id")
        record.pop("world_sha256")
        record.pop("paired_block_status")
        for cell in record["cells"]:
            cell.pop("paired_block_id")
            cell.pop("world_sha256")
        path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="Manifest requires paired-block metadata"):
        E.aggregate(d)
    manifest_path = d / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.pop("paired_block_contract")  # Genuine legacy manifests make no identity promise.
    manifest_path.write_text(json.dumps(manifest))
    summary = E.aggregate(d)
    assert summary["paired_audit"]["unverified_blocks"] == 2
    assert summary["paired_audit"]["complete_blocks"] == 0
    assert "At least two" in summary["paired"]["grouped_robust_minus_random_robust"]["error"]
