"""MOCK contract checks; these are not calibration-performance evidence."""
import copy
import json
from scripts import mirun_dml_size_coverage_calibration as C


def fixture_record():
    cells = [{"cell": name, "status": "ok", "lower": -.1, "upper": 1.1,
              "estimate": .5, "se": .2, "paired_block_id": "block", "world_sha256": "a"*64}
             for name in C.E.CELL_MAP]
    return {"cells": cells, "paired_block_id": "block", "world_sha256": "a"*64,
            "paired_block_status": "complete", "total_seconds": 0.}


def test_naive_failure_excludes_the_entire_paired_world():
    broken = fixture_record()
    broken["cells"][0]["status"] = "failed"
    broken["paired_block_status"] = "incomplete"
    result = C.paired_coverage([fixture_record(), broken], 1.)
    assert result["valid_pairs"] == result["excluded_blocks"] == 1


def test_campaign_retains_raw_attempts_and_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(C.E, "run_replication", lambda *a, **k: copy.deepcopy(fixture_record()))
    path = tmp_path/"screening.json"
    C.main(["--reps", "2", "--out", str(path)])
    result = json.loads(path.read_text())
    assert len(result["conditions"]) == 24
    assert len(list(path.with_suffix("").rglob("rep_*.json"))) == 48
    manifest = json.loads((path.with_suffix("")/"manifest.json").read_text())
    assert manifest["replications_per_condition"] == 2
    assert manifest["evidence_class"] == "EXPLORATORY"
