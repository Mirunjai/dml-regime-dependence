"""Coverage, null size, power and Monte Carlo error on independent replications.

No estimator, DGP or runner imports. Closed confidence intervals include their
endpoints. Failures are explicit and never silently removed or counted as null
rejections. See docs/DECISIONS.md and Morris, White & Crowther (2019).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from math import ceil, sqrt
from numbers import Real
from pathlib import Path
from statistics import NormalDist
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

FailurePolicy = Literal["raise", "report"]


def _finite_real(name: str, value: float) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real scalar")
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


@dataclass(frozen=True)
class BinomialSummary:
    successes: int
    replications: int
    rate: float
    mcse: float
    wilson95: tuple[float, float]


@dataclass(frozen=True)
class IntervalSummary:
    attempted: int
    valid: int
    failed: int
    truth: float
    coverage: BinomialSummary | None
    rejection: BinomialSummary | None
    size: BinomialSummary | None
    power: BinomialSummary | None
    mean_width: float | None
    width_mcse: float | None
    coverage_bounds_all_attempted: tuple[float, float]
    conditional_on_success: bool


@dataclass(frozen=True)
class PairedDifference:
    """A minus B, on explicitly aligned, jointly successful replication IDs."""

    attempted_union: int
    common_ids: int
    valid_pairs: int
    only_a: int
    only_b: int
    failed_a: int
    failed_b: int
    difference: float
    mcse: float
    conditional_on_joint_success: bool


def binomial_summary(successes: int, replications: int) -> BinomialSummary:
    """Plug-in MCSE plus a Wilson 95% interval, including boundary outcomes.

    The plug-in MCSE is zero at an observed rate of zero or one. The Wilson
    interval shows that finite samples at these boundaries do not imply certainty.
    """
    from numbers import Integral

    for name, value in (("successes", successes), ("replications", replications)):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
            raise TypeError(f"{name} must be an integer")
    if replications <= 0 or not 0 <= successes <= replications:
        raise ValueError("Require replications > 0 and 0 <= successes <= replications")
    successes, replications = int(successes), int(replications)
    p = successes / replications
    z = NormalDist().inv_cdf(0.975)
    denominator = 1 + z**2 / replications
    center = (p + z**2 / (2 * replications)) / denominator
    half = z * sqrt(p * (1 - p) / replications + z**2 / (4 * replications**2)) / denominator
    return BinomialSummary(
        successes, replications, p, sqrt(p * (1 - p) / replications),
        (max(0.0, center - half), min(1.0, center + half)),
    )


def _policy(value: FailurePolicy) -> None:
    if value not in ("raise", "report"):
        raise ValueError("failure_policy must be 'raise' or 'report'")


def summarize_intervals(
    lower: ArrayLike,
    upper: ArrayLike,
    truth: float,
    *,
    success: ArrayLike | None = None,
    failure_policy: FailurePolicy = "raise",
    expected_replications: int | None = None,
) -> IntervalSummary:
    """Summarize intervals without treating failed rows as valid observations.

    ``success`` is an explicit boolean vector. Missing/nonfinite or reversed bounds
    on a successful row always raise, even in report mode. Failed rows may have
    arbitrary numeric bounds (including NaN); they are never used in metrics.
    Strict mode raises on any failed row. Report mode returns success-conditioned
    metrics, attempted/valid/failed counts, and all-attempted coverage bounds.
    An all-failed run has undefined metrics (None), not zero coverage/size.

    Rows must be independent replications, not firms/windows from one panel.
    Attempted means rows supplied. Provide expected_replications to detect omitted
    rows; explicitly materialize missing planned runs as failed rows to report
    their effect. An array alone cannot reveal runs omitted by its producer.
    Null size uses CI inversion and is available only for truth=0; otherwise
    rejection of zero is labeled power. Intervals need not be symmetric or Wald.
    """
    _policy(failure_policy)
    truth = _finite_real("truth", truth)
    if np.iscomplexobj(lower) or np.iscomplexobj(upper):
        raise ValueError("Interval bounds must be real, not complex")
    lo, hi = np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)
    if lo.ndim != 1 or lo.size == 0 or lo.shape != hi.shape:
        raise ValueError("lower and upper must be matching nonempty 1-D arrays")
    if expected_replications is not None:
        from numbers import Integral
        if isinstance(expected_replications, (bool, np.bool_)) or not isinstance(expected_replications, Integral):
            raise TypeError("expected_replications must be an integer")
        if expected_replications != lo.size:
            raise ValueError("Row count differs from expected_replications; materialize missing runs as failures")
    ok = np.ones(lo.size, dtype=bool) if success is None else np.asarray(success)
    if ok.dtype.kind != "b" or ok.shape != lo.shape:
        raise ValueError("success must be a boolean vector matching the bounds")
    valid, failed = int(ok.sum()), int((~ok).sum())
    if failed and failure_policy == "raise":
        raise ValueError(f"{failed} failed replications; explicitly use failure_policy='report'")
    lvalid, uvalid = lo[ok], hi[ok]
    if not (np.isfinite(lvalid).all() and np.isfinite(uvalid).all()):
        raise ValueError("Successful intervals must have finite bounds")
    if np.any(lvalid > uvalid):
        raise ValueError("Successful intervals must satisfy lower <= upper")
    covered = int(np.sum((lvalid <= truth) & (truth <= uvalid)))
    rejected = int(np.sum((uvalid < 0) | (lvalid > 0)))
    coverage = binomial_summary(covered, valid) if valid else None
    rejection = binomial_summary(rejected, valid) if valid else None
    with np.errstate(over="raise", invalid="raise"):
        widths = uvalid - lvalid
        # Averaging after division prevents overflow of a representable mean.
        width = float(np.sum(widths / valid)) if valid else None
        if valid > 1:
            scale = float(np.max(widths))
            width_mcse = float(np.std(widths / scale, ddof=1) * (scale / sqrt(valid))) if scale else 0.0
        else:
            width_mcse = None
    return IntervalSummary(
        lo.size, valid, failed, truth, coverage, rejection,
        rejection if truth == 0 else None, rejection if truth != 0 else None,
        width, width_mcse, (covered / lo.size, (covered + failed) / lo.size), bool(failed),
    )


def empirical_size(
    lower: ArrayLike, upper: ArrayLike, truth: float, **kwargs: object,
) -> BinomialSummary | None:
    """Reject requests to label nonzero-effect rejection rates as empirical size."""
    if _finite_real("truth", truth) != 0:
        raise ValueError("Empirical size requires a zero true effect; use power otherwise")
    return summarize_intervals(lower, upper, truth, **kwargs).size


def paired_binary_difference(
    a: Mapping[str | int, bool | None],
    b: Mapping[str | int, bool | None],
    *,
    failure_policy: FailurePolicy = "raise",
) -> PairedDifference:
    """Difference of paired binary outcomes, e.g. coverage or null rejection.

    IDs align outcomes independently of insertion order. None means an explicitly
    failed replication; absent IDs are missing attempts. Strict mode requires the
    same IDs and no failures. Report mode uses the intersection of successes and
    exposes exclusions. Never replace paired uncertainty with two independent
    binomial MCSEs. At least two successful pairs are required to estimate its SE.
    Include every planned ID in both mappings (None when failed); IDs absent from
    both mappings cannot be inferred from the data supplied to this function.
    """
    _policy(failure_policy)
    for data in (a, b):
        if not isinstance(data, Mapping):
            raise TypeError("Outcomes must map unique replication IDs to bool or None")
        for key, value in data.items():
            if isinstance(key, (bool, np.bool_)) or not isinstance(key, (str, int, np.integer)):
                raise TypeError("Replication IDs must be strings or integers")
            if value is not None and not isinstance(value, (bool, np.bool_)):
                raise TypeError("Paired outcomes must be bool, or None for a failure")
    ids_a, ids_b = set(a), set(b)
    common = ids_a & ids_b
    failed_a = sum(value is None for value in a.values())
    failed_b = sum(value is None for value in b.values())
    excluded = ids_a != ids_b or failed_a > 0 or failed_b > 0
    if excluded and failure_policy == "raise":
        raise ValueError("Missing/failed pairs; explicitly use failure_policy='report'")
    # Sorting also makes serialized reports stable across insertion order.
    differences = np.array([
        int(a[key]) - int(b[key]) for key in sorted(common, key=lambda k: (str(type(k)), str(k)))
        if a[key] is not None and b[key] is not None
    ], dtype=float)
    if differences.size < 2:
        raise ValueError("At least two jointly successful paired replications are required")
    return PairedDifference(
        len(ids_a | ids_b), len(common), differences.size,
        len(ids_a - ids_b), len(ids_b - ids_a), failed_a, failed_b,
        float(differences.mean()), float(differences.std(ddof=1) / sqrt(differences.size)),
        excluded,
    )


def replication_budget(target_mcse: float, expected_rate: float | None = None) -> int:
    """Planning budget; None uses the conservative p(1-p)<=1/4 bound.

    Does not choose a grid, run replications, or grant Gate 3 approval. This is a
    precision target at the stated expected rate, not a guarantee at other rates.
    """
    target = _finite_real("target_mcse", target_mcse)
    if not 0 < target < 1:
        raise ValueError("target_mcse must be between zero and one")
    variance = 0.25
    if expected_rate is not None:
        p = _finite_real("expected_rate", expected_rate)
        if not 0 < p < 1:
            raise ValueError("expected_rate must be strictly between zero and one")
        variance = p * (1 - p)
    # Floating roundoff near an integer must not add a spurious replication.
    ratio = variance / target / target
    if not np.isfinite(ratio):
        raise ValueError("target_mcse is too small for a finite floating-point budget")
    nearest = round(ratio)
    return max(1, nearest if np.isclose(ratio, nearest, rtol=1e-14, atol=0) else ceil(ratio))


def summarize_csv(
    path: Path,
    truth: float,
    *,
    cell: str | None = None,
    failure_policy: FailurePolicy = "raise",
    expected_replications: int | None = None,
) -> IntervalSummary:
    """Recompute metrics from raw CSV bounds, without an experiment runner.

    Required columns: lower, upper. Optional: replication, cell, truth, and one
    of success (true/false) or status (ok/failed). Blank failed bounds are allowed.
    A multi-cell file needs explicit cell selection; duplicate replication IDs
    within the selected cell raise. A truth column, when supplied, must match
    the explicitly given evaluation truth. Other metadata columns are preserved
    by the caller and ignored here. This schema is an adapter, not a runner mandate.
    """
    import csv

    truth = _finite_real("truth", truth)
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)):
            raise ValueError("CSV column names must be unique")
        if not {"lower", "upper"} <= set(fields):
            raise ValueError("CSV needs lower and upper columns")
        if "success" in fields and "status" in fields:
            raise ValueError("CSV must use success or status, not both")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError("CSV rows must have the same number of fields as the header")
    if cell is not None:
        if "cell" not in fields:
            raise ValueError("Cell selection requires a cell column")
        rows = [row for row in rows if row["cell"] == cell]
    elif "cell" in fields and len({row["cell"] for row in rows}) > 1:
        raise ValueError("Multiple cells present; select one explicitly")
    if "replication" in fields:
        ids = [row["replication"] for row in rows]
        if any(not value for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("Replication IDs must be nonempty and unique within a cell")
    lower, upper, success = [], [], []
    for row in rows:
        ok = True
        if "success" in fields:
            flag = row["success"].strip().lower()
            if flag not in ("true", "false"):
                raise ValueError("CSV success values must be true/false")
            ok = flag == "true"
        if "status" in fields:
            flag = row["status"].strip().lower()
            if flag not in ("ok", "failed"):
                raise ValueError("CSV status values must be ok/failed")
            ok = flag == "ok"
        if "truth" in fields and float(row["truth"]) != truth:
            raise ValueError("CSV truth does not match the evaluation truth")
        lower.append(float(row["lower"]) if row["lower"].strip() else np.nan)
        upper.append(float(row["upper"]) if row["upper"].strip() else np.nan)
        success.append(ok)
    return summarize_intervals(lower, upper, truth, success=np.array(success, dtype=bool),
                               failure_policy=failure_policy, expected_replications=expected_replications)


def main() -> None:
    """Known-outcome example or independent recomputation from saved CSV bounds."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Raw interval CSV; omit to run the known-outcome mock")
    parser.add_argument("--truth", type=float)
    parser.add_argument("--cell")
    parser.add_argument("--failure-policy", choices=("raise", "report"), default="raise")
    parser.add_argument("--expected-replications", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.input is not None:
        if args.truth is None:
            parser.error("--truth is required with --input")
        result = {"source": str(args.input), "cell": args.cell,
                  "summary": asdict(summarize_csv(args.input, args.truth, cell=args.cell,
                                                failure_policy=args.failure_policy,
                                                expected_replications=args.expected_replications))}
    else:
        if args.truth is not None or args.cell is not None or args.expected_replications is not None:
            parser.error("--truth, --cell and --expected-replications require --input")
        lower = np.r_[np.full(95, -1.0), np.full(5, 0.1)]
        result = {
            "label": "mock intervals; not DML calibration evidence",
            "summary": asdict(summarize_intervals(lower, np.ones(100), 0.0)),
            "planned_R_at_95pct_for_mcse_0_005": replication_budget(0.005, 0.95),
            "conservative_R_for_mcse_0_005": replication_budget(0.005),
        }
    content = json.dumps(result, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
