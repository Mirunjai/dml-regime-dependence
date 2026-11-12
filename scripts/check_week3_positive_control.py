"""Fresh-seed recheck of the existing component independence positive control.

This is not an integrated DGP validation or a final Week 3 robustness run.
Reuses the Week 2 diagnostic configuration, labels all settings provisional, and
pins the actual merged regime source. Raw per-panel evidence stays gitignored.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dgp.independence import regime_reference
from src.dgp.validate_volatility import run_independence
from src.evaluation.verification import file_hash, rate_summary
from src.evaluation.week3_audit import provenance, read_json, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiments/deeptanshu_validation.json")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seed < 0 or args.output.exists():
        parser.error("Require a nonnegative seed and a new output directory")
    config = copy.deepcopy(read_json(args.config))
    inputs = [args.config]
    component_paths = [ROOT / name for name in (
        "src/dgp/volatility.py", "src/dgp/independence.py", "src/dgp/validate_volatility.py")]
    for path in component_paths:
        relative = path.relative_to(ROOT).as_posix()
        committed = subprocess.check_output(["git", "-C", str(ROOT), "show", "HEAD:" + relative])
        if path.read_bytes() != committed:
            parser.error("Component source is edited; review/pin it before rechecking")
    inputs += component_paths
    args.output.mkdir(parents=True)
    config["seed"] = args.seed
    config["label"] = "Week 3 component-only fresh-seed corroboration; NOT Gate 3 design or DML robustness results"
    config["independence"]["regime_ref"] = "HEAD"
    # Write this engineering configuration before observing its diagnostic output.
    write_json(args.output / "config.json", config)
    start = provenance(inputs)
    with regime_reference(ROOT, "HEAD", snapshot_dir=args.output / "reference") as (simulator, reference):
        rows, summary = run_independence(config["independence"], config["stability"], args.seed, simulator)
    alpha = config["independence"]["diagnostic_alpha"]
    independent_recomputation = {}
    for key in ("independent", "positive_control"):
        values = [row[key]["p_value"] for row in rows if row["status"] == "ok" and row[key]["p_value"] is not None]
        independent_recomputation[key] = rate_summary(sum(value <= alpha for value in values), len(values))
    end = provenance(inputs)
    if start["input_sha256"] != end["input_sha256"]:
        raise ValueError("Component/config source changed during the recheck")
    summary["interpretation"] = "Actual pinned GARCH/regime component recheck with a deliberately invalid dependence control; no integrated DGP, DML calibration or gate approval"
    report = {"evidence_kind": "actual_component_recheck", "config": config,
              "summary": summary, "independent_rate_recomputation": independent_recomputation,
              "reference": reference, "provenance": end,
              "recheck_script_sha256": file_hash(__file__)}
    write_json(args.output / "independence_replications.json", rows)
    write_json(args.output / "summary.json", report)
    print(f"Saved component positive-control recheck: {args.output / 'summary.json'}")
    return 0 if summary["status"] == "evaluated" else 2


if __name__ == "__main__":
    raise SystemExit(main())
