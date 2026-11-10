"""Independent recomputation of pilot coverage, paired contrasts and spread from raw reconstructed intervals.
EXPLORATORY. Inputs: audit/legacy_intervals.csv (legacy DGP, CR1 first-regime) and calendar raw_intervals.csv
(week2_completion DGP, overlap sandwich). The two variants are summarised separately and never pooled."""
import json, sys
import numpy as np, pandas as pd

CELLS = ["random_xfit__naive_var","random_xfit__robust_var","grouped_xfit__naive_var","grouped_xfit__robust_var"]

def wilson(k, n, z=1.959964):
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [float(c-h), float(c+h)]

def summarize(df):
    out = {}
    for scen, g in df.groupby("scenario", sort=False):
        piv = {c: g[g.cell == c].sort_values("replication").reset_index(drop=True) for c in CELLS}
        n = len(piv[CELLS[0]]); truth = float(g.truth.iloc[0]); row = {"reps": n, "truth": truth, "cells": {}}
        cov = {}
        for c, d in piv.items():
            ok = d.status == "ok"
            hit = ((d.lower <= truth) & (truth <= d.upper) & ok).astype(int).to_numpy()
            cov[c] = (hit, ok.to_numpy())
            k, m = int(hit.sum()), int(ok.sum())
            row["cells"][c] = {"valid": m, "failed": int(n-m), "coverage": k/m if m else None,
                "mcse": float(np.sqrt(k/m*(1-k/m)/m)) if m else None, "wilson95": wilson(k, m) if m else None,
                "mean_width": float((d.upper-d.lower)[ok].mean()) if m else None,
                "sd_estimate": float(d.estimate[ok].std(ddof=1)) if m > 1 else None,
                "bias": float((d.estimate[ok]-truth).mean()) if m else None}
        a, b = "random_xfit__robust_var", "grouped_xfit__robust_var"
        both = cov[a][1] & cov[b][1]
        if both.sum() > 1:
            diff = cov[b][0][both]-cov[a][0][both]; m = int(both.sum())
            row["paired_grouped_minus_random_robust"] = {"n": m, "diff": float(diff.mean()),
                "mcse": float(diff.std(ddof=1)/np.sqrt(m)), "discordant": int((diff != 0).sum())}
        out[scen] = row
    return out

if __name__ == "__main__":
    legacy, calendar, outp = sys.argv[1:4]
    res = {"legacy_variant": summarize(pd.read_csv(legacy)), "calendar_variant": summarize(pd.read_csv(calendar)),
           "note": "exploratory reconstruction; legacy and calendar variants are different estimators and are not pooled"}
    open(outp, "x").write(json.dumps(res, indent=1))
