"""Render Week 3 figures and compare saved calendar-pilot summaries."""

import argparse
import math
import os
import platform
import sys
from collections import Counter
from pathlib import Path

from src.evaluation.verification import read_csv
from src.evaluation.week3_audit import provenance, read_json, save_source_snapshot, write_json
from src.infra.ablation_report import MATRIX, save_heatmap
from src.infra.reporting import markdown_table, save_csv_table
from src.infra.reproducibility import software_versions
from src.real_data.sp500_schema import COLUMNS, validate_event

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
CELLS = tuple(cell for row in MATRIX for cell in row)
PILOT_CELLS = dict(zip(("random/naive", "random/multiway", "grouped/naive", "grouped/multiway"), CELLS))
FIELDS = {
    "successful_reps": "valid",
    "coverage": "coverage95",
    "mc_se_coverage": "coverage_mcse",
    "empirical_size": "empirical_size",
    "mc_se_size": "size_mcse",
    "mean_interval_width": "mean_ci_width",
    "bias": "bias",
    "rmse": "rmse",
}
TABLE_FIELDS = (
    "scenario", "K", "density_setting", "truth", "cell", "planned", "valid", "failed",
    "missing", "coverage95", "coverage_mcse", "empirical_size", "size_mcse", "power",
    "power_mcse", "mean_ci_width", "bias", "rmse",
)


def compare_calendar_pilot(producer, review):
    """Align the archived producer's calendar variant with the saved replay."""
    if producer["schema_version"] != 1 or review["evidence_kind"] != "reviewer_reconstruction_of_exploratory_pilots":
        raise ValueError("Expected the archived calendar pilot and a reviewer reconstruction")
    records = review["calendar_summaries"]
    replay = {(row["scenario"], row["cell"]): row for row in records}
    if len(replay) != len(records):
        raise ValueError("Duplicate replay scenario and cell")

    rows, comparisons = [], []
    for run in producer["runs"]:
        if run["results"].keys() != PILOT_CELLS.keys():
            raise ValueError("Expected all four calendar-pilot cells")
        scenario = f"gamma{run['gamma']:g}_tau{run['tau']:g}"
        for original, cell in PILOT_CELLS.items():
            if (scenario, cell) not in replay:
                raise ValueError(f"Missing or duplicate pilot cell in {scenario}")
            row = replay.pop((scenario, cell))
            if row["truth"] != run["tau"] or row["planned"] != run["reps_requested"]:
                raise ValueError(f"Pilot truth or planned denominator mismatch in {scenario}")
            rows.append({**row, "K": run["K"], "density_setting": run["density_setting"]})
            for published, field in FIELDS.items():
                expected = run["results"][original][published]
                observed = row[field]
                matches = (
                    expected == observed if field == "valid" or None in (expected, observed)
                    else math.isclose(expected, observed, rel_tol=1e-10, abs_tol=1e-12)
                )
                comparisons.append(dict(scenario=scenario, cell=cell, field=field,
                                        published=expected, replay=observed, matched=matches))
    if replay or not rows:
        raise ValueError("Unexpected replay cells or empty calendar pilot")
    return rows, comparisons


