"""Validate evidence completeness for the Week 3 SCM donor-screening table.

This checks documentation fields only. It cannot establish historical index
membership, identify contaminated firms, or certify a donor as eligible.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TREATED = {
    "CRM": "2008-09-12",
    "FAST": "2008-09-12",
    "ADS": "2013-12-20",
    "MHK": "2013-12-20",
    "SWKS": "2015-03-11",
    "ETSY": "2020-09-21",
    "TER": "2020-09-21",
    "CTLT": "2020-09-21",
}
REQUIRED_EVIDENCE = [
    "security_type", "us_domicile", "sp500_member_on_event",
    "sp500_membership_source", "sector", "industry",
    "sector_industry_source", "market_cap_usd", "market_cap_date",
    "beta", "beta_window", "beta_source", "median_dollar_volume_usd",
    "liquidity_window", "liquidity_source", "pre_event_return_correlation",
    "return_source", "price_history_start", "price_history_end",
    "price_source", "adjustment_method", "contamination_flag",
    "contamination_source", "eligibility", "reviewer", "review_date",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="?", default="data/processed/week3_donor_candidates.csv")
    args = parser.parse_args()
    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"Missing donor table: {path}")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    required_columns = {"treated_ticker", "event_date", "donor_ticker", "exclusion_reason", *REQUIRED_EVIDENCE}
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise SystemExit("Missing columns: " + ", ".join(missing_columns))

    errors: list[str] = []
    if df.empty:
        errors.append("donor table is empty; no donor screening has been completed")
    allowed_status = {"eligible", "excluded", "pending"}
    for idx, row in df.iterrows():
        line = idx + 2
        treated = row["treated_ticker"].strip()
        if treated not in TREATED or row["event_date"].strip() != TREATED.get(treated):
            errors.append(f"row {line}: unknown treated ticker or event date mismatch")
        donor = row["donor_ticker"].strip().upper()
        if not donor:
            errors.append(f"row {line}: donor_ticker is blank (template row)")
            continue
        if donor in TREATED:
            errors.append(f"row {line}: treated firm {donor} cannot be its own donor")
        missing = [c for c in REQUIRED_EVIDENCE if not row[c].strip()]
        if missing:
            errors.append(f"row {line} ({donor}): missing evidence: {', '.join(missing)}")
        if row["eligibility"].strip().lower() not in allowed_status:
            errors.append(f"row {line} ({donor}): eligibility must be eligible, excluded, or pending")
        if row["sp500_member_on_event"].strip().lower() not in {"yes", "no", "unknown"}:
            errors.append(f"row {line} ({donor}): sp500_member_on_event must be yes/no/unknown")
        if row["contamination_flag"].strip().lower() not in {"yes", "no", "unknown"}:
            errors.append(f"row {line} ({donor}): contamination_flag must be yes/no/unknown")
        if row["security_type"].strip().lower() not in {"common_stock", "other", "unknown"}:
            errors.append(f"row {line} ({donor}): security_type must be common_stock/other/unknown")
        if row["eligibility"].strip().lower() == "eligible":
            if row["security_type"].strip().lower() != "common_stock":
                errors.append(f"row {line} ({donor}): eligible donor must be documented US common stock")
            if row["us_domicile"].strip().lower() != "yes":
                errors.append(f"row {line} ({donor}): eligible donor must have verified US domicile")
            if row["sp500_member_on_event"].strip().lower() != "no":
                errors.append(f"row {line} ({donor}): eligible donor must be verified outside S&P 500 on event date")
            if row["contamination_flag"].strip().lower() != "no":
                errors.append(f"row {line} ({donor}): eligible donor must have contamination review cleared")
            if row["exclusion_reason"].strip():
                errors.append(f"row {line} ({donor}): eligible donor cannot have an exclusion_reason")
        if row["eligibility"].strip().lower() == "excluded" and not row["exclusion_reason"].strip():
            errors.append(f"row {line} ({donor}): excluded donor needs an exclusion_reason")

    if errors:
        print("DONOR SCREEN NOT VALIDATED")
        for error in errors:
            print(f"- {error}")
        return 1
    eligible = df["eligibility"].str.lower().eq("eligible").sum()
    pending = df["eligibility"].str.lower().eq("pending").sum()
    print(f"Documentation checks passed: {len(df)} rows, {eligible} marked eligible, {pending} pending.")
    print("This is not proof of source accuracy, complete price histories, or methodological fit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
