"""Integrated calendar-regime DGP with explicit multi-regime event membership.

This is a comparison implementation. gamma=0 removes regime-level treatment
assignment heterogeneity; gamma>0 includes it. Do not select gamma after looking
at coverage: pre-specify the comparison with the team.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import fsum
from numbers import Real
import numpy as np

STREAMS = ("cov", "dates", "vol", "factor", "layout", "shock",
           "regime_treat", "treat", "noise")

def spawn_rngs(seed: int):
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    children = np.random.SeedSequence(int(seed)).spawn(len(STREAMS))
    return {name: np.random.default_rng(child) for name, child in zip(STREAMS, children)}

@dataclass(frozen=True)
class Config:
    n: int = 400
    T: int = 260
    H: int = 5
    p: int = 5
    persistence: float = .90
    garch_alpha: float = .10
    sigma2_bar: float = 1.0
    density: float = .50
    n_regimes: int = 4
    sd_shock: float = .40
    sd_factor: float = .50
    gamma: float = 1.0
    tau: float = 1.0
    seed: int = 0
    break_vol_independence: bool = False
    break_treat_independence: bool = False

    def validate(self):
        ints = {"n": self.n, "T": self.T, "H": self.H, "p": self.p, "n_regimes": self.n_regimes}
        for key, val in ints.items():
            if isinstance(val, bool) or not isinstance(val, (int, np.integer)):
                raise TypeError(f"{key} must be an integer")
        if self.n < 2 or self.T < 2 or not 1 <= self.H <= self.T or self.p < 4 or self.n_regimes < 0:
            raise ValueError("Require n>=2, T>=2, 1<=H<=T, p>=4, n_regimes>=0")
        for key in ("persistence", "garch_alpha", "sigma2_bar", "density", "sd_shock", "sd_factor", "gamma", "tau"):
            val = getattr(self, key)
            if isinstance(val, (bool, np.bool_)) or not isinstance(val, Real) or not np.isfinite(val):
                raise ValueError(f"{key} must be finite")
        if not 0 < self.garch_alpha < self.persistence < 1:
            raise ValueError("Require 0 < garch_alpha < persistence < 1")
        if self.sigma2_bar <= 0 or not 0 <= self.density <= 1 or self.sd_shock < 0 or self.sd_factor < 0:
            raise ValueError("Invalid variance, density, or shock scale")
        if self.gamma < 0:
            raise ValueError("gamma must be nonnegative")
        for name in ("break_vol_independence", "break_treat_independence"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be an explicit boolean")
        if isinstance(self.seed, bool) or not isinstance(self.seed, (int, np.integer)) or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")

def simulate_volatility(n_firms, n_periods, persistence, rng, alpha=.10, sigma2_bar=1., burn=500):
    """Historical fixed-alpha GARCH family, not the canonical arch-share family.

    Row-major innovations and explicit burn are retained for replay of Mirun's
    saved pilot. The canonical src/dgp/volatility.py is unchanged and uses a
    different default alpha mapping, burn-in and innovation draw order.
    """
    for name, value, minimum in (("n_firms", n_firms, 1), ("n_periods", n_periods, 1), ("burn", burn, 0)):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if (any(isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not np.isfinite(value)
            for value in (persistence, alpha, sigma2_bar))
            or not 0 < alpha < persistence < 1 or sigma2_bar <= 0):
        raise ValueError("Invalid GARCH parameters")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy Generator")
    beta = persistence - alpha
    omega = fsum((1., -alpha, -beta)) * sigma2_bar
    if omega <= 0:
        raise ValueError("GARCH intercept underflowed or is nonpositive")
    zall = rng.standard_normal((n_firms, n_periods + burn))
    h = np.full(n_firms, sigma2_bar)
    sig = np.empty_like(zall)
    for t in range(n_periods + burn):
        with np.errstate(over="raise", invalid="raise"):
            sig[:, t] = np.sqrt(h)
            r = sig[:, t] * zall[:, t]
            h = omega + alpha * r * r + beta * h
        if not np.isfinite(h).all() or (h <= 0).any():
            raise FloatingPointError(f"GARCH failed at t={t}")
    return sig[:, burn:], zall[:, burn:]

def simulate_calendar_regimes(T, density, K, sd_shock, rng_layout, rng_shock):
    """Contiguous calendar-time blocks. Returns ids[T], U[T], shocks[K_actual]."""
    if isinstance(T, bool) or not isinstance(T, (int, np.integer)) or T < 1:
        raise ValueError("T must be a positive integer")
    if isinstance(K, bool) or not isinstance(K, (int, np.integer)) or K < 0:
        raise ValueError("K must be a nonnegative integer")
    if not np.isfinite(density) or not 0 <= density <= 1 or not np.isfinite(sd_shock) or sd_shock < 0:
        raise ValueError("density must be in [0,1] and sd_shock nonnegative")
    ids = np.full(T, -1, dtype=int); U = np.zeros(T)
    L = int(round(density*T))
    if K == 0 or L == 0:
        return ids, U, np.zeros(0)
    Kactual = min(K, L)
    lengths = np.full(Kactual, L//Kactual, dtype=int)
    lengths[:L % Kactual] += 1
    gaps = rng_layout.multinomial(T-L, np.ones(Kactual+1)/(Kactual+1))
    shocks = rng_shock.normal(0., sd_shock, Kactual)
    pos = int(gaps[0])
    for k, length in enumerate(lengths):
        ids[pos:pos+length] = k
        U[pos:pos+length] = shocks[k]
        pos += int(length + gaps[k+1])
    if (ids >= 0).sum() != L:
        raise RuntimeError("Regime layout did not allocate the requested active periods")
    return ids, U, shocks

def build_world(cfg: Config):
    cfg.validate()
    R = spawn_rngs(cfg.seed); n,T,H = cfg.n,cfg.T,cfg.H
    X = R["cov"].standard_normal((n,cfg.p))
    t0 = R["dates"].integers(0,T-H+1,size=n)
    sig,z = simulate_volatility(n,T,cfg.persistence,R["vol"],cfg.garch_alpha,cfg.sigma2_bar)
    F = R["factor"].normal(0,cfg.sd_factor,T)
    rid_t,U_t,Uk = simulate_calendar_regimes(T,cfg.density,cfg.n_regimes,cfg.sd_shock,R["layout"],R["shock"])
    vk = R["regime_treat"].standard_normal(max(len(Uk),1))
    if cfg.break_vol_independence:
        sig = sig*(1+2*np.abs(U_t)[None,:]/max(cfg.sd_shock,1e-9))
    idx = t0[:,None]+np.arange(H)[None,:]
    rw = rid_t[idx]
    # Membership set per event: all unique nonnegative regimes touched by its H-window.
    memberships = [tuple(int(k) for k in np.unique(row) if k >= 0) for row in rw]
    exposed = np.array([bool(m) for m in memberships])
    U_win = U_t[idx].sum(axis=1); F_win = F[idx].sum(axis=1)
    beta_i = 1+.3*X[:,3]
    r_idio = sig[np.arange(n)[:,None],idx]*z[np.arange(n)[:,None],idx]
    first = np.array([m[0] if m else -1 for m in memberships],dtype=int)
    # Regime treatment random effect: compare gamma=0 against the pre-specified gamma>0 design.
    regime_effect = np.array([np.mean(vk[list(m)]) if m else 0. for m in memberships])
    logit = -.5+.5*X[:,0]+.3*X[:,1]+cfg.gamma*regime_effect
    if cfg.break_treat_independence:
        logit = logit+3*U_win/max(cfg.sd_shock*H,1e-9)
    # numerically stable logistic
    prob = np.empty_like(logit)
    pos = logit >= 0
    prob[pos] = 1/(1+np.exp(-logit[pos]))
    e = np.exp(logit[~pos]); prob[~pos] = e/(1+e)
    D = (R["treat"].random(n)<prob).astype(float)
    g = .5*X[:,0]+.3*X[:,1]**2+.2*X[:,0]*X[:,2]
    Y = g+beta_i*F_win+U_win+r_idio.sum(axis=1)+cfg.tau*D
    return {"Y":Y,"D":D,"X":X,"t0":t0,"idx":idx,"cluster_memberships":memberships,
            "cluster":first,"regime":first,"exposed":exposed,"U_win":U_win,"F_win":F_win,
            "sig_event":sig[np.arange(n),t0],"sig":sig,"z":z,"rid_t":rid_t,"U_t":U_t,
            "Uk":Uk,"vk":vk,"cfg":cfg}
