"""Compare the two GARCH(1,1) parameterizations used by Project A.

The historical Week-2 DGP fixes alpha=.10. The canonical src/dgp implementation
sets alpha=.10*rho (arch_share=.10). Both hold unconditional variance at one,
but they are not the same process. This script documents parameter and moment
differences and runs a finite-sample diagnostic at rho=.90 and .99.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from research.week2_completion.dgp import simulate_volatility as fixed_alpha_sim
from src.dgp.volatility import simulate_volatility as canonical_sim, garch_parameters

N_FIRMS, N_PERIODS, BURN, SEED = 200, 5000, 1000, 20261112

def acf1(x):
    x=np.asarray(x,dtype=float).ravel()
    a=x[:-1]; b=x[1:]
    return float(np.corrcoef(a,b)[0,1])

def one(rho, mode):
    if mode=="canonical":
        alpha=.10*rho; share=.10
        sigma,eps=canonical_sim(N_FIRMS,N_PERIODS,rho,np.random.default_rng(SEED),
            unconditional_variance=1.0,arch_share=share,burn_in=BURN)
    else:
        alpha=.10; share=alpha/rho
        sigma,eps=fixed_alpha_sim(N_FIRMS,N_PERIODS,rho,np.random.default_rng(SEED),
            alpha=alpha,sigma2_bar=1.0,burn=BURN)
    p=garch_parameters(rho,unconditional_variance=1.0,arch_share=share)
    ret=sigma*eps
    return {
      "mode":mode,"rho":rho,"alpha":p.alpha,"beta":p.beta,"omega":p.omega,
      "persistence":p.persistence,"unconditional_variance_target":1.0,
      "finite_fourth_moment":p.has_finite_fourth_moment,
      "fourth_moment_margin":p.fourth_moment_margin,
      "sample_mean_conditional_variance":float(np.mean(sigma**2)),
      "sample_mean_squared_return":float(np.mean(ret**2)),
      "sample_squared_return_acf1":acf1(ret**2) if p.has_finite_fourth_moment else None,
      "population_squared_return_acf1":float(p.squared_return_acf(1)[1]) if p.has_finite_fourth_moment else None,
      "sample_shape":list(ret.shape),"seed":SEED,"burn_in":BURN,
    }

def main():
    rows=[one(rho,mode) for rho in (.90,.99) for mode in ("fixed_alpha","canonical")]
    out={"schema":"project_a_garch_parameterization_comparison_v1",
      "status":"TECHNICAL_RECONCILIATION_NOT_SCIENTIFIC_GATE_APPROVAL",
      "fixed_alpha_definition":"alpha=0.10; beta=rho-alpha",
      "canonical_definition":"alpha=0.10*rho; beta=rho-alpha",
      "both_hold_unconditional_variance_at_one":True,
      "dgp_file_sha1":hashlib.sha1((ROOT/"research/week2_completion/dgp.py").read_bytes()).hexdigest(),
      "canonical_sha256":hashlib.sha256((ROOT/"src/dgp/volatility.py").read_bytes()).hexdigest(),
      "rows":rows,
      "conclusion":"The implementations are not pathwise or parametrically identical. At rho=.90 both have finite fourth moments but different ARCH response and squared-return ACF. At rho=.99 fixed alpha=.10 violates the Gaussian fourth-moment condition while canonical alpha=.099 retains a small positive margin. Both retain finite unconditional variance. Do not describe the rho=.99 variants as moment-equivalent.",
      "limitations":["Different RNG draw order means same seed does not create pathwise identical shocks.",
        "Finite sample moment estimates are diagnostics, not proof of stationary population moments.",
        "No GARCH parameterization is selected as the team's approved production choice."]}
    path=ROOT/"results/tables/mirun_garch_parameterization_comparison_2026-11-12.json"
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
