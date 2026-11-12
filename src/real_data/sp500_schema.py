
"""Schema and validation for S&P 500 inclusion events."""

import csv
from collections.abc import Mapping
from datetime import date
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


COLUMNS = [
    "firm_id",
    "ticker",
    "company_name",
    "announcement_date",
    "effective_date",
    "event_type",
    "source_url",
]


def validate_event(event):
    """Validate one index membership event."""
    if not isinstance(event, Mapping):
        raise ValueError("Event must be a mapping")
    missing = [key for key in COLUMNS if not isinstance(event.get(key), str) or not event[key].strip()]
    if missing:
        raise ValueError(f"Missing fields: {missing}")
    if set(event) != set(COLUMNS):
        raise ValueError("Unexpected event fields")

    for key in ("announcement_date", "effective_date"):
        if date.fromisoformat(event[key]).isoformat() != event[key]:
            raise ValueError("Dates must use YYYY-MM-DD")

    if event["event_type"] not in ("addition", "removal"):
        raise ValueError("event_type must be addition or removal")

    if date.fromisoformat(event["announcement_date"]) > date.fromisoformat(
        event["effective_date"]
    ):
        raise ValueError("Announcement cannot follow effective date")

    url = urlsplit(event["source_url"])
    if url.scheme not in ("https", "http") or not url.hostname or any(c.isspace() for c in event['source_url']):
        raise ValueError("A source URL is required")

    return True


def save_events(events, path):
    """Validate once, then atomically write; generators and prior files are safe.

    Validating a row/schema does not verify its claims against the source URL.
    This event list is not a daily-return panel or a complete inclusion universe.
    """
    events = list(events)
    path = Path(path)
    seen = set()
    for event in events:
        validate_event(event)
        key = tuple(event[k] for k in ('firm_id', 'announcement_date', 'effective_date', 'event_type'))
        if key in seen:
            raise ValueError("Duplicate event")
        seen.add(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', newline='', encoding='utf-8',
                                         dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(events)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    output = Path("data/processed/sp500_events_template.csv")
    save_events([], output)
    print(f"Created empty event-list template: {output}")
