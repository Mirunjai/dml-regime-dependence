"""Independent event-graph manipulation checks; no estimator outcomes select values."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import numpy as np

from research.week2_completion.dgp import spawn_rngs, simulate_calendar_regimes


def structural_world(seed, n, k, density, T=260, H=5, shock_sd=.4):
    streams=spawn_rngs(seed)
    dates=streams['dates'].integers(0,T-H+1,size=n)
    ids,_,_=simulate_calendar_regimes(T,density,k,shock_sd,streams['layout'],streams['shock'])
    windows=ids[dates[:,None]+np.arange(H)[None,:]]
    loadings=np.zeros((n,k),dtype=np.int64)
    for r in range(k):loadings[:,r]=(windows==r).sum(axis=1)
    memberships=[tuple(np.flatnonzero(row).tolist()) for row in loadings]
    # Exact union-pair count from unique membership sets, with no n-by-n matrix.
    counts=Counter(memberships);shared=0
    items=list(counts.items())
    for i,(group,number) in enumerate(items):
        if group:shared+=number*(number-1)//2
        for other,other_number in items[i+1:]:
            if set(group).intersection(other):shared+=number*other_number
    pairs=n*(n-1)//2
    # Analytical error covariance from common shocks, conditional on the layout.
    # Idiosyncratic GARCH returns have unconditional variance 1 per period and
    # are uncorrelated across firms. No observed Y or treatment truth is used.
    diagonal=H+shock_sd**2*np.sum(loadings**2,axis=1)
    standardized=loadings/np.sqrt(diagonal[:,None])
    correlation_sum=shock_sd**2*(np.sum(standardized.sum(axis=0)**2)-np.sum(standardized**2))
    return {'n':n,'K':k,'configured_density':density,'shared_pairs':shared,
            'pair_density':shared/pairs,'exposed_share':float(np.mean(loadings.sum(axis=1)>0)),
            'average_common_shock_correlation':float(correlation_sum/(2*pairs)),
            'average_marginal_error_variance':float(diagonal.mean())}


def summarize(rows):
    out={'worlds':len(rows)}
    for key in ('shared_pairs','pair_density','exposed_share','average_common_shock_correlation','average_marginal_error_variance'):
        a=np.asarray([r[key] for r in rows],float)
        out[key]={'mean':float(a.mean()),'mcse':float(a.std(ddof=1)/np.sqrt(len(a)))}
    return out


def run(output, reps=1000):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    seeds=range(810000,810000+reps);grid=[];scaling=[]
    for k in (4,16):
        for d in (.25,.3,.31,.5,.75):
            rows=[structural_world(seed,400,k,d) for seed in seeds]
            grid.append({'K':k,'density':d,**summarize(rows)})
        means=[]
        for n in (200,400,800,1600):
            result=summarize([structural_world(seed,n,k,.5) for seed in seeds])
            means.append(result['shared_pairs']['mean'])
            scaling.append({'K':k,'n':n,**result})
        slope=float(np.polyfit(np.log([200,400,800,1600]),np.log(means),1)[0])
        print('K',k,'shared-pair scaling exponent',slope,flush=True)
    matches=[]
    for kind,(k1,d1),(k2,d2) in [('pair_density',(4,.31),(16,.5)),('exposed_share',(4,.5),(16,.3))]:
        differences=[]
        for seed in seeds:
            a,b=structural_world(seed,400,k1,d1),structural_world(seed,400,k2,d2)
            differences.append({key:a[key]-b[key] for key in ('pair_density','exposed_share','average_common_shock_correlation','average_marginal_error_variance')})
        matches.append({'kind':kind,'left':{'K':k1,'density':d1},'right':{'K':k2,'density':d2},
                        'paired_differences':{key:{'mean':float(np.mean([r[key] for r in differences])),
                                                   'mcse':float(np.std([r[key] for r in differences],ddof=1)/np.sqrt(reps))}
                                              for key in differences[0]}})
    result={'schema':'final_structural_validation_v1','seed_range':[810000,810000+reps],
            'grid':grid,'scaling':scaling,'matches':matches,
            'interpretation':'Fixed nonzero pair density implies O(n^2) dependent event pairs even when each event has only one regime label. Rare multi-membership is distinct from sparse cross-event dependence.'}
    (output/'structure.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--reps',type=int,default=1000)
    a=p.parse_args();run(a.out,a.reps)
