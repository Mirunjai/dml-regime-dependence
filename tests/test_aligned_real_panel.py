"""Calendar gaps, information timing and joint-block calculation checks."""
import numpy as np
import pandas as pd
from src.real_data.aligned_panel import session_returns,prior_market_residuals,block_bootstrap


def test_missing_session_does_not_become_a_multiday_one_session_return():
    days=pd.bdate_range('2020-01-01',periods=5)
    prices=pd.DataFrame({'A':[100.,101.,103.,104.]},index=days[[0,1,3,4]])
    r=session_returns(prices,days)
    assert np.isnan(r.loc[days[2],'A']) and np.isnan(r.loc[days[3],'A'])
    assert r.loc[days[4],'A']==104/103-1


def test_market_fit_uses_only_prior_observations():
    rng=np.random.default_rng(17);days=pd.bdate_range('2020-01-01',periods=100)
    market=pd.Series(rng.normal(size=100),index=days)
    stock=pd.DataFrame({'A':.2+1.3*market+rng.normal(scale=.1,size=100)},index=days)
    first=prior_market_residuals(stock,market,window=30,minimum=20)
    altered=stock.copy();altered.iloc[61:]+=1000.
    second=prior_market_residuals(altered,market,window=30,minimum=20)
    np.testing.assert_allclose(first.iloc[:61],second.iloc[:61],equal_nan=True)


def test_joint_block_resampling_preserves_identical_firm_correlations():
    rng=np.random.default_rng(7);days=pd.bdate_range('2020-01-01',periods=200)
    values=rng.normal(size=200)
    data=pd.DataFrame({'A':values,'B':values,'C':values},index=days)
    labels=pd.Series(np.where(np.arange(200)%2,'calm','turbulent'),index=days)
    r=block_bootstrap(data,labels,length=10,replications=20,seed=6,minimum=30)
    assert r['valid']==20 and r['failed']==0
    np.testing.assert_allclose(r['observed']['difference'],0.,atol=1e-14)
    np.testing.assert_allclose(r['percentile95'],[0.,0.],atol=1e-14)
