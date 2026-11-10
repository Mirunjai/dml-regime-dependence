"""Gate 2 validation checks A-E (standalone, no DML). Writes results/gate2_checks.json + fig_gate2.png"""
import json, sys, numpy as np, warnings
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from dgp import *
warnings.filterwarnings("ignore")

def acf(x, lag):  # pooled over firms: x [n,T]
    x = x - x.mean(1, keepdims=True)
    num = (x[:, lag:] * x[:, :-lag]).sum(1); den = (x**2).sum(1)
    return float(np.mean(num / den))

def ols_resid(v, X):
    P = np.column_stack([np.ones(len(v)), X, X**2] + [X[:, i] * X[:, j] for i in range(X.shape[1]) for j in range(i + 1, X.shape[1])])
    return v - P @ np.linalg.lstsq(P, v, rcond=None)[0]

def manip(d):
    """Dependence diagnostics computed ONLY from observable data (no access to U): the manipulation check."""
    cl, Y, D, X = d["cluster"], d["Y"], d["D"], d["X"]
    Yt, Dt = ols_resid(Y, X), ols_resid(D, X)
    n = len(Y); J = (Dt**2).sum(); tau = (Dt * Yt).sum() / J; psi = Dt * (Yt - tau * Dt)
    u, inv = np.unique(cl, return_inverse=True); G = len(u)
    se_n = np.sqrt((psi**2).sum()) / J; se_r = np.sqrt(G / (G - 1) * (np.bincount(inv, weights=psi)**2).sum()) / J
    m = np.bincount(inv); ex = m[inv] >= 2
    # ANOVA ICC(1) of outcome residual over clusters with >=2 events
    icc = np.nan
    if ex.any():
        sel = np.isin(inv, np.where(m >= 2)[0]); y = Yt[sel]; g = inv[sel]; ug, gi = np.unique(g, return_inverse=True)
        mk = np.bincount(gi); k = len(ug); N = len(y)
        gm = np.bincount(gi, weights=y) / mk
        ssb = (mk * (gm - y.mean())**2).sum(); ssw = ((y - gm[gi])**2).sum()
        msb = ssb / max(k - 1, 1); msw = ssw / max(N - k, 1); m0 = (N - (mk**2).sum() / N) / max(k - 1, 1)
        icc = (msb - msw) / (msb + (m0 - 1) * msw)
    mm = np.bincount(inv)[np.bincount(inv) >= 2]
    pair = (mm * (mm - 1)).sum() / (n * (n - 1))
    return dict(overlap_density=float(d["exposed"].mean()), pair_density=float(pair), icc=float(icc),
                se_ratio=float(se_r / se_n), regimes_hit=int(len(np.unique(d["regime"][d["exposed"]]))))

out = {}
# ---------------- A. persistence sweep ----------------
from arch import arch_model
A = []
for p in [0.5, 0.8, 0.9, 0.95, 0.98]:
    rng = np.random.default_rng(11)
    sig, z = simulate_volatility(300, 1000, p, rng); r = sig * z
    fits = []
    for i in range(12):
        res = arch_model(r[i] * 1.0, mean="Zero", vol="GARCH", p=1, q=1, rescale=False).fit(disp="off")
        fits.append(res.params["alpha[1]"] + res.params["beta[1]"])
    A.append(dict(persistence=p, mean_r2=float((r**2).mean()), acf1=acf(r**2, 1), acf5=acf(r**2, 5), acf10=acf(r**2, 10), acf20=acf(r**2, 20),
                  fitted_persistence=float(np.mean(fits)), n_nan=int(np.isnan(r).sum()), max_abs_r=float(np.abs(r).max()),
                  kurtosis=float(stats.kurtosis(r.ravel())), share_abs_gt_8=float((np.abs(r) > 8).mean())))
out["A_persistence"] = A

# ---------------- B. density sweep (K=4) ----------------
B = []
for dens in [0.0, 0.10, 0.25, 0.50, 0.75]:
    ms = [manip(simulate_dgp(Config(density=dens, n_regimes=4 if dens > 0 else 0, seed=s))) for s in range(100)]
    B.append(dict(density=dens, **{k: float(np.nanmean([m[k] for m in ms])) for k in ms[0]}))
out["B_density"] = B

# ---------------- C. regime count at matched density 0.5 ----------------
C = []
for K in [1, 2, 4, 8, 16, 32]:
    ms, mean_u = [], []
    for s in range(300):
        d = simulate_dgp(Config(density=0.5, n_regimes=K, seed=s)); ms.append(manip(d)); mean_u.append(d["U_win"].mean())
    C.append(dict(n_regimes=K, **{k: float(np.nanmean([m[k] for m in ms])) for k in ms[0]},
                  sd_of_mean_shock=float(np.std(mean_u))))
