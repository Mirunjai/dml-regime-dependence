"""Calendar-aligned returns and descriptive regime comparisons, without imputation."""
from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from scipy.stats import rankdata


def session_returns(prices, sessions):
    """Compute adjacent expected-session simple returns; missing rows stay missing."""
    frame=prices.copy();frame.index=pd.DatetimeIndex(frame.index).normalize()
    sessions=pd.DatetimeIndex(sessions).normalize()
    if frame.index.has_duplicates or sessions.has_duplicates or not sessions.is_monotonic_increasing:
        raise ValueError('Dates must be unique; sessions must be ordered')
    a=frame.to_numpy(dtype=float)
    if np.isinf(a).any() or np.any(a[np.isfinite(a)]<=0):raise ValueError('Observed prices must be finite and positive')
    frame=frame.reindex(sessions)
    return frame.pct_change(fill_method=None)


def prior_market_residuals(returns, market, window=252, minimum=200):
    """Fit each stock's market model using strictly earlier paired observations."""
    if type(window) is not int or type(minimum) is not int or not 3<=minimum<=window:
        raise ValueError('Require integer 3<=minimum<=window')
    out=pd.DataFrame(index=returns.index,columns=returns.columns,dtype=float)
    market=market.reindex(returns.index)
    for name in returns:
        y=returns[name];valid=y.notna()&market.notna();x=market.where(valid);yy=y.where(valid)
        variance=x.rolling(window,min_periods=minimum).var(ddof=1).shift(1)
        covariance=yy.rolling(window,min_periods=minimum).cov(x,ddof=1).shift(1)
        beta=covariance/variance.where(variance>0)
        alpha=yy.rolling(window,min_periods=minimum).mean().shift(1)-beta*x.rolling(window,min_periods=minimum).mean().shift(1)
        out[name]=y-(alpha+beta*market)
    return out


def pair_statistics(returns, labels, minimum=60):
    labels=labels.reindex(returns.index);rows=[]
    for a,b in itertools.combinations(returns.columns,2):
        for label in ('calm','mixed','turbulent'):
            values=returns.loc[labels==label,[a,b]].dropna().to_numpy(float);n=len(values)
            defined=n>=minimum and np.all(np.std(values,axis=0)>0)
            rows.append({'firm_a':a,'firm_b':b,'label':label,'aligned_sessions':n,
                         'status':'descriptive' if defined else 'insufficient',
                         'pearson':float(np.corrcoef(values,rowvar=False)[0,1]) if defined else None,
                         'spearman':float(np.corrcoef(rankdata(values,axis=0),rowvar=False)[0,1]) if defined else None})
    return rows


def mean_pair_correlation(values, labels, minimum=60):
    values=np.asarray(values,float);labels=np.asarray(labels)
    upper=np.triu_indices(values.shape[1],1);means={};counts={}
    for label in ('calm','turbulent'):
        x=values[(labels==label)&np.isfinite(values).all(axis=1)]
        counts[label]=len(x)
        if len(x)<minimum or np.any(np.std(x,axis=0)==0):raise ValueError('Insufficient aligned state observations')
        means[label]=float(np.mean(np.corrcoef(x,rowvar=False)[upper]))
    return {'calm':means['calm'],'turbulent':means['turbulent'],
            'difference':means['turbulent']-means['calm'],'aligned_sessions':counts}


def block_bootstrap(returns, labels, *, length, replications, seed, minimum=60):
    """Resample joint calendar blocks, retaining contemporaneous cross-firm vectors."""
    if type(length) is not int or not 2<=length<=len(returns) or replications<2:raise ValueError('Invalid bootstrap budget/block length')
    x=returns.to_numpy(float);state=labels.reindex(returns.index).to_numpy();n=len(x)
    observed=mean_pair_correlation(x,state,minimum);rng=np.random.default_rng(seed)
    differences=[];failures=[]
    for rep in range(replications):
        starts=rng.integers(0,n-length+1,size=(n+length-1)//length)
        ids=(starts[:,None]+np.arange(length)[None,:]).ravel()[:n]
        try:differences.append(mean_pair_correlation(x[ids],state[ids],minimum)['difference'])
        except ValueError as exc:failures.append({'replication':rep,'error':str(exc)})
    if len(differences)<2:raise ValueError('Bootstrap did not produce usable contrasts')
    return {'observed':observed,'block_length':length,'planned':replications,'valid':len(differences),
            'failed':len(failures),'failures':failures,'percentile95':np.quantile(differences,[.025,.975]).tolist(),
            'bootstrap_sd':float(np.std(differences,ddof=1)),'seed':seed,
            'interpretation':'Descriptive moving-block uncertainty, not causal or known-truth coverage inference'}
