"""
Project A - DGP v0 (integrated toy DGP).   Author: Mirun (Week 2)

Unit of analysis (OPEN for team review): one firm-event = one firm, one event date t_i,
one outcome window of H periods starting at t_i. Treated = S&P-inclusion-type event,
untreated = control firm observed over its own pseudo-event window.

Y_i = g(X_i) + sum_{s=t_i}^{t_i+H-1} [ beta_i*F[s] + lam*U[s] + sigma[i,s]*z[i,s] ] + tau*D_i

Three separate mechanisms, three separate dials, nine separate random streams:
  1. persistence  : GARCH(1,1) alpha+beta, firm-level, driven ONLY by the firm's own z      (stream 'vol')
  2. density      : fraction of calendar time inside a regime window (events overlapping
                    a regime window get the shared shock U_k)                              (streams 'layout','shock')
  3. n_regimes    : number of distinct shock realizations the covered time is split into    (same streams)
Treatment timing (dates) and treatment assignment use their own streams and never read U or sigma.
"""
import numpy as np
from dataclasses import dataclass, replace

STREAMS = ["cov", "dates", "vol", "factor", "layout", "shock", "regime_treat", "treat", "noise"]


def spawn_rngs(seed):
    kids = np.random.SeedSequence(seed).spawn(len(STREAMS))
    return {n: np.random.default_rng(k) for n, k in zip(STREAMS, kids)}


@dataclass(frozen=True)
class Config:
    n: int = 400              # firm-events
    T: int = 260              # calendar periods
    H: int = 5                # outcome window length
    p: int = 5                # covariates
    persistence: float = 0.90 # GARCH alpha+beta
    garch_alpha: float = 0.10
    sigma2_bar: float = 1.0   # unconditional variance (held fixed across persistence)
    density: float = 0.50     # share of calendar time inside regime windows
    n_regimes: int = 4        # number of distinct regime shocks
    sd_shock: float = 0.40    # sd of per-period regime shock U_k
    sd_factor: float = 0.50
    gamma: float = 1.0        # regime-level random effect on treatment propensity (assignment clustering)
    tau: float = 1.0          # KNOWN true effect
    seed: int = 0
    # positive-control switches (used ONLY by validation code, never in production runs)
    break_vol_independence: bool = False
    break_treat_independence: bool = False


def simulate_volatility(n_firms, n_periods, persistence, rng, alpha=0.10, sigma2_bar=1.0, burn=200):
    """GARCH(1,1) per firm. sigma2_t = omega + alpha*r_{t-1}^2 + beta*sigma2_{t-1}, r=sigma*z.
    omega=(1-persistence)*sigma2_bar keeps the UNCONDITIONAL variance fixed for every persistence.
    Driven only by own innovations z. Returns sigma[n,T], z[n,T]."""
    assert 0 < alpha < persistence < 1
    beta = persistence - alpha
    omega = (1 - persistence) * sigma2_bar
    z_all = rng.standard_normal((n_firms, n_periods + burn))
    s2 = np.full(n_firms, sigma2_bar)
    sig = np.empty_like(z_all)
    for t in range(n_periods + burn):
        sig[:, t] = np.sqrt(s2)
        r = sig[:, t] * z_all[:, t]
        s2 = omega + alpha * r**2 + beta * s2
    return sig[:, burn:], z_all[:, burn:]


