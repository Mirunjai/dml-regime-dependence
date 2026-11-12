
import csv

import numpy as np
import pytest

from src.evaluation.metrics import summarize_intervals

from src.infra.reporting import (
    markdown_table,
    save_csv_table,
    save_line_plot,
)


def test_markdown_table():
    rows = [
        {"cell": "random", "coverage": 0.95},
        {"cell": "grouped", "coverage": 0.94},
    ]

    table = markdown_table(
        rows,
        ["cell", "coverage"],
    )

    assert "random" in table
    assert "grouped" in table
    assert "0.9500" in table
    assert "0.9400" in table


def test_markdown_missing_and_special_values():
    rows = [
        {"cell": "a|b", "coverage": None},
    ]

    table = markdown_table(
        rows,
        ["cell", "coverage"],
    )

    assert r"a\|b" in table
    assert "N/A" in table


def test_duplicate_columns_rejected():
    with pytest.raises(ValueError):
        markdown_table(
            [{"cell": "random"}],
            ["cell", "cell"],
        )


def test_csv_saving(tmp_path):
    rows = [
        {
            "cell": "random",
            "coverage": 0.95123456789,
        }
    ]

    path = tmp_path / "results.csv"

    save_csv_table(
        rows,
        ["cell", "coverage"],
        path,
    )

    assert path.exists()

    with path.open(newline="") as file:
        saved = list(csv.DictReader(file))

    assert len(saved) == 1
    assert saved[0]["cell"] == "random"
    assert float(saved[0]["coverage"]) == pytest.approx(
        0.95123456789
    )


def test_empty_csv_has_headers(tmp_path):
    path = tmp_path / "empty.csv"

    save_csv_table(
        [],
        ["cell", "coverage"],
        path,
    )

    with path.open(newline="") as file:
        reader = csv.DictReader(file)

        assert reader.fieldnames == [
            "cell",
            "coverage",
        ]
        assert list(reader) == []


def test_plot_generation(tmp_path):
    path = tmp_path / "plot.png"

    x = np.arange(100)

    save_line_plot(
        x=x,
        series={
            "series_a": np.sin(x / 10),
            "series_b": np.cos(x / 10),
        },
        output_path=path,
        title="Diagnostic test",
    )

    assert path.exists()
    assert path.stat().st_size > 0


def test_plot_rejects_different_lengths(tmp_path):
    with pytest.raises(ValueError):
        save_line_plot(
            x=[0, 1, 2],
            series={"invalid": [1, 2]},
            output_path=tmp_path / "invalid.png",
        )


def test_plot_rejects_nonfinite_values(tmp_path):
    with pytest.raises(ValueError):
        save_line_plot(
            x=[0, 1],
            series={"invalid": [1, np.nan]},
            output_path=tmp_path / "invalid.png",
        )


def test_integration_with_existing_metrics():
    """
    Verify reporting consumes existing scientific metrics
    without recalculating coverage ourselves.
    """
    summary = summarize_intervals(
        lower=[-1.0, 0.5],
        upper=[1.0, 1.5],
        truth=0.0,
    )

    rows = [{
        "cell": "mock",
        "coverage": summary.coverage.rate,
        "size": summary.size.rate,
        "mean_width": summary.mean_width,
    }]

    table = markdown_table(
        rows,
        [
            "cell",
            "coverage",
            "size",
            "mean_width",
        ],
    )

    assert "0.5000" in table
    assert "mock" in table
