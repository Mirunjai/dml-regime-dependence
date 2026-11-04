"""Qualitative diagnostics must expose labels, missingness and undefined pairs."""
import copy
import csv
import json
import math
from datetime import date, timedelta

import numpy as np
import pytest

from src.real_data.dependence import analyze_dependence, correlation, main


def panel():
    rows = []
    # Orthogonal centered vectors give exactly zero calm correlation; the
    # deliberately shared turbulent pattern gives +1. Labels are fixed first.
    patterns = {"calm": ([1., -1., 1., -1.], [1., 1., -1., -1.]),
                "turbulent": ([1., -1., 1., -1.], [2., -2., 2., -2.])}
    for label_index, (label, patterns) in enumerate(patterns.items()):
        for index, values in enumerate(zip(*patterns)):
            for firm, value in zip(("A", "B"), values):
                rows.append({"date": (date(2026, 1, 1) + timedelta(days=label_index * 4 + index)).isoformat(),
                             "firm_id": firm, "value": value, "regime": label})
    return rows


def analyze(rows, **kwargs):
    return analyze_dependence(rows, min_overlap=3, value_kind="residual",
                              label_source="Mock labels fixed before values; software only",
                              evidence_kind="mock", **kwargs)


def test_hand_computed_calm_turbulent_and_matched_comparison():
    result = analyze(panel())
    assert result["evidence_kind"] == "mock_diagnostic"
    assert result["summaries"]["calm"]["mean_correlation"] == pytest.approx(0)
    assert result["summaries"]["turbulent"]["mean_correlation"] == pytest.approx(1)
    assert result["matched_pair_comparison"]["mean_correlation_difference"] == pytest.approx(1)
    assert result["matched_pair_comparison"]["inferential_standard_error"] is None
    assert result["matched_pair_comparison"]["usable_in_both_regimes"] == 1
    assert all(row["dates"] == 4 for row in result["summaries"].values())
    assert "coverage" not in result


def test_date_alignment_not_row_order_and_numpy_reference():
    rows = panel()[::-1]
    assert analyze(rows) == analyze(panel())
    generator = np.random.default_rng(19)
    for _ in range(20):
        x, y = generator.normal(size=(2, 30))
        assert correlation(x, y) == pytest.approx(np.corrcoef(x, y)[0, 1], abs=1e-14)


def test_explicit_missingness_absent_rows_and_pair_overlap_are_visible():
    rows = panel()
    rows[0]["value"] = ""
    del rows[2]
    result = analyze(rows)
    calm = result["summaries"]["calm"]
    assert calm["explicit_missing_values"] == 1
    assert calm["absent_firm_dates"] == 1
    assert calm["usable_pairs"] == 0
    row = next(item for item in result["pairs"] if item["regime"] == "calm")
    assert row["overlapping_dates"] == 2
    assert row["correlation"] is None
    assert row["reason"] == "insufficient_overlap"
    assert result["matched_pair_comparison"]["usable_in_both_regimes"] == 0


def test_constant_series_is_undefined_never_zero_correlation():
    rows = panel()
    for row in rows:
        if row["firm_id"] == "A":
            row["value"] = 0
    result = analyze(rows)
    assert all(row["correlation"] is None and row["reason"] == "constant_series" for row in result["pairs"])
    assert result["summaries"]["calm"]["mean_correlation"] is None


def test_missing_one_regime_is_recorded_as_unavailable():
    result = analyze([row for row in panel() if row["regime"] == "calm"])
    assert result["summaries"]["turbulent"]["dates"] == 0
    assert result["summaries"]["turbulent"]["usable_pairs"] == 0
    assert result["summaries"]["turbulent"]["mean_correlation"] is None


@pytest.mark.parametrize("field,value", [
    ("value", "nan"), ("value", float("inf")), ("value", True),
    ("date", "20260101"), ("date", "2026-02-30"), ("regime", "guess"),
    ("firm_id", ""),
])
def test_invalid_values_and_labels_never_silently_removed(field, value):
    rows = panel()
    rows[0][field] = value
    with pytest.raises(ValueError):
        analyze(rows)


def test_duplicate_and_conflicting_date_labels_rejected():
    rows = panel()
    with pytest.raises(ValueError, match="Duplicate"):
        analyze(rows + [rows[0]])
    rows[0]["regime"] = "turbulent"
    with pytest.raises(ValueError, match="conflicting"):
        analyze(rows)


def test_extreme_magnitudes_remain_numerically_stable():
    assert correlation([1e308, 2e307, -1e308], [1e308, 2e307, -1e308]) == pytest.approx(1)
    assert correlation([1e-308, 2e-308, 3e-308], [-1e-308, -2e-308, -3e-308]) == pytest.approx(-1)


def test_no_fabricated_p_values_or_pair_iid_standard_errors():
    result = analyze(panel())
    assert all("p_value" not in row and "mcse" not in row for row in result["pairs"])
    assert all("mcse" not in row for row in result["summaries"].values())
    assert any("not independent" in text for text in result["limitations"])


def test_real_data_cli_emits_csv_and_fingerprinted_json_without_touching_input(tmp_path):
    source = tmp_path / "mock_panel.csv"
    rows = panel()
    with source.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    before = source.read_bytes()
    output = tmp_path / "diagnostic"
    assert main(["--panel", str(source), "--min-overlap", "3", "--value-kind", "residual",
                 "--evidence-kind", "mock", "--label-source", "mock external labels",
                 "--output", str(output)]) == 0
    result = json.loads((output / "dependence.json").read_text())
    assert result["evidence_kind"] == "mock_diagnostic"
    assert result["provenance"]["input_sha256"][str(source)]
    assert (output / "pair_correlations.csv").exists()
    assert source.read_bytes() == before
