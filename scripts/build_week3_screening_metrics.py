"""Calculate price-based pre-event screening statistics from the saved Yahoo panel."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "raw" / "week3_yahoo"
OUT = ROOT / "data" / "processed" / "week3_price_screening_metrics.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

cand = pd.read_csv(DATA / "candidate_prices_exploratory.csv", parse_dates=["date"])
treated = pd.read_csv(DATA / "treated_prices.csv", parse_dates=["date"])
spy = pd.read_csv(DATA / "spy_market_prices.csv", parse_dates=["date"])
coverage = pd.read_csv(DATA / "candidate_price_coverage.csv")
rows = []
for _, c in coverage.iterrows():
    sub = cand[(cand.treated_ticker == c.treated_ticker) & (cand.ticker == c.ticker)].sort_values("date")
    if sub.empty:
        rows.append({"treated_ticker":c.treated_ticker,"ticker":c.ticker,"fit_sessions":0,
                     "beta_vs_SPY":None,"pre_event_fit_adj_return":None,"median_fit_dollar_volume":None,
                     "treated_pair_fit_return_correlation":None,"treated_pre_event_fit_adj_return":None,
                     "status":"not calculable: no candidate price rows"})
        continue
    event = pd.Timestamp(c.event_day_zero)
    event_dates = sorted(pd.to_datetime(sub.date.unique()))
    if event not in event_dates:
        rows.append({"treated_ticker":c.treated_ticker,"ticker":c.ticker,"fit_sessions":0,
                     "beta_vs_SPY":None,"pre_event_fit_adj_return":None,"median_fit_dollar_volume":None,
                     "treated_pair_fit_return_correlation":None,"treated_pre_event_fit_adj_return":None,
                     "status":"not calculable: event date absent"})
        continue
    eidx = event_dates.index(event)
    fit_dates = set(event_dates[max(0,eidx-252):max(0,eidx-20)])
    fit = sub[sub.date.isin(fit_dates)].copy()
    market = spy[spy.window_start.eq(c.window_start)].copy()
    market["date"] = pd.to_datetime(market.date)
    full_ret = pd.to_numeric(sub.adj_close,errors="coerce").pct_change()
    fit["ret"] = full_ret.loc[fit.index]
    # The first locked-window price has no prior price inside that window.
    if len(fit):
        fit.loc[fit.date.eq(fit.date.min()), "ret"] = float("nan")
    fit["dollar_volume"] = pd.to_numeric(fit.close_raw,errors="coerce") * pd.to_numeric(fit.volume_raw,errors="coerce")
    market["mret"] = pd.to_numeric(market.adj_close,errors="coerce").pct_change()
    joined = fit.merge(market[["date","mret"]],on="date",how="inner").dropna(subset=["ret","mret"])
    beta = joined.ret.cov(joined.mret) / joined.mret.var() if len(joined)>1 and joined.mret.var() else None
    cum = (1+fit.ret.dropna()).prod()-1 if fit.ret.notna().any() else None
    tsub = treated[(treated.ticker == c.treated_ticker) & (treated.window_start == c.window_start)].sort_values("date").copy()
    tsub["ret"] = pd.to_numeric(tsub.adj_close,errors="coerce").pct_change()
    tfit = tsub[tsub.date.isin(fit_dates)]
    if len(tfit):
        tfit.loc[tfit.date.eq(tfit.date.min()), "ret"] = float("nan")
    paired = fit[["date","ret"]].merge(tfit[["date","ret"]],on="date",how="inner",suffixes=("_donor","_treated")).dropna()
    corr = paired.ret_donor.corr(paired.ret_treated) if len(paired)>1 else None
    tcum = (1+tfit.ret.dropna()).prod()-1 if tfit.ret.notna().any() else None
    rows.append({"treated_ticker":c.treated_ticker,"ticker":c.ticker,"fit_sessions":len(fit),
                 "beta_vs_SPY":beta,"pre_event_fit_adj_return":cum,
                 "median_fit_dollar_volume":fit.dollar_volume.median(),
                 "treated_pair_fit_return_correlation":corr,"treated_pre_event_fit_adj_return":tcum,
                 "status":"price-based descriptive only; donor eligibility not established"})
pd.DataFrame(rows).to_csv(OUT,index=False)

