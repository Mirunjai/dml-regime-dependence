"""Validator for the real-data integration contract (reports/mirun_real_data_requirements.md).

Validates STRUCTURE only: it does not download data, fit labels, estimate anything, or verify a
source claim. Every threshold is an explicit argument; this module invents no default research value.
Reuses the existing event schema (src.real_data.sp500_schema) and the panel columns that
src.real_data.dependence already requires.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

from src.real_data.sp500_schema import validate_event

PANEL_COLUMNS = ("date", "firm_id", "value", "regime")
LABELS = ("calm", "turbulent")
VALUE_KINDS = ("return", "abnormal_return", "residual")


def validate_panel_contract(panel, events, *, value_kind, label_source, window_days,
                            min_nonmissing_share, evidence_kind):
    """Return {"errors": [...], "warnings": [...], "stats": {...}}; never raises on data problems.

    window_days: trading days after the event date that must exist (explicit; team-decided).
    min_nonmissing_share: required share of non-missing values for an event firm in its window.
    evidence_kind: 'real' or 'synthetic_fixture' (a synthetic fixture must never be reported as real).
    """
    errors, warnings = [], []
    if evidence_kind not in ("real", "synthetic_fixture"):
        raise ValueError("evidence_kind must be 'real' or 'synthetic_fixture'")
    if value_kind not in VALUE_KINDS:
        raise ValueError(f"value_kind must be one of {VALUE_KINDS}")
    if not isinstance(window_days, int) or window_days < 1:
        raise ValueError("window_days must be an explicit positive int")
    if not (0 < min_nonmissing_share <= 1):
        raise ValueError("min_nonmissing_share must be in (0, 1]")
    if not isinstance(label_source, str) or not label_source.strip():
        raise ValueError("label_source (provenance of external regime labels) is required")

    seen, label_by_date, values, dates = set(), {}, defaultdict(dict), set()
    for i, row in enumerate(panel):
        if not isinstance(row, dict) or not set(PANEL_COLUMNS) <= row.keys():
            errors.append(f"row {i}: missing one of {PANEL_COLUMNS}")
            continue
        try:
            day = date.fromisoformat(row["date"]).isoformat()
        except (TypeError, ValueError):
            errors.append(f"row {i}: date not YYYY-MM-DD")
            continue
        if day != row["date"]:
            errors.append(f"row {i}: date not YYYY-MM-DD")
            continue
        firm = row["firm_id"]
        if not isinstance(firm, str) or not firm.strip():
            errors.append(f"row {i}: empty firm_id")
            continue
        if row["regime"] not in LABELS:
            errors.append(f"row {i}: regime must be one of {LABELS}")
        if (day, firm) in seen:
            errors.append(f"row {i}: duplicate (date, firm_id) {day}/{firm}")
        seen.add((day, firm))
        if label_by_date.setdefault(day, row["regime"]) != row["regime"]:
            errors.append(f"{day}: conflicting regime labels on one calendar date")
        v = row["value"]
        if v in (None, ""):
            values[firm][day] = None
        else:
            try:
                x = float(v)
            except (TypeError, ValueError):
                errors.append(f"row {i}: non-numeric value")
                continue
            if not math.isfinite(x):
                errors.append(f"row {i}: non-finite value")
                continue
            values[firm][day] = x
        dates.add(day)
    if not seen:
        errors.append("panel is empty")
    calendar = sorted(dates)
    checked = 0
    for ev in events:
        try:
            validate_event(ev)
        except ValueError as exc:
            errors.append(f"event {ev.get('firm_id') if isinstance(ev, dict) else ev}: {exc}")
            continue
        firm, eff = ev["firm_id"], ev["effective_date"]
        if firm not in values:
            errors.append(f"event {firm}/{eff}: firm absent from panel")
            continue
        if eff not in dates:
            errors.append(f"event {firm}/{eff}: effective date is not a panel trading date")
            continue
        start = calendar.index(eff)
        window = calendar[start:start + window_days + 1]
        if len(window) < window_days + 1:
            errors.append(f"event {firm}/{eff}: window runs past end of panel")
            continue
        present = [d for d in window if values[firm].get(d) is not None]
        share = len(present) / len(window)
        if share < min_nonmissing_share:
            errors.append(f"event {firm}/{eff}: non-missing share {share:.2f} < {min_nonmissing_share}")
        elif share < 1:
            warnings.append(f"event {firm}/{eff}: {len(window) - len(present)} missing values in window")
        checked += 1
    return {"errors": errors, "warnings": warnings, "evidence_kind": evidence_kind,
            "value_kind": value_kind, "label_source": label_source,
            "stats": {"rows": len(seen), "firms": len(values), "dates": len(dates), "events_checked": checked}}
