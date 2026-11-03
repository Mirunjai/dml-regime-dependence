"""Cross-fitted partially-linear DML with explicit multiway regime membership.

The multiway score sandwich uses inclusion-exclusion over every nonempty
intersection of regime memberships. It is an asymptotic covariance estimator,
not a few-cluster correction. Negative variance / insufficient grouped
components are explicit failures, never silently clipped.
"""
from __future__ import annotations
import itertools, time
import numpy as np
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor

CELLS = (("random","naive"),("random","multiway"),("grouped","naive"),("grouped","multiway"))

def _validate_arrays(Y,D,X,memberships):
    Y=np.asarray(Y,dtype=float); D=np.asarray(D,dtype=float); X=np.asarray(X,dtype=float)
    n=len(Y)
    if Y.ndim!=1 or D.shape!=(n,) or X.ndim!=2 or X.shape[0]!=n or len(memberships)!=n:
        raise ValueError("Expected Y,D[n], X[n,p], and n membership sets")
    if n<4 or X.shape[1]<1 or not (np.isfinite(Y).all() and np.isfinite(D).all() and np.isfinite(X).all()):
        raise ValueError("Inputs must be finite and contain at least four observations")
    clean=[]
    for m in memberships:
        t=tuple(sorted(set(int(k) for k in m)))
        if any(k<0 for k in t): raise ValueError("Memberships contain only nonnegative regime IDs")
        clean.append(t)
    return Y,D,X,clean

def _components(memberships):
    """Connected components of the event-regime bipartite dependence graph."""
    n=len(memberships); parent=list(range(n)); rank=[0]*n; owner={}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a==b:return
        if rank[a]<rank[b]:a,b=b,a
        parent[b]=a
        if rank[a]==rank[b]:rank[a]+=1
    for i,m in enumerate(memberships):
        for k in m:
            if k in owner: union(i,owner[k])
            else: owner[k]=i
    roots=[find(i) for i in range(n)]
    _,labels=np.unique(roots,return_inverse=True)
    return labels

def make_folds(scheme, memberships, n_folds, rng):
    n=len(memberships)
    if isinstance(n_folds,bool) or not isinstance(n_folds,int) or n_folds<2 or n_folds>n:
        raise ValueError("n_folds must be between 2 and n")
    if scheme=="random":
        perm=rng.permutation(n); fold=np.empty(n,dtype=int); fold[perm]=np.arange(n)%n_folds
        return fold
    if scheme!="grouped": raise ValueError("scheme must be random or grouped")
    groups=_components(memberships); uniq,inv=np.unique(groups,return_inverse=True)
    if len(uniq)<n_folds:
        raise ValueError(f"Only {len(uniq)} independent dependence-graph components; cannot form {n_folds} grouped folds")
    sizes=np.bincount(inv); order=np.lexsort((rng.random(len(uniq)),-sizes))
    load=np.zeros(n_folds); gf=np.empty(len(uniq),dtype=int)
    for g in order:
        f=int(np.argmin(load)); gf[g]=f; load[f]+=sizes[g]
    return gf[inv]

def _learner(seed,n_estimators=40):
    return RandomForestRegressor(n_estimators=n_estimators,min_samples_leaf=8,max_features=.5,n_jobs=1,random_state=int(seed))

def crossfit(Y,D,X,fold,n_folds,seed):
    n=len(Y)
    if fold.shape!=(n,) or set(np.unique(fold))!=set(range(n_folds)):
        raise ValueError("Every fold must be nonempty and represented")
    my=np.empty(n); md=np.empty(n)
    for k in range(n_folds):
        tr=fold!=k; te=fold==k
        if tr.sum()<2 or not te.any(): raise ValueError(f"Invalid train/test partition for fold {k}")
        my[te]=_learner(seed+k).fit(X[tr],Y[tr]).predict(X[te])
        md[te]=_learner(seed+100+k).fit(X[tr],D[tr]).predict(X[te])
    return Y-my,D-md

def _multiway_meat(psi,memberships):
    """Estimate sum_i sum_j psi_i psi_j 1[M_i intersect M_j != empty].

    Inclusion-exclusion: for each distinct nonempty regime subset S, add
    (-1)^(|S|+1) * (sum_{i:S subset M_i} psi_i)^2. Singleton/no-regime
    events are independent and contribute their own squared score.
    """
    meat=0.0
    subsets=set()
    for m in memberships:
        for r in range(1,len(m)+1):
            subsets.update(itertools.combinations(m,r))
    for S in subsets:
        mask=np.array([set(S).issubset(m) for m in memberships])
        sign=1.0 if len(S)%2 else -1.0
        meat += sign*float(np.sum(psi[mask])**2)
    for i,m in enumerate(memberships):
        if not m: meat += float(psi[i]**2)
    return meat, len(subsets)

def estimate(Yt,Dt,memberships,alpha=.05):
    Yt=np.asarray(Yt,dtype=float); Dt=np.asarray(Dt,dtype=float)
    if Yt.ndim!=1 or Dt.shape!=Yt.shape or not np.isfinite(Yt).all() or not np.isfinite(Dt).all():
        raise ValueError("Residuals must be matching finite vectors")
    J=float(np.sum(Dt**2))
    if not np.isfinite(J) or J<=np.finfo(float).eps:
        raise ValueError("Residualized treatment has zero/near-zero sum of squares")
    tau=float(np.sum(Dt*Yt)/J)
    psi=Dt*(Yt-tau*Dt)
    naive=float(np.sqrt(np.sum(psi**2))/J)
    meat,n_intersections=_multiway_meat(psi,memberships)
    if not np.isfinite(meat) or meat<=0:
        raise ValueError(f"Multiway sandwich meat is nonpositive ({meat}); inference undefined")
    multiway=float(np.sqrt(meat)/J)
    if not 0<alpha<1: raise ValueError("alpha must be in (0,1)")
    z=float(norm.ppf(1-alpha/2))
    return {"tau":tau,"se_naive":naive,"se_multiway":multiway,
            "n_multiway_intersections":n_intersections,"score_sum":float(psi.sum()),
            "J":J,"critical_value":z}

def run_dml(data,n_folds=5,seed=0,alpha=.05):
    Y,D,X,m=_validate_arrays(data["Y"],data["D"],data["X"],data["cluster_memberships"])
    rows=[]; runtime={}
    for scheme in ("random","grouped"):
        t=time.perf_counter()
        fold=make_folds(scheme,m,n_folds,np.random.default_rng(seed+(0 if scheme=="random" else 1)))
        Yt,Dt=crossfit(Y,D,X,fold,n_folds,seed)
        est=estimate(Yt,Dt,m,alpha)
        runtime[scheme]=time.perf_counter()-t
        for variance,sekey in (("naive","se_naive"),("multiway","se_multiway")):
            se=est[sekey]; tau=est["tau"]; z=est["critical_value"]
            rows.append({"folds":scheme,"variance":variance,"tau":tau,"se":se,
                         "lo":tau-z*se,"hi":tau+z*se,
                         "n_multiway_intersections":est["n_multiway_intersections"]})
    return rows,runtime
