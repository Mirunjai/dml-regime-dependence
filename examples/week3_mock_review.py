"""Generate deterministic software fixtures and exercise all Week 3 audit CLIs.

No estimator or financial data: interval outcomes and labels are constructed for
known arithmetic. The production metrics module supplies a separate reference.
All generated raw evidence goes to a new gitignored directory. No commits/pushes.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation.metrics import paired_binary_difference, summarize_intervals
from src.evaluation.verification import CELLS, file_hash
from src.evaluation.week3_audit import write_json


def save_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_fixtures(output):
    plan = {"schema_version": 1, "evidence_kind": "mock", "failure_policy": "raise",
            "confidence_level": .95, "team_design_status": "Software fixture; NOT Gate 3 approval",
            "scenarios": [{"id": name, "truth": truth, "replication_ids": list(range(100)), "role": role}
                          for name, truth, role in (("null", 0., "primary"), ("nonzero", .4, "primary"),
                                                   ("mock_robustness", 0., "robustness"))],
            "manipulation_checks": [{"name": "fixture_contract_probe", "operator": ">=", "threshold": .5,
                                      "scenarios": ["null", "nonzero", "mock_robustness"]}],
            "trace_absolute_limits": {"return": 12.},
            "warning": "All numbers are software test cases; neither DGP settings nor a locked robustness subset."}
    rows, traces, probes = [], [], []
    coverage_counts = [95, 96, 90, 97]
    for scenario in plan["scenarios"]:
        name, truth = scenario["id"], scenario["truth"]
        for index in range(100):
            for cell_index, cell in enumerate(CELLS):
                covers = (index + cell_index * 7) % 100 < coverage_counts[cell_index]
                lower, upper = (truth - .2, truth + .2) if covers else (truth + .3, truth + .7)
                rows.append({"scenario": name, "replication": str(index), "cell": cell,
                             "panel_id": f"{name}-panel-{index}", "truth": truth,
                             "estimate": (lower + upper) / 2, "lower": lower, "upper": upper,
                             "confidence_level": .95, "status": "ok", "error": "", "seconds": .01})
                traces.append({"scenario": name, "replication": str(index), "cell": cell,
                               "component": "mock_fixture", "quantity": "variance", "value": 1., "coordinate": "0"})
        for cell in CELLS:
            probes.append({"scenario": name, "cell": cell, "diagnostic": "fixture_contract_probe", "value": .75})
    claims, paired = [], []
    for scenario in plan["scenarios"]:
        selected = [row for row in rows if row["scenario"] == scenario["id"]]
        for cell in CELLS:
            data = [row for row in selected if row["cell"] == cell]
            summary = summarize_intervals([row["lower"] for row in data], [row["upper"] for row in data], scenario["truth"])
            claims.append({"scenario": scenario["id"], "cell": cell, "planned": 100,
                           "attempted": summary.attempted, "valid": summary.valid, "failed": summary.failed,
                           "missing": 0, "coverage95": summary.coverage.rate, "coverage_mcse": summary.coverage.mcse,
                           "empirical_size": summary.size.rate if summary.size else None,
                           "size_mcse": summary.size.mcse if summary.size else None,
                           "power": summary.power.rate if summary.power else None,
                           "power_mcse": summary.power.mcse if summary.power else None,
                           "mean_ci_width": summary.mean_width, "width_mcse": summary.width_mcse})
        a, b = CELLS[1], CELLS[3]
        for outcome in ("coverage", "empirical_size" if scenario["truth"] == 0 else "power"):
            def outcomes(cell):
                return {row["replication"]: bool(row["lower"] <= scenario["truth"] <= row["upper"])
                        if outcome == "coverage" else bool(row["upper"] < 0 or row["lower"] > 0)
                        for row in selected if row["cell"] == cell}
            reference = paired_binary_difference(outcomes(a), outcomes(b))
            paired.append({"scenario": scenario["id"], "a": a, "b": b, "outcome": outcome,
                           "direction": "a_minus_b", "difference": reference.difference,
                           "mcse": reference.mcse, "valid_pairs": reference.valid_pairs,
                           "planned_pairs": 100, "excluded_pairs": 0})
    panel = []
    for label_index, label in enumerate(("calm", "turbulent")):
        for time in range(64):
            for firm in range(6):
                local = math.sin(2 * math.pi * (firm + 2) * time / 64)
                common = math.sin(2 * math.pi * time / 64)
                value = local if label == "calm" else common + .1 * local
                panel.append({"date": (date(2026, 1, 1) + timedelta(days=64 * label_index + time)).isoformat(),
                              "firm_id": f"mock-{firm}", "value": value, "regime": label})
    write_json(output / "plan.json", plan)
    save_csv(output / "intervals.csv", rows)
    save_csv(output / "claims.csv", claims)
    save_csv(output / "paired_claims.csv", paired)
    save_csv(output / "manipulation_fixture.csv", probes)
    save_csv(output / "numeric_trace.csv", traces)
    save_csv(output / "mock_panel.csv", panel)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Fixture output exists; choose a new name")
    args.output.mkdir(parents=True)
    plan = build_fixtures(args.output)
    audit_command = [sys.executable, "-S", "-m", "src.evaluation.week3_audit",
                     "--plan", str(args.output / "plan.json"), "--raw", str(args.output / "intervals.csv"),
                     "--claims", str(args.output / "claims.csv"), "--paired-claims", str(args.output / "paired_claims.csv"),
                     "--manipulation", str(args.output / "manipulation_fixture.csv"),
                     "--trace", str(args.output / "numeric_trace.csv"), "--output", str(args.output / "audit")]
    diagnostic_command = [sys.executable, "-S", "-m", "src.real_data.dependence",
                          "--panel", str(args.output / "mock_panel.csv"), "--min-overlap", "32",
                          "--value-kind", "residual", "--evidence-kind", "mock",
                          "--label-source", "Deterministic labels fixed before fixture values; not real data",
                          "--output", str(args.output / "dependence")]
    for command in (audit_command, diagnostic_command):
        subprocess.run(command, cwd=ROOT, check=True)
    audit = json.loads((args.output / "audit/audit.json").read_text())
    diagnostic = json.loads((args.output / "dependence/dependence.json").read_text())
    assert audit["claims_comparison"]["status"] == "matched"
    assert audit["paired_claims_comparison"]["status"] == "matched"
    assert audit["all_records_successful"]
    for scenario in plan["scenarios"]:
        cell2 = next(row for row in audit["summaries"] if row["scenario"] == scenario["id"] and row["cell"] == CELLS[1])
        cell4 = next(row for row in audit["summaries"] if row["scenario"] == scenario["id"] and row["cell"] == CELLS[3])
        assert cell2["coverage95"] == .96 and cell4["coverage95"] == .97
    assert abs(diagnostic["summaries"]["calm"]["mean_correlation"]) < 1e-12
    assert diagnostic["summaries"]["turbulent"]["mean_correlation"] > .98
    summary = {
        "evidence_kind": "mock_software_validation", "raw_interval_rows": 1200,
        "scenarios": 3, "four_cell_summaries": len(audit["summaries"]),
        "paired_comparisons": len(audit["comparisons"]),
        "claimed_summaries": audit["claims_comparison"]["status"],
        "central_paired_claims": audit["paired_claims_comparison"]["status"],
        "python_without_site_packages_verified": True,
        "calm_mean_correlation": diagnostic["summaries"]["calm"]["mean_correlation"],
        "turbulent_mean_correlation": diagnostic["summaries"]["turbulent"]["mean_correlation"],
        "commands": [audit_command, diagnostic_command],
        "source_sha256": {str(path.relative_to(ROOT)): file_hash(path) for path in (
            Path(__file__), ROOT / "src/evaluation/verification.py", ROOT / "src/evaluation/week3_audit.py",
            ROOT / "src/real_data/dependence.py")},
        "limitations": "Constructed intervals and synthetic panel; not Mirun pilot results, real-data evidence or actual robustness results.",
    }
    write_json(args.output / "software_validation.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
