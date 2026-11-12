"""Diagnostic finite-length sensitivity for squared-return ACF at rho=0.97.

Reuses the standalone simulator/harness. These settings investigate finite-sample
behavior and do not change or lock the project's eventual experimental grid.
"""

import argparse
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dgp.validate_volatility import _csv, _json, _provenance, run_stability, validate_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/deeptanshu_validation.json"))
    parser.add_argument("--output-root", type=Path, default=Path("results"))
    args = parser.parse_args()
    base = json.loads(args.config.read_text())
    validate_config(base)
    raw = args.output_root / "raw/acf_length_sensitivity"
    raw.mkdir(parents=True, exist_ok=True)
    provenance = _provenance(base, raw)
    results = []
    for periods in (1024, 4096, 16384, 65536):
        config = copy.deepcopy(base["stability"])
        config.update(n_firms=16, replications=8, persistence=[0.97], acf_lags=10, n_periods=periods)
        rows, summaries, _ = run_stability(config, base["seed"])
        _csv(raw / f"periods_{periods}.csv", rows)
        results.append({"config": config, "summary": summaries})
        print(f"T={periods}: short-burn lag-1 ACF={summaries[0]['mean_acf'][1]:.6f}", flush=True)
    report = {"label": "Diagnostic finite-length sensitivity; not a design/grid change",
              "seed": base["seed"], "results": results, "source_sha256": provenance["source_sha256"],
              "environment": {key: provenance[key] for key in ("python", "numpy", "platform")}}
    _json(args.output_root / "tables/acf_length_sensitivity.json", report)
    _json(raw / "provenance.json", provenance)
    if any(summary["failed"] for result in results for summary in result["summary"]):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
