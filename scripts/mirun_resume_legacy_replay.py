"""Resume an interrupted `replay_mirun_pilots.py` legacy replay (time-boxed).

Uses the original `worker` and the pinned source snapshot already extracted by
the interrupted run. Attempts already saved are skipped; nothing is overwritten.
Usage: python -m scripts.mirun_resume_legacy_replay --dir <replay_dir> --budget-seconds 200
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from scripts import replay_mirun_pilots as rp


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--budget-seconds", type=float, default=200)
    args = ap.parse_args(argv)
    source = args.dir / "calendar" / "source"
    legacy = args.dir / "legacy"
    plan = json.loads((legacy / "replay_plan.json").read_text())
    rp.initialize(source)
    from research.week2_mirun.dgp import Config as LegacyConfig
    unique = {}
    for target in plan["targets"]:
        for r, key in enumerate(target["keys"]):
            cfg = asdict(LegacyConfig(**target["config"], seed=10000 + r))
            assert hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:20] == key
            unique[key] = cfg
    assert len(unique) == plan["unique_configs"], (len(unique), plan["unique_configs"])
    started, done = time.perf_counter(), 0
    for key, cfg in unique.items():
        path = legacy / "attempts" / (key + ".json")
        if path.exists():
            continue
        if time.perf_counter() - started > args.budget_seconds:
            break
        _, attempt = rp.worker(("legacy", key, cfg))
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(attempt))
        tmp.replace(path)
        done += 1
    have = len(list((legacy / "attempts").glob("*.json")))
    print(json.dumps({"saved_this_call": done, "total_saved": have, "planned": len(unique)}))
    return 0 if have == len(unique) else 3


if __name__ == "__main__":
    sys.exit(main())
