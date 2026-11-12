"""Check alignment against the saved pilot and its reviewer reconstruction."""

import pytest

from scripts.sudarshan_week3_report import ROOT, compare_calendar_pilot
from src.evaluation.week3_audit import read_json


@pytest.fixture
def pilot_and_review():
    return (
        read_json(ROOT / "results/week2_mc.json"),
        read_json(ROOT / "results/tables/week3_mirun_verification.json"),
    )


def test_calendar_comparison_surfaces_a_changed_value(pilot_and_review):
    producer, review = pilot_and_review
    rows, comparisons = compare_calendar_pilot(producer, review)
    assert len(rows) == 16
    assert len(comparisons) == 128
    assert all(row["matched"] for row in comparisons)
    assert all((row["empirical_size"] is None) == (row["truth"] != 0) for row in rows)
    review["calendar_summaries"][0]["coverage95"] = 0.5
    _, comparisons = compare_calendar_pilot(producer, review)
    assert [row["field"] for row in comparisons if not row["matched"]] == ["coverage95"]


def test_calendar_comparison_rejects_a_duplicate_cell(pilot_and_review):
    producer, review = pilot_and_review
    review["calendar_summaries"].append(review["calendar_summaries"][0])
    with pytest.raises(ValueError, match="Duplicate replay"):
        compare_calendar_pilot(producer, review)
