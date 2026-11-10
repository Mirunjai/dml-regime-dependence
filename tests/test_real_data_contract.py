"""SYNTHETIC FIXTURES ONLY. Firm ids 'SYN*' and all returns are artificial; nothing here is financial data."""
import pytest
from src.real_data.panel_contract import validate_panel_contract

KW = dict(value_kind="abnormal_return", label_source="SYNTHETIC_FIXTURE_LABELS_v0", window_days=2,
          min_nonmissing_share=0.8, evidence_kind="synthetic_fixture")


def make_panel(n_days=10, firms=("SYN0001", "SYN0002")):
    days = [f"2000-01-{d:02d}" for d in range(3, 3 + n_days)]
    return [{"date": d, "firm_id": f, "value": 0.001 * (i + 1), "regime": "calm" if i < 5 else "turbulent"}
            for i, d in enumerate(days) for f in firms]


def make_event(firm="SYN0001", eff="2000-01-05"):
    return {"firm_id": firm, "ticker": "SYNA", "company_name": "Synthetic Co", "announcement_date": "2000-01-04",
            "effective_date": eff, "event_type": "addition", "source_url": "https://example.invalid/synthetic"}


def test_clean_synthetic_panel_passes():
    out = validate_panel_contract(make_panel(), [make_event()], **KW)
    assert out["errors"] == [] and out["evidence_kind"] == "synthetic_fixture" and out["stats"]["events_checked"] == 1


@pytest.mark.parametrize("mutate,msg", [
    (lambda p: p.append(dict(p[0])), "duplicate"),
    (lambda p: p.__setitem__(0, {**p[0], "regime": "bull"}), "regime must be"),
    (lambda p: p.__setitem__(0, {**p[0], "date": "01/03/2000"}), "YYYY-MM-DD"),
    (lambda p: p.__setitem__(0, {**p[0], "value": float("inf")}), "non-finite"),
    (lambda p: p.__setitem__(1, {**p[1], "regime": "turbulent"}), "conflicting regime"),
])
def test_structural_errors_are_reported_not_raised(mutate, msg):
    panel = make_panel()
    mutate(panel)
    out = validate_panel_contract(panel, [make_event()], **KW)
    assert any(msg in e for e in out["errors"])


def test_event_problems():
    panel = make_panel()
    out = validate_panel_contract(panel, [make_event(firm="SYN9999")], **KW)
    assert any("absent from panel" in e for e in out["errors"])
    out = validate_panel_contract(panel, [make_event(eff="2000-01-12")], **KW)       # runs past end of panel
    assert any("past end" in e for e in out["errors"])
    out = validate_panel_contract(panel, [make_event(eff="2000-02-01")], **KW)
    assert any("not a panel trading date" in e for e in out["errors"])


def test_missing_data_rule_is_explicit():
    panel = make_panel()
    for r in panel:
        if r["firm_id"] == "SYN0001" and r["date"] in ("2000-01-05", "2000-01-06"):
            r["value"] = None
    out = validate_panel_contract(panel, [make_event()], **KW)
    assert any("non-missing share" in e for e in out["errors"])
    out = validate_panel_contract(panel, [make_event()], **{**KW, "min_nonmissing_share": 0.3})
    assert out["errors"] == [] and out["warnings"]


def test_no_hidden_defaults_and_evidence_label():
    with pytest.raises(TypeError):
        validate_panel_contract(make_panel(), [make_event()], value_kind="return")
    with pytest.raises(ValueError):
        validate_panel_contract(make_panel(), [make_event()], **{**KW, "evidence_kind": "maybe"})
    with pytest.raises(ValueError):
        validate_panel_contract(make_panel(), [make_event()], **{**KW, "label_source": " "})
    assert validate_panel_contract([], [], **KW)["errors"] == ["panel is empty"]
