"""Independent numerical audit of the final derived panel, without producer imports.

Direct least squares, dot products and an independently written calendar-block
loop check the released CSVs against source observations and frozen summaries.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import numpy as np
import pandas as pd


def audit(source, derived, output):
    source, derived, output = map(Path, (source, derived, output))
    output.mkdir(parents=True, exist_ok=False)
    report = json.loads((derived/'audit.json').read_text())
    manifest = json.loads((source/'manifest.json').read_text())
    files = {r['symbol']: source/r['file'] for r in manifest['requests'] if r['status']=='ok'}
    panel = pd.read_csv(derived/'aligned_returns.csv', index_col='date', parse_dates=True)
    residual = pd.read_csv(derived/'prior_market_residuals.csv', index_col='date', parse_dates=True)
    full = pd.read_csv(derived/'derived_returns_full.csv', index_col='date', parse_dates=True)
    firms = report['firms']; dates = panel.index
    discrepancies = {}; checks = 0
    def compare(name, actual, expected, tolerance=1e-10):
        nonlocal checks
        a, b = np.asarray(actual, float), np.asarray(expected, float)
        if a.shape != b.shape or not np.array_equal(np.isnan(a), np.isnan(b)):
            raise ValueError(f'{name}: shape/missingness mismatch')
        gap = float(np.nanmax(np.abs(a-b))) if np.isfinite(a).any() else 0.
        if gap > tolerance: raise ValueError(f'{name}: numerical difference {gap}')
        discrepancies[name] = gap; checks += a.size
    for symbol in firms+['^GSPC','SPY']:
        raw = pd.read_csv(files[symbol], index_col='date', parse_dates=True)['Adj Close']
        p = raw.reindex(full.index).to_numpy(float)
        ret = np.r_[np.nan, p[1:]/p[:-1]-1.]
        compare('source_returns_'+symbol, full[symbol], ret)
        if symbol in firms: compare('released_returns_'+symbol, panel[symbol], full.loc[dates,symbol])
    for i in [0,17,100,500,1000,len(dates)-1]:
        day = dates[i]; k = full.index.get_loc(day)
        for firm in firms:
            prior = full.iloc[max(0,k-252):k][['^GSPC',firm]].dropna()
            if len(prior)<200: expected=np.nan
            else:
                design=np.column_stack([np.ones(len(prior)),prior['^GSPC']])
                coefficients=np.linalg.lstsq(design,prior[firm],rcond=None)[0]
                expected=full.loc[day,firm]-np.dot([1,full.loc[day,'^GSPC']],coefficients)
            compare(f'prior_OLS_{day.date()}_{firm}',[residual.loc[day,firm]],[expected])
    labels = panel.regime_label.to_numpy()
    for kind, data in [('raw_returns',panel),('prior_market_residuals',residual)]:
        a=data[firms].to_numpy(float)
        def statistic(ids):
            means=[]
            for lab in ['calm','turbulent']:
                sub=a[ids][(labels[ids]==lab)&np.isfinite(a[ids]).all(axis=1)]
                if len(sub)<60: raise ValueError('Insufficient aligned bootstrap observations')
                centered=sub-sub.mean(axis=0)
                gram=centered.T@centered
                corr=gram/np.sqrt(np.outer(np.diag(gram),np.diag(gram)))
                means.append(float(np.mean(corr[np.triu_indices(len(firms),1)])))
            return means[1]-means[0]
        for frozen in report['block_bootstrap'][kind]:
            rng=np.random.default_rng(frozen['seed']); n=len(a); length=frozen['block_length']; vals=[]
            for _ in range(frozen['planned']):
                starts=rng.integers(0,n-length+1,size=int(np.ceil(n/length)))
                ids=np.concatenate([np.arange(s,s+length) for s in starts])[:n]
                vals.append(statistic(ids))
            compare(f'{kind}_L{length}_observed',[statistic(np.arange(n))],[frozen['observed']['difference']])
            compare(f'{kind}_L{length}_bootstrap',np.quantile(vals,[.025,.975]),frozen['percentile95'])
            compare(f'{kind}_L{length}_sd',[np.std(vals,ddof=1)],[frozen['bootstrap_sd']])
    events=pd.read_csv(derived/'reacquired_event_returns.csv',index_col='date',parse_dates=True)
    for row in report['classical_rows']:
        k=events.index.get_loc(pd.Timestamp(row['event_day_zero'])); prior=events.iloc[k-250:k-30][['^GSPC',row['ticker']]]
        if len(prior)!=220 or prior.isna().any().any():raise ValueError('Invalid event estimation data')
        ab=np.linalg.lstsq(np.column_stack([np.ones(220),prior['^GSPC']]),prior[row['ticker']],rcond=None)[0]
        compare('classical_parameters_'+row['ticker'],ab,[row['alpha'],row['beta']])
        for name,lo,hi in [('primary',-1,1),('short',0,1),('wide',-5,5)]:
            part=events.iloc[k+lo:k+hi+1]
            car=float((part[row['ticker']]-ab[0]-ab[1]*part['^GSPC']).sum())
            compare('classical_'+name+'_'+row['ticker'],[car],[row['car_'+name]])
    result={'schema':'independent_final_real_panel_audit_v1','passed':True,'numeric_comparisons':checks,
            'maximum_absolute_difference':max(discrepancies.values()),'checks':discrepancies,
            'panel_dates':len(panel),'firms':firms,'labels':panel.regime_label.value_counts().to_dict(),
            'csv_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in derived.glob('*.csv')},
            'audit_scope':'Independent direct return, prior-regression, joint-block-bootstrap and classical-CAR recomputation; issuer identity and source provenance remain separately documented.',
            'historical_original_inputs_authenticated':False}
    (output/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','numeric_comparisons','maximum_absolute_difference','panel_dates']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--derived',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();audit(a.source,a.derived,a.out)