out["C_regime_count"] = C

# ---------------- D. separation (bitwise + statistical) ----------------
d1, d2 = simulate_dgp(Config(persistence=0.5, seed=5)), simulate_dgp(Config(persistence=0.95, seed=5))
same_reg = all(np.array_equal(d1[k], d2[k]) for k in ["rid_t", "U_t", "Uk", "t0", "X", "vk", "regime", "D"])
e1, e2 = simulate_dgp(Config(density=0.0, n_regimes=0, seed=5)), simulate_dgp(Config(density=0.75, seed=5))
same_vol = all(np.array_equal(e1[k], e2[k]) for k in ["sig", "z", "t0", "X"])
icc_by_p = {p: float(np.nanmean([manip(simulate_dgp(Config(persistence=p, density=0.5, seed=s)))["icc"] for s in range(150)])) for p in [0.5, 0.95]}
acf_by_dens = {dn: acf((simulate_dgp(Config(density=dn, n_regimes=4 if dn else 0, seed=5))["sig"] * simulate_dgp(Config(density=dn, n_regimes=4 if dn else 0, seed=5))["z"])**2, 5) for dn in [0.0, 0.75]}
out["D_separation"] = dict(regime_and_treatment_arrays_bitwise_identical_when_persistence_changes=bool(same_reg),
    volatility_arrays_bitwise_identical_when_density_changes=bool(same_vol), mean_icc_by_persistence=icc_by_p,
    acf5_idiosyncratic_r2_by_density=acf_by_dens)

# ---------------- E. independence + positive controls ----------------
def corr_tests(**kw):
    c_vol, c_D, c_t = [], [], []
    for s in range(300):
        d = simulate_dgp(Config(seed=1000 + s, density=0.5, n_regimes=8, **kw)); ex = d["exposed"]
        c_vol.append(stats.spearmanr(d["sig_event"][ex], np.abs(d["U_win"][ex]))[0])
        c_D.append(np.corrcoef(d["D"], d["U_win"])[0, 1]); c_t.append(np.corrcoef(d["t0"], d["U_win"])[0, 1])
    f = lambda c: dict(mean_corr=float(np.mean(c)), t_stat=float(stats.ttest_1samp(c, 0).statistic))
    return dict(vol_vs_abs_shock=f(c_vol), treatment_vs_shock=f(c_D), event_date_vs_shock=f(c_t))
out["E_independence"] = dict(production=corr_tests(), positive_control_break_vol=corr_tests(break_vol_independence=True),
                              positive_control_break_treatment=corr_tests(break_treat_independence=True))
json.dump(out, open("results/gate2_checks.json", "w"), indent=1)

# ---------------- figure ----------------
fig, ax = plt.subplots(2, 2, figsize=(11, 8))
rng = np.random.default_rng(11)
for p, c in zip([0.5, 0.9, 0.98], ["C0", "C1", "C3"]):
    sig, z = simulate_volatility(300, 1000, p, rng); r2 = (sig * z)**2
    ax[0, 0].plot(range(1, 31), [acf(r2, l) for l in range(1, 31)], c, label=f"persistence {p}")
ax[0, 0].set(title="A. ACF of squared returns decays slower with persistence", xlabel="lag", ylabel="ACF"); ax[0, 0].legend()
ax[0, 1].plot([b["density"] for b in B], [b["overlap_density"] for b in B], "o-", label="events overlapping a regime")
ax[0, 1].plot([b["density"] for b in B], [b["pair_density"] for b in B], "s-", label="share of event pairs in same regime")
ax[0, 1].plot([0, 1], [0, 1], "k:", lw=.7); ax[0, 1].set(title="B. Realized dependence vs density dial (K=4)", xlabel="density setting"); ax[0, 1].legend()
ax[1, 0].plot([c["n_regimes"] for c in C], [c["sd_of_mean_shock"] for c in C], "o-")
ax[1, 0].set_xscale("log", base=2); ax[1, 0].set(title="C. Density fixed at 0.5: sd of mean shock falls with #regimes", xlabel="number of regimes K", ylabel="sd of sample-mean shock")
ax2 = ax[1, 1]; ax2.plot([c["n_regimes"] for c in C], [c["overlap_density"] for c in C], "o-", label="overlap density"); ax2.plot([c["n_regimes"] for c in C], [c["pair_density"] for c in C], "s-", label="pair density")
ax2.set_xscale("log", base=2); ax2.set(title="C. Overlap density ~ matched; pair density moves with K", xlabel="number of regimes K"); ax2.legend()
plt.tight_layout(); plt.savefig("results/fig_gate2.png", dpi=130)
print(json.dumps(out, indent=1)[:6000])
