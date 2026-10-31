
"""Schema and validation for S&P 500 inclusion events."""

import csv
from datetime import date
from pathlib import Path


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
    missing = [key for key in COLUMNS if not event.get(key)]
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    for key in ("announcement_date", "effective_date"):
        date.fromisoformat(event[key])

    if event["event_type"] not in ("addition", "removal"):
        raise ValueError("event_type must be addition or removal")

    if date.fromisoformat(event["announcement_date"]) > date.fromisoformat(
        event["effective_date"]
    ):
        raise ValueError("Announcement cannot follow effective date")

    if not event["source_url"].startswith(("https://", "http://")):
        raise ValueError("A source URL is required")

    return True


def save_events(events, path):
    """Write validated events to a CSV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for event in events:
        validate_event(event)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(events)


if __name__ == "__main__":
    output = Path("data/processed/sp500_events_template.csv")
    save_events([], output)
    print(f"Created empty event-list template: {output}")