def simulate_regimes(n_periods, density, n_regimes, sd_shock, rng_layout, rng_shock):
    """Regime layout: n_regimes non-overlapping windows jointly covering round(density*T) periods.
    Returns regime_id[t] (-1 = no regime), U[t] (shock of the regime active at t, else 0), U_k[K]."""
    rid = np.full(n_periods, -1)
    U = np.zeros(n_periods)
    if n_regimes == 0 or density <= 0:
        return rid, U, np.zeros(0)
    L = int(round(density * n_periods))
    K = min(n_regimes, max(L, 1))
    lens = np.full(K, L // K); lens[: L % K] += 1
    gaps = rng_layout.multinomial(n_periods - L, np.ones(K + 1) / (K + 1))
    Uk = rng_shock.normal(0.0, sd_shock, K)
    pos = gaps[0]
    for k in range(K):
        rid[pos: pos + lens[k]] = k
        U[pos: pos + lens[k]] = Uk[k]
        pos += lens[k] + gaps[k + 1]
    return rid, U, Uk


def expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def build_world(cfg: Config, vol_fn, regime_fn):
    """THE SKELETON: the structural equation with two plug-in points (vol_fn, regime_fn).
    Week 1 placeholders and the Week 2 real modules both go through this one function."""
    R = spawn_rngs(cfg.seed)
    n, T, H = cfg.n, cfg.T, cfg.H
    X = R["cov"].standard_normal((n, cfg.p))
    t0 = R["dates"].integers(0, T - H + 1, size=n)                 # event dates: own stream, never sees U
    sig, z = vol_fn(n, T, cfg.persistence, R["vol"], cfg.garch_alpha, cfg.sigma2_bar)
    F = R["factor"].normal(0, cfg.sd_factor, T)
    rid_t, U_t, Uk = regime_fn(T, cfg.density, cfg.n_regimes, cfg.sd_shock, R["layout"], R["shock"])
    vk = R["regime_treat"].standard_normal(max(cfg.n_regimes, 1))  # regime-level treatment effect, independent of U

    if cfg.break_vol_independence:   # POSITIVE CONTROL: volatility state reacts to the regime shock
        sig = sig * (1 + 2.0 * np.abs(U_t)[None, :] / max(cfg.sd_shock, 1e-9))

    idx = t0[:, None] + np.arange(H)[None, :]                          # n x H period indices
    beta_i = 1.0 + 0.3 * X[:, 3]
    r_idio = sig[np.arange(n)[:, None], idx] * z[np.arange(n)[:, None], idx]
    U_win = U_t[idx].sum(1)
    F_win = F[idx].sum(1)
    # regime membership of each event = first regime overlapping its window (-1 if none)
    rw = rid_t[idx]
    first = np.where((rw >= 0).any(1), rw[np.arange(n), (rw >= 0).argmax(1)], -1)
    exposed = first >= 0

    logit = -0.5 + 0.5 * X[:, 0] + 0.3 * X[:, 1] + cfg.gamma * np.where(exposed, vk[np.maximum(first, 0)], 0.0)
    if cfg.break_treat_independence:  # POSITIVE CONTROL: treatment reacts to realized shock
        logit = logit + 3.0 * U_win / max(cfg.sd_shock * H, 1e-9)
    D = (R["treat"].random(n) < expit(logit)).astype(float)

    g = 0.5 * X[:, 0] + 0.3 * X[:, 1] ** 2 + 0.2 * X[:, 0] * X[:, 2]
    Y = g + beta_i * F_win + U_win + r_idio.sum(1) + cfg.tau * D
    cluster = np.where(exposed, first, -1 - np.arange(n))               # unexposed events = singleton clusters
    return dict(Y=Y, D=D, X=X, cluster=cluster, regime=first, exposed=exposed, t0=t0, U_win=U_win,
                sig_event=sig[np.arange(n), t0], sig=sig, z=z, rid_t=rid_t, U_t=U_t, Uk=Uk, vk=vk, cfg=cfg)


def simulate_dgp(cfg: Config):
    """DGP v0 = skeleton with the real Week 1 modules plugged in."""
    return build_world(cfg, simulate_volatility, simulate_regimes)


def placeholder_volatility(n_firms, n_periods, persistence, rng, alpha=0.10, sigma2_bar=1.0):
    """Week 1 stand-in: constant volatility, iid innovations (no persistence)."""
    return np.full((n_firms, n_periods), np.sqrt(sigma2_bar)), rng.standard_normal((n_firms, n_periods))


def placeholder_regimes(n_periods, density, n_regimes, sd_shock, rng_layout, rng_shock):
    """Week 1 stand-in: no regimes, no common shock (U = 0). Skeleton then has no cross-sectional dependence."""
    return np.full(n_periods, -1), np.zeros(n_periods), np.zeros(0)


def overlap_for(density, K, T=260, H=5, reps=300, seed=0):
    """Mean share of event windows overlapping a regime window, for a given calendar density and K."""
    rs = np.random.default_rng(seed); tot = 0.0
    for _ in range(reps):
        rid, _, _ = simulate_regimes(T, density, K, 1.0, rs, rs)
        hit = np.array([(rid[s:s + H] >= 0).any() for s in range(T - H + 1)])
        tot += hit.mean()
    return tot / reps


def density_for_overlap(target, K, T=260, H=5):
    """Bisection: calendar density that yields a target REALIZED event-overlap density for K regimes.
    Needed because boundary effects inflate overlap as K grows (finding from Gate 2 check C)."""
    lo, hi = 0.0, 1.0
    for _ in range(18):
        mid = (lo + hi) / 2
        if overlap_for(mid, K, T, H, reps=60) < target: lo = mid
        else: hi = mid
    return (lo + hi) / 2
