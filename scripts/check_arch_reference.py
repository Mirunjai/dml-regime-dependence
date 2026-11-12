"""Optional parity check against a separate official bashtage/arch source clone.

Requires that clone's dependencies (pandas, SciPy, statsmodels) in the interpreter.
No source is copied into this repository or edited. An unbuilt clone lacks its
generated version file; a temporary in-process metadata module supplies only
version strings, leaving the scientific implementation unchanged.
"""

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile
import types

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dgp.volatility import garch_parameters, simulate_volatility


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if not (source / "arch/univariate/volatility.py").exists():
        parser.error("--source must be the official arch repository root")
    if "arch" in sys.modules:
        raise RuntimeError("Run in a fresh process so the selected source is unambiguous")
    shim = not (source / "arch/_version.py").exists()
    if shim:
        metadata = types.ModuleType("arch._version")
        metadata.version = f"0+source.{commit[:8]}"
        metadata.version_tuple = (0, "source")
        sys.modules["arch._version"] = metadata
    sys.path.insert(0, str(source))
    os.environ["ARCH_DISABLE_NUMBA"] = "1"
    with tempfile.TemporaryDirectory(prefix="ada-arch-plot-cache-") as cache:
        os.environ.setdefault("MPLCONFIGDIR", cache)
        from arch.univariate import GARCH

        cases = []
        for rho in (0.0, 0.3, 0.9, 0.97):
            for variance in (0.0004, 1.0):
                for burn in (0, 500):
                    params = garch_parameters(rho, unconditional_variance=variance)
                    sigma, eps = simulate_volatility(1, 2048, rho, np.random.default_rng(7),
                        burn_in=burn, unconditional_variance=variance)
                    reference_returns, reference_h = GARCH(1, 0, 1).simulate(
                        [params.omega, params.alpha, params.beta], 2048,
                        np.random.default_rng(7).standard_normal, burn=burn, initial_value=variance)
                    np.testing.assert_allclose(sigma[0]**2, reference_h, rtol=2e-14, atol=1e-14 * variance)
                    np.testing.assert_allclose(sigma[0] * eps[0], reference_returns, rtol=2e-14, atol=1e-14 * np.sqrt(variance))
                    cases.append({"persistence": rho, "variance": variance, "burn_in": burn,
                                  "max_abs_variance_difference": float(np.max(np.abs(sigma[0]**2 - reference_h))),
                                  "max_abs_return_difference": float(np.max(np.abs(sigma[0] * eps[0] - reference_returns)))})
    report = {"status": "passed", "source_commit": commit,
              "implementation_sha256": hashlib.sha256((Path(__file__).resolve().parents[1] / "src/dgp/volatility.py").read_bytes()).hexdigest(),
              "source_file_sha256": hashlib.sha256((source / "arch/univariate/volatility.py").read_bytes()).hexdigest(),
              "version_metadata_shim": shim, "reference_modified": False,
              "note": "Actual official GARCH.simulate API; source-only import using Python fallback. No package installed.",
              "numpy": np.__version__, "python": platform.python_version(), "cases": cases}
    content = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
