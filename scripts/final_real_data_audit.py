"""Feasibility diagnostics from existing inputs; never an approved real panel."""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import numpy as np
import pandas as pd
from src.real_data.regime_labels import classify_regimes


def audit(config_path, output):
    config=json.loads(Path(config_path).read_text())
    prices=pd.read_csv(config['price_input'],parse_dates=['date'])
    vixframe=pd.read_csv(config['vix_input'],parse_dates=['date'])
    vix=vixframe.set_index('date')['vix_close'].sort_index()
    candidates=pd.read_csv(config['candidates'])
    if prices.duplicated(['ticker','date']).any():raise ValueError('Duplicate firm-date')
    if not np.isfinite(prices['adj_close']).all() or (prices['adj_close']<=0).any():raise ValueError('Invalid source price')
    prices=prices.sort_values(['ticker','date'])
    prices['return']=prices.groupby('ticker')['adj_close'].pct_change(fill_method=None)
    dates=pd.DataFrame({'announcement_date':sorted(prices['date'].unique())})
    labelled=classify_regimes(dates,vix,window=config['vix_window'],reference_years=config['reference_years'])
    # Independent convolution/NumPy quantiles, including the five-year truncation.
    max_error=0.; mismatches=0
    for r in labelled.itertuples():
        history=vix.loc[(vix.index<r.announcement_date)&(vix.index>=r.announcement_date-pd.DateOffset(years=config['reference_years']))].to_numpy()
        means=np.convolve(history,np.ones(config['vix_window'])/config['vix_window'],mode='valid')
        low,high=np.quantile(means[:-1],[.25,.75]);latest=means[-1]
        lab='calm' if latest<low else 'turbulent' if latest>high else 'mixed'
        mismatches+=lab!=r.regime_label
        max_error=max(max_error,abs(latest-r.pre_event_vix20),abs(low-r.vix_p25),abs(high-r.vix_p75))
    if mismatches or max_error>1e-10:raise ValueError('Independent label calculation disagrees')
    labels=labelled[['announcement_date','regime_label']].rename(columns={'announcement_date':'date'})
    panel=prices.merge(labels,on='date',validate='many_to_one')
    pairs=[];all_firms=list(candidates['ticker'])
    for a,b in itertools.combinations(all_firms,2):
        x=panel.loc[panel.ticker==a,['date','return','regime_label']]
        y=panel.loc[panel.ticker==b,['date','return']]
        joined=x.merge(y,on='date',suffixes=('_a','_b')).dropna(subset=['return_a','return_b'])
        for label in ('calm','mixed','turbulent'):
            z=joined.loc[joined.regime_label==label];n=len(z)
            cov=np.cov(z[['return_a','return_b']].to_numpy().T,ddof=1) if n>=2 else None
            varok=cov is not None and cov[0,0]>0 and cov[1,1]>0
            corr=float(cov[0,1]/np.sqrt(cov[0,0]*cov[1,1])) if varok else None
            eligible=n>=config['minimum_aligned_sessions'] and varok
            pairs.append({'firm_a':a,'firm_b':b,'regime_label':label,'aligned_sessions':n,
                'status':'descriptive' if eligible else 'insufficient', 'correlation':corr if eligible else None,
                'sample_covariance':float(cov[0,1]) if eligible else None,
                'variance_a':float(cov[0,0]) if eligible else None,'variance_b':float(cov[1,1]) if eligible else None})
    counts=[]
    for ticker in all_firms:
        z=panel.loc[panel.ticker==ticker];valid=z.loc[z['return'].notna()]
        counts.append({'ticker':ticker,'price_rows':len(z),'valid_return_rows':len(valid),'first_date':str(z.date.min().date()) if len(z) else None,
          'last_date':str(z.date.max().date()) if len(z) else None, **{f'{lab}_returns':int((valid.regime_label==lab).sum()) for lab in ('calm','mixed','turbulent')},
          'price_status':'available_exploratory' if len(z) else 'missing_ADS_discrepancy' if ticker=='ADS' else 'missing'})
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    labels.to_csv(output/'daily_labels.csv',index=False);pd.DataFrame(pairs).to_csv(output/'pair_diagnostics.csv',index=False);pd.DataFrame(counts).to_csv(output/'availability.csv',index=False)
    # Returns/prices stay local; release contains labels and aggregate statistics only.
    source_paths=[Path(config_path),Path(__file__),Path(config['price_input']),Path(config['vix_input']),Path(config['candidates']),Path('src/real_data/regime_labels.py')]
    report={'evidence_class':'EXPLORATORY','registered_config':config,'label_dates':len(labels),'label_counts_dates':labels.regime_label.value_counts().to_dict(),
      'independent_label_check':{'mismatches':mismatches,'max_absolute_calculation_error':max_error},
      'candidate_firms':len(candidates),'price_available_firms':int(sum(x['price_rows']>0 for x in counts)),
      'return_rows':int(panel['return'].notna().sum()),'pairs_with_any_overlap':len({(r['firm_a'],r['firm_b']) for r in pairs if r['aligned_sessions']>0}),
      'descriptive_pairs_by_label':{lab:sum(r['regime_label']==lab and r['status']=='descriptive' for r in pairs) for lab in ('calm','mixed','turbulent')},
      'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'availability':counts,'pairs':pairs,
      'conclusion':'Sparse staggered windows do not supply a validated broad daily calm/turbulent panel; available pair correlations are descriptive feasibility outputs only.'}
    (output/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('label_dates','return_rows','pairs_with_any_overlap','descriptive_pairs_by_label','independent_label_check')}))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args();audit(a.config,a.output)
