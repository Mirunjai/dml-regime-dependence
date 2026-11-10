"""Exploratory DGP structure scan (Mirun). Not a Gate 2 check, not approved evidence.

Reports, for the calendar-time DGP in research/week2_completion, how event-level
exposure and the number of dependence-graph components (the grouped-fold units)
vary with density and K. Also tabulates fourth-moment margins of the canonical
(arch_share=.1) vs legacy (alpha=.10) GARCH families. Writes a NEW json file;
refuses to overwrite.
"""
import json, sys
from pathlib import Path
import numpy as np
from src.dgp.volatility import garch_parameters
from research.week2_completion.dgp import Config, build_world
from research.week2_completion.dml import _components

def main(out, seeds=100):
    out = Path(out)
    if out.exists():
        sys.exit(f"refusing to overwrite {out}")
    garch = []
    for rho in (.5, .8, .9, .95, .97, .99):
        c = garch_parameters(rho, arch_share=.1)
        legacy = 1 - rho**2 - 2*.10**2
        garch.append(dict(rho=rho, canonical_alpha=c.alpha, canonical_margin=c.fourth_moment_margin,
                          legacy_alpha=.10, legacy_margin=legacy))
    grid = {}
    for dens in (.1, .25, .5, .75):
        for K in (2, 4, 8, 16):
            comps, mx, expo, multi, regs = [], [], [], [], []
            for s in range(seeds):
                d = build_world(Config(density=dens, n_regimes=K, seed=s, sd_factor=0.0))
                m = d["cluster_memberships"]; lab = _components(m)
                comps.append(len(np.unique(lab))); mx.append(int(np.bincount(lab).max()))
                expo.append(float(np.mean([len(x) > 0 for x in m])))
                multi.append(float(np.mean([len(x) > 1 for x in m])))
                regs.append(len({r for x in m for r in x}))
            grid[f"density={dens}|K={K}"] = dict(
                seeds=seeds, components_mean=float(np.mean(comps)), components_min=int(min(comps)),
                largest_component_mean=float(np.mean(mx)), exposed_event_fraction=float(np.mean(expo)),
                multi_regime_event_fraction=float(np.mean(multi)),
                distinct_regimes_touched_mean=float(np.mean(regs)))
    out.write_text(json.dumps(dict(garch_fourth_moment=garch, calendar_grid=grid,
        config="n=400,T=260,H=5,sd_factor=0 (factor off; seeds 0..99)"), indent=1))
    print("wrote", out)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/tables/mirun_dgp_component_scan.json")
