"""Firm-level Gaussian GARCH(1,1), independent of all regime inputs.

Arrays use (firm, time). ``sigma`` is conditional standard deviation in return
units, ``eps`` is dimensionless iid N(0,1), and idiosyncratic returns are their
product. See Bollerslev (1986), Sections 2-4, and docs/DECISIONS.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def _count(name: str, value: int, minimum: int = 1) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return int(value)


def _finite_real(name: str, value: float) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real scalar")
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


@dataclass(frozen=True)
class GARCHParameters:
    """Resolved coefficients and their moment conditions (Gaussian innovations)."""

    omega: float
    alpha: float
    beta: float
    unconditional_variance: float

    @property
    def persistence(self) -> float:
        return self.alpha + self.beta

    @property
    def stationarity_gap(self) -> float:
        """Accurate 1-alpha-beta for the actual float64 coefficients."""
        return fsum((1.0, -self.alpha, -self.beta))

    @property
    def fourth_moment_margin(self) -> float:
        """1-E[(alpha*eps²+beta)²], evaluated without subtracting near-unit squares."""
        gap = self.stationarity_gap
        return gap * (2 - gap) - 2 * self.alpha**2

    @property
    def fourth_moment_factor(self) -> float:
        return fsum((1.0, -self.fourth_moment_margin))

    @property
    def has_finite_fourth_moment(self) -> bool:
        # A displayed factor can round to exactly 1 while its margin is positive.
        return self.stationarity_gap > 0 and self.fourth_moment_margin > 0

    def squared_return_acf(self, max_lag: int) -> FloatArray:
        """Population ACF at lags 0..max_lag; undefined without a fourth moment."""
        max_lag = _count("max_lag", max_lag, 0)
        if not self.has_finite_fourth_moment:
            raise ValueError("Squared-return ACF requires a finite fourth moment")
        acf = np.ones(max_lag + 1)
        if max_lag:
            rho = self.persistence
            gap = self.stationarity_gap
            one_minus_rho_squared = gap * (2 - gap)
            first = self.alpha * (one_minus_rho_squared + self.alpha * (1 - gap)) / (
                one_minus_rho_squared + self.alpha**2
            )
            acf[1:] = first * rho ** np.arange(max_lag)
        return acf


def garch_parameters(
    persistence: float,
    *,
    unconditional_variance: float = 1.0,
    arch_share: float = 0.1,
) -> GARCHParameters:
    """Map rho to alpha=a*rho, beta=rho-alpha, omega=v*(1-rho).

    This holds the *intended* unconditional variance fixed. It changes shock
    responsiveness and higher moments along with persistence. Finite variance
    requires rho<1; a Gaussian fourth moment additionally requires rho²+2alpha²<1.
    Finite-variance processes without a fourth moment may still be simulated.
    """
    rho = _finite_real("persistence", persistence)
    variance = _finite_real("unconditional_variance", unconditional_variance)
    share = _finite_real("arch_share", arch_share)
    if not 0 <= rho < 1:
        raise ValueError("persistence must satisfy 0 <= persistence < 1")
    if variance <= 0:
        raise ValueError("unconditional_variance must be positive")
    if not 0 < share <= 1:
        raise ValueError("arch_share must satisfy 0 < arch_share <= 1")
    alpha = share * rho
    beta = rho - alpha
    # Algebraically v*(1-rho), using the resolved coefficients. Ordinary
    # subtraction loses meaningful relative precision near the unit boundary.
    gap = fsum((1.0, -alpha, -beta))
    if gap <= 0:
        raise ValueError("Resolved coefficients must have alpha+beta < 1")
    omega = variance * gap
    if omega == 0:
        raise ValueError("omega underflows to zero; use a representable variance scale")
    return GARCHParameters(omega, alpha, beta, variance)


def simulate_volatility(
    n_firms: int,
    n_periods: int,
    persistence: float,
    rng: np.random.Generator,
    *,
    unconditional_variance: float = 1.0,
    arch_share: float = 0.1,
    burn_in: int = 1000,
) -> tuple[FloatArray, FloatArray]:
    """Return conditional standard deviations and standardized innovations.

    h[i,t] = omega + alpha*e[i,t-1]**2 + beta*h[i,t-1], e=sqrt(h)*eps.
    Initialize h[:,0]=v; this matches its mean, not its stationary distribution.
    Discard exactly ``burn_in`` time steps. Independent Gaussian draws are made
    once per time step for all firms; extending n_periods preserves the prefix
    for a fixed n_firms, seed and burn-in. The caller owns RNG state and seeding.

    No regime/factor/treatment argument is accepted. Numerical overflow or a
    nonpositive state raises FloatingPointError with a time index; never clip,
    renormalize, or return a partially invalid panel. Memory is O(firms*periods),
    independent of burn-in length.
    """
    firms = _count("n_firms", n_firms)
    periods = _count("n_periods", n_periods)
    burn = _count("burn_in", burn_in, 0)
    params = garch_parameters(
        persistence, unconditional_variance=unconditional_variance, arch_share=arch_share
    )
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    sigma = np.empty((firms, periods))
    eps = np.empty_like(sigma)
    variance = np.full(firms, params.unconditional_variance)
    previous_return = np.zeros(firms)
    for time in range(burn + periods):
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                if time and params.alpha:
                    variance = (
                        params.omega
                        + params.alpha * np.square(previous_return)
                        + params.beta * variance
                    )
                if not np.all(np.isfinite(variance) & (variance > 0)):
                    raise FloatingPointError("nonfinite or nonpositive conditional variance")
                conditional_sd = np.sqrt(variance)
                innovations = rng.standard_normal(firms)
                previous_return = conditional_sd * innovations
        except FloatingPointError as error:
            raise FloatingPointError(f"GARCH numerical failure at time {time}: {error}") from error
        if time >= burn:
            sigma[:, time - burn] = conditional_sd
            eps[:, time - burn] = innovations
    return sigma, eps


def main() -> None:
    """Small CPU example; the full validation command also writes plots/reports."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persistence", type=float, default=0.9)
    parser.add_argument("--n-firms", type=int, default=50)
    parser.add_argument("--n-periods", type=int, default=500)
    parser.add_argument("--burn-in", type=int, default=1000)
    parser.add_argument("--variance", type=float, default=1.0)
    parser.add_argument("--arch-share", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    from dataclasses import asdict

    params = garch_parameters(
        args.persistence, unconditional_variance=args.variance, arch_share=args.arch_share
    )
    sigma, eps = simulate_volatility(
        args.n_firms, args.n_periods, args.persistence, np.random.default_rng(args.seed),
        unconditional_variance=args.variance, arch_share=args.arch_share,
        burn_in=args.burn_in,
    )
    print(json.dumps({
        "parameters": asdict(params), "shape": list(sigma.shape),
        "has_finite_fourth_moment": params.has_finite_fourth_moment,
        "mean_conditional_variance": float(np.mean(sigma**2)),
        "mean_squared_idiosyncratic_return": float(np.mean((sigma * eps)**2)),
        "seed": args.seed, "burn_in": args.burn_in,
        "note": "Toy smoke example, not Gate 2 validation.",
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
