"""Repeated read-only audit snapshots while a producer writes raw results.

Example: python -m src.evaluation.monitor --interval 60 --iterations 0 \
  --output-root results/raw/week3-monitor -- --plan plan.json --raw raw.csv \
  --allow-incomplete

Zero iterations means explicitly continuous monitoring; Ctrl-C stops cleanly.
A busy/changing CSV is recorded as an input error, never a successful snapshot.
The producer's data are never modified and incomplete metrics remain labelled.
"""
from __future__ import annotations

import argparse
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from src.evaluation.week3_audit import main as audit_main, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, required=True)
    parser.add_argument("--iterations", type=int, default=1, help="0 explicitly requests continuous monitoring")
    parser.add_argument("--output-root", type=Path, required=True, help="New monitoring session directory")
    parser.add_argument("audit_args", nargs=argparse.REMAINDER, help="Arguments after -- are passed to week3_audit")
    args = parser.parse_args(argv)
    if not math.isfinite(args.interval) or args.interval <= 0 or args.iterations < 0:
        parser.error("interval must be finite and positive; iterations must be >=0")
    audit_args = args.audit_args[1:] if args.audit_args[:1] == ["--"] else args.audit_args
    if not audit_args or any(arg == "--output" or arg.startswith("--output=") for arg in audit_args):
        parser.error("Provide audit arguments after --; the monitor owns --output")
    if args.output_root.exists():
        parser.error("Monitoring session exists; choose a new output-root")
    try:
        args.output_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        parser.error(f"Cannot reserve a new monitoring directory: {exc}")
    snapshots = []
    index = 0
    try:
        while args.iterations == 0 or index < args.iterations:
            index += 1
            output = args.output_root / f"snapshot-{index:06d}"
            try:
                code = audit_main([*audit_args, "--output", str(output)])
            except SystemExit as exc:
                code = int(exc.code or 0)
            snapshots.append({"index": index, "utc": datetime.now(timezone.utc).isoformat(),
                              "audit_exit_code": code, "directory": str(output)})
            write_json(args.output_root / "monitor.json", {
                "snapshots": snapshots, "status": "running", "producer_modified": False,
            })
            if args.iterations and index >= args.iterations:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    write_json(args.output_root / "monitor.json", {
        "snapshots": snapshots, "status": "stopped", "producer_modified": False,
    })
    return snapshots[-1]["audit_exit_code"] if snapshots else 2


if __name__ == "__main__":
    raise SystemExit(main())
