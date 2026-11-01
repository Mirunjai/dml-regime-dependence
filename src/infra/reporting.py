
"""Generic tables and plotting for experiment results."""

import csv
import math
from collections.abc import Mapping
from pathlib import Path

import matplotlib

# Allow plots to render without a graphical desktop.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def _validate_columns(columns):
    """Validate table column names."""
    columns = list(columns)

    if not columns:
        raise ValueError("At least one column is required")

    if not all(
        isinstance(column, str) and column
        for column in columns
    ):
        raise ValueError("Column names must be nonempty strings")

    if len(columns) != len(set(columns)):
        raise ValueError("Duplicate column names")

    return columns


def _format_cell(value):
    """Format table cells for presentation only."""
    if value is None:
        return "N/A"

    if isinstance(value, float):
        if not math.isfinite(value):
            return "N/A"
        return f"{value:.4f}"

    return str(value)


def markdown_table(rows, columns):
    """
    Create a Markdown table from dictionaries.

    This does not compute or alter scientific metrics.
    """
    columns = _validate_columns(columns)

    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(
        "---" for _ in columns
    ) + " |"

    lines = [header, divider]

    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError("Rows must be dictionaries")

        formatted = []

        for column in columns:
            value = _format_cell(row.get(column))

            # Prevent values from breaking Markdown tables.
            value = value.replace("|", r"\|")
            value = value.replace("\n", " ")

            formatted.append(value)

        lines.append(
            "| " + " | ".join(formatted) + " |"
        )

    return "\n".join(lines)


def save_csv_table(rows, columns, output_path):
    """
    Save results to CSV without rounding numeric values.

    Presentation rounding belongs in the Markdown renderer,
    not in the machine-readable output.
    """
    columns = _validate_columns(columns)

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns,
        )

        writer.writeheader()

        for row in rows:
            if not isinstance(row, Mapping):
                raise TypeError("Rows must be dictionaries")

            writer.writerow({
                column: row.get(column)
                for column in columns
            })

    return output_path


def save_line_plot(
    x,
    series,
    output_path,
    *,
    title="Experiment diagnostics",
    x_label="Time / observation",
    y_label="Value",
):
    """
    Save a reusable diagnostic plot.

    Parameters
    ----------
    x:
        One-dimensional observation coordinates.

    series:
        Dictionary mapping each line label to its values.

    output_path:
        Destination PNG path.
    """
    x = np.asarray(x, dtype=float)

    if x.ndim != 1 or x.size == 0:
        raise ValueError("x must be a nonempty 1D array")

    if not np.isfinite(x).all():
        raise ValueError("x must contain finite values")

    if not isinstance(series, Mapping) or not series:
        raise ValueError("series must be a nonempty mapping")

    validated_series = {}

    for label, values in series.items():
        values = np.asarray(values, dtype=float)

        if values.ndim != 1 or len(values) != len(x):
            raise ValueError(
                f"Shape mismatch for series: {label}"
            )

        if not np.isfinite(values).all():
            raise ValueError(
                f"Nonfinite values in series: {label}"
            )

        validated_series[label] = values

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(9, 5))

    try:
        for label, values in validated_series.items():
            ax.plot(x, values, label=label)

        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        ax.grid(alpha=0.25)
        ax.legend()

        fig.tight_layout()
        fig.savefig(output_path, dpi=150)

    finally:
        plt.close(fig)

    return output_path