def save_event_figure(events, output):
    """Show only timing and counts for the supplied inclusion-event sample."""
    for event in events:
        validate_event(event)
    identities = {(e["firm_id"], e["announcement_date"], e["effective_date"]) for e in events}
    if not events or len(identities) != len(events) or any(e["event_type"] != "addition" for e in events):
        raise ValueError("Expected a nonempty list of unique inclusion events")
    batches = Counter((e["announcement_date"], e["effective_date"]) for e in events)
    labels = [f"{announced} to {effective}" for announced, effective in sorted(batches)]
    counts = [batches[key] for key in sorted(batches)]
    fig, ax = plt.subplots(figsize=(8, max(2.8, 0.45 * len(labels) + 1.7)))
    try:
        bars = ax.barh(labels, counts, color="#267a78")
        ax.bar_label(bars, padding=4)
        ax.set_xlim(0, max(counts) * 1.2)
        ax.invert_yaxis()
        ax.set_title("S&P 500 additions in the verified event sample")
        ax.set_xlabel("Number of additions")
        ax.set_ylabel("Announcement to effective date")
        fig.tight_layout()
        fig.savefig(output, dpi=150)
    finally:
        plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", required=True, type=Path)
    parser.add_argument("--replay-summary", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New report directory")
    args = parser.parse_args(argv)
    review = read_json(args.replay_summary)
    rows, comparisons = compare_calendar_pilot(read_json(args.pilot), review)
    events = read_csv(args.events, COLUMNS)

    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    save_event_figure(events, out / "sp500_inclusion_batches.png")
    save_csv_table(rows, TABLE_FIELDS, out / "calendar_pilot.csv")
    save_csv_table(comparisons, list(comparisons[0]), out / "pilot_comparison.csv")
    paired = review["central_paired_comparisons"]["calendar"]
    save_csv_table(paired, list(paired[0]), out / "paired_robust_comparisons.csv")
    widths = [row["mean_ci_width"] for row in rows if row["mean_ci_width"] is not None]
    width_max = max(widths, default=0)
    sections = [
        "# Exploratory calendar DML pilot",
        "Values come from the saved reviewer reconstruction. Each cell gives "
        "95% interval coverage, empirical size or power, mean interval width, "
        "and valid/planned replications. Rates use successful replications. The CSV includes "
        "Monte Carlo errors and separate failed and missing counts.",
    ]
    for scenario in dict.fromkeys(row["scenario"] for row in rows):
        group = [row for row in rows if row["scenario"] == scenario]
        by_cell = {row["cell"]: row for row in group}
        gamma, truth = scenario.removeprefix("gamma").split("_tau")
        rate, label = ("empirical_size", "Empirical size") if group[0]["truth"] == 0 else ("power", "Power")
        table = []
        for fold, cells in zip(("Random", "Grouped"), MATRIX):
            entries = []
            for cell in cells:
                row = by_cell[cell]
                values = [row["coverage95"], row[rate], row["mean_ci_width"]]
                summary = " / ".join("N/A" if value is None else f"{value:.3f}" for value in values)
                entries.append(f"{summary} ({row['valid']}/{row['planned']})")
            table.append({"Folds": fold, "Naive variance": entries[0], "Robust variance": entries[1]})
        sections.extend([
            f"## γ={gamma} and τ={truth}",
            f"Coverage / {label.lower()} / mean interval width (valid/planned)",
            markdown_table(table, ("Folds", "Naive variance", "Robust variance")),
        ])
        for field, title, limits in (
            ("coverage95", "95% interval coverage", (0, 1)),
            (rate, label, (0, 1)),
            ("mean_ci_width", "Mean interval width", (0, width_max or 1)),
        ):
            save_heatmap(group, field, f"Exploratory pilot (γ={gamma}, τ={truth})\n{title}",
                         out / f"{scenario}_{field}.png", limits=limits)
    (out / "calendar_pilot.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")

    sources = [Path(__file__), *(ROOT / path for path in (
        "src/infra/ablation_report.py", "src/infra/reporting.py",
        "src/infra/reproducibility.py", "src/real_data/sp500_schema.py",
    ))]
    log = provenance([args.pilot, args.replay_summary, args.events], extra_sources=sources)
    command_args = sys.orig_argv[1:] if argv is None else ["-m", "scripts.sudarshan_week3_report", *argv]
    log.update(
        command_argv=[sys.executable, *command_args],
        working_directory=str(Path.cwd()),
        environment={name: os.environ[name] for name in ("MPLBACKEND", "MPLCONFIGDIR") if name in os.environ},
        platform=platform.platform(), software=software_versions(),
        pilot_source_commit=review["source_commit"], replay_environment=review["reviewer_packages"],
        comparison_fields=len(comparisons), discrepancies=sum(not row["matched"] for row in comparisons),
        event_count=len(events), scope="Saved exploratory pilot comparison and descriptive event timing",
    )
    log["source_archive"] = save_source_snapshot(out, log, extra_sources=sources)
    write_json(out / "reproducibility.json", log)
    print(f"{len(comparisons)} compared fields, {log['discrepancies']} discrepancies. Reports in {out}")
    return 2 if log["discrepancies"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
