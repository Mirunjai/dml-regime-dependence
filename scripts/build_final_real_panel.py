"""Build and independently check the registered contemporaneous six-firm panel."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import exchange_calendars as xc

from src.real_data.aligned_panel import session_returns,prior_market_residuals,pair_statistics,block_bootstrap
from src.real_data.regime_labels import classify_regimes
from src.benchmarks.event_study import estimate_market_model_event_study


def build(config_path, source, output):
    config=json.loads(Path(config_path).read_text());source=Path(source);out=Path(output)
    out.mkdir(parents=True,exist_ok=False)
    source_paths=[Path(__file__),Path('src/real_data/aligned_panel.py'),Path('src/real_data/regime_labels.py'),Path('src/benchmarks/event_study.py'),Path(config_path)]
    code_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    manifest=json.loads((source/'manifest.json').read_text());requests={r['symbol']:r for r in manifest['requests']}
    series={};hashes={};provider_missing={}
    for symbol in config['tickers']+config['market_tickers']+[config['vix_ticker'],'BFH']:
        r=requests[symbol]
        if r['status']!='ok':raise ValueError(f'Acquisition failed for {symbol}')
        p=source/r['file'];sha=hashlib.sha256(p.read_bytes()).hexdigest()
        if sha!=r['sha256']:raise ValueError('Acquisition source changed')
        frame=pd.read_csv(p,parse_dates=['date']).set_index('date').sort_index()
        if frame.index.has_duplicates:raise ValueError('Duplicate provider dates')
        field='Close' if symbol=='^VIX' else 'Adj Close'
        values=frame[field].astype(float)
        if np.isinf(values).any() or (values.dropna()<=0).any():raise ValueError('Invalid nonmissing provider observations')
        provider_missing[symbol]={'missing_price_rows':int(values.isna().sum()),'dates':values.index[values.isna()].strftime('%Y-%m-%d').tolist()}
        series[symbol]=values;hashes[symbol]=sha
    calendar=xc.get_calendar('XNYS',start='2000-01-01',end='2022-01-01')
    vix_expected=calendar.sessions_in_range(series['^VIX'].index.min(),series['^VIX'].index.max()).tz_localize(None)
    missing_vix_dates=series['^VIX'].index[series['^VIX'].isna()]
    if len(missing_vix_dates.intersection(vix_expected)):
        raise ValueError('Missing VIX observations on expected exchange sessions')
    # keepna=True returned explicit holiday rows. Remove only those independently
    # verified non-session missing rows; never fill or skip a missing trading day.
    series['^VIX']=series['^VIX'].dropna()
    provider_missing['^VIX']['handling']='All missing rows verified as non-XNYS sessions; excluded from observed-VIX rolling windows, with no imputation.'
    sessions=calendar.sessions_in_range('2007-01-03','2021-12-31').tz_localize(None)
    prices=pd.DataFrame({s:series[s] for s in config['tickers']+['SPY','^GSPC']})
    returns=session_returns(prices,sessions)
    days=sessions[(sessions>=config['panel_start'])&(sessions<config['panel_end_exclusive'])]
    panel=returns.loc[days,config['tickers']]
    labels=classify_regimes(pd.DataFrame({'announcement_date':days}),series['^VIX'],window=20,reference_years=5)
    if labels.regime_label.eq('insufficient_data').any():raise ValueError('Unclassifiable panel dates')
    maximum=0.;mismatches=0
    for row in labels.itertuples():
        h=series['^VIX'].loc[(series['^VIX'].index<row.announcement_date)&(series['^VIX'].index>=row.announcement_date-pd.DateOffset(years=5))].to_numpy()
        means=np.convolve(h,np.ones(20)/20,mode='valid');low,high=np.quantile(means[:-1],[.25,.75]);latest=means[-1]
        lab='calm' if latest<low else 'turbulent' if latest>high else 'mixed'
        mismatches+=lab!=row.regime_label;maximum=max(maximum,abs(latest-row.pre_event_vix20),abs(low-row.vix_p25),abs(high-row.vix_p75))
    if mismatches or maximum>1e-10:raise ValueError('Independent label verification failed')
    state=pd.Series(labels.regime_label.to_numpy(),index=days,name='regime_label')
    all_residuals=prior_market_residuals(returns[config['tickers']],returns['^GSPC'])
    residuals=all_residuals.loc[days]
    raw_pairs=pair_statistics(panel,state,config['minimum_pair_label_sessions'])
    residual_pairs=pair_statistics(residuals,state,config['minimum_pair_label_sessions'])
    bootstrap={}
    for kind,data in (('raw_returns',panel),('prior_market_residuals',residuals)):
        bootstrap[kind]=[]
        for length in [config['bootstrap']['primary_block_length']]+config['bootstrap']['sensitivity_block_lengths']:
            reps=config['bootstrap']['primary_replications'] if length==config['bootstrap']['primary_block_length'] else config['bootstrap']['sensitivity_replications']
            bootstrap[kind].append(block_bootstrap(data,state,length=length,replications=reps,seed=config['bootstrap']['seed']+length,minimum=config['minimum_pair_label_sessions']))
    panel.index.name='date';panel.assign(regime_label=state).to_csv(out/'aligned_returns.csv',float_format='%.17g')
    residuals.index.name='date';residuals.assign(regime_label=state).to_csv(out/'prior_market_residuals.csv',float_format='%.17g')
    labels.rename(columns={'announcement_date':'date'}).to_csv(out/'daily_labels_and_thresholds.csv',index=False,float_format='%.17g')
    pd.DataFrame(raw_pairs).to_csv(out/'raw_pair_correlations.csv',index=False);pd.DataFrame(residual_pairs).to_csv(out/'residual_pair_correlations.csv',index=False)
    returns.index.name='date';returns.to_csv(out/'derived_returns_full.csv',float_format='%.17g')
    # A source-verified issuer crosswalk, never an assertion that the original
    # missing file or its historical adjustment vintage was recovered.
    bfh=session_returns(pd.DataFrame({'ADS':series['BFH']}),sessions)['ADS']
    fresh=returns.assign(ADS=bfh);fresh.to_csv(out/'reacquired_event_returns.csv',float_format='%.17g');events=pd.read_csv('data/processed/week3_event_day_zero.csv')
    classical=[]
    for row in events.itertuples():
        if row.ticker=='CTLT':continue
        r={'ticker':row.ticker,'event_day_zero':row.event_day_zero,'source_symbol':'BFH' if row.ticker=='ADS' else row.ticker}
        for name,window in (('primary',(-1,1)),('short',(0,1)),('wide',(-5,5))):
            fit=estimate_market_model_event_study(fresh,stock_ticker=row.ticker,market_ticker='^GSPC',event_session=row.event_day_zero,estimation_window=(-250,-31),event_window=window,expected_sessions=sessions)
            r['car_'+name]=fit['car']
            if name=='primary':r.update(alpha=fit['alpha'],beta=fit['beta'],estimation_observations=fit['estimation_observations'])
        classical.append(r)
    pd.DataFrame(classical).to_csv(out/'fresh_classical_event_study.csv',index=False,float_format='%.17g')
    legacy=pd.read_csv('results/benchmarks/week3_classical_event_study.csv').set_index('ticker')
    comparison=[]
    for r in classical:
        for field in ('car_primary','car_short','car_wide','alpha','beta','estimation_observations'):
            comparison.append({'ticker':r['ticker'],'field':field,'legacy':float(legacy.loc[r['ticker'],field]),'fresh':float(r[field]),'difference':float(r[field]-legacy.loc[r['ticker'],field])})
    pd.DataFrame(comparison).to_csv(out/'legacy_classical_comparison.csv',index=False,float_format='%.17g')
    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=code_hashes[str(p)] for p in source_paths):raise ValueError('Analysis source changed during execution')
    report={'schema':'final_aligned_panel_analysis_v1','config':config,'source_sha256':hashes,'analysis_source_sha256':code_hashes,'provider_missing_observations':provider_missing,
            'calendar':{'name':'XNYS','package_version':xc.__version__,'expected_panel_sessions':len(days)},
            'panel_sessions':len(panel),'firms':list(panel),'first_date':str(days.min().date()),'last_date':str(days.max().date()),
            'label_counts':state.value_counts().to_dict(),'valid_returns':int(panel.notna().sum().sum()),
            'missing_returns':int(panel.isna().sum().sum()),'label_check':{'mismatches':mismatches,'maximum_absolute_difference':maximum},
            'raw_pair_statistics':raw_pairs,'residual_pair_statistics':residual_pairs,'block_bootstrap':bootstrap,
            'classical_rows':classical,'legacy_comparisons':comparison,'original_missing_inputs_authenticated':False,
            'ADS_identity':{'historical_ticker':'ADS','current_ticker':'BFH','issuer_CIK':'0001101215','ticker_change':'2022-04-04',
                            'source':'https://www.sec.gov/Archives/edgar/data/1101215/000110121522000058/form_8-k.htm',
                            'scope':'Same issuer verified; freshly reacquired adjusted history, not original missing file.'},
            'CTLT':'Original missing-data case preserved; no invented observations or SCM execution.',
            'return_units':'fractional simple adjusted-close returns; no filling, clipping or trimming',
            'scope':'Descriptive selected six-firm common-window analysis; no causal effect or known-truth coverage claim.'}
    (out/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('panel_sessions','valid_returns','missing_returns','label_counts','label_check')}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();build(a.config,a.source,a.out)
