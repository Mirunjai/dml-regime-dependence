import numpy as np
import pandas as pd
import pytest
from types import SimpleNamespace
from src.benchmarks.event_study import estimate_market_model_event_study, adjusted_prices_to_returns
from src.real_data.regime_labels import classify_regimes
from src.benchmarks import synthetic_control as scm


def frame():
    dates=pd.bdate_range('2020-01-01',periods=30)
    m=np.linspace(-.01,.01,30)
    return pd.DataFrame({'stock':.001+1.2*m,'market':m},index=dates)


@pytest.mark.parametrize('bad',[1.5,True])
def test_dated_window_no_silent_coercion(bad):
    f=frame()
    with pytest.raises(ValueError,match='integers'):
        estimate_market_model_event_study(f,stock_ticker='stock',market_ticker='market',event_session=f.index[20],estimation_window=(-10,-2),event_window=(0,bad))


def test_dated_nonfinite_is_not_a_success():
    f=frame();f.iloc[20,0]=np.inf
    with pytest.raises(ValueError,match='nonfinite'):
        estimate_market_model_event_study(f,stock_ticker='stock',market_ticker='market',event_session=f.index[20],estimation_window=(-10,-2),event_window=(0,1))


def test_dates_known_effect_and_pre_event_fit():
    f=frame();f.iloc[20:23,0]+=.02
    r=estimate_market_model_event_study(f,stock_ticker='stock',market_ticker='market',event_session=f.index[20],estimation_window=(-10,-2),event_window=(0,2))
    assert r['car']==pytest.approx(.06)
    assert r['beta']==pytest.approx(1.2)


@pytest.mark.parametrize('value',[0.,-1.,np.inf,'broken'])
def test_bad_prices_rejected(value):
    f=pd.DataFrame({'price':[1.,value,2.]},index=pd.date_range('2020-01-01',periods=3))
    with pytest.raises((ValueError,TypeError)):
        adjusted_prices_to_returns(f)


def test_missing_prices_not_filled():
    f=pd.DataFrame({'p':[1.,np.nan,2.,4.]},index=pd.date_range('2020-01-01',periods=4))
    r=adjusted_prices_to_returns(f)
    assert r.p.iloc[:3].isna().all() and r.p.iloc[3]==1


def test_optimizer_success_does_not_hide_invalid_weights(monkeypatch):
    monkeypatch.setattr(scm,'minimize',lambda *a,**k:SimpleNamespace(success=True,x=np.array([-.1,1.1]),message='fixture'))
    with pytest.raises(RuntimeError,match='infeasible'):
        scm.fit_synthetic_control([1.,2.],np.array([[1.,0.],[2.,0.]]),[3.],np.array([[3.,0.]]),donor_ids=['a','b'])


@pytest.mark.parametrize('window',[True,2.5])
def test_vix_integer_window(window):
    with pytest.raises(ValueError):
        classify_regimes(pd.DataFrame({'announcement_date':['2020-02-01']}),pd.Series(20.,index=pd.date_range('2020-01-01',periods=40)),window=window)


def test_missing_calendar_session_does_not_shift_window():
    f=frame();sessions=f.index;anchor=f.index[20];f=f.drop(f.index[19])
    with pytest.raises(ValueError,match='missing'):
        estimate_market_model_event_study(f,stock_ticker='stock',market_ticker='market',event_session=anchor,estimation_window=(-10,-2),event_window=(-1,1),expected_sessions=sessions)


def test_empty_donor_template_is_not_completed_validation(monkeypatch):
    from src.real_data import validate_week3_donors as d
    monkeypatch.setattr('sys.argv',['validator'])
    assert d.main()==1
    assert 'CTLT' in d.TREATED
