"""Calculate price-based pre-event screening statistics from the saved Yahoo panel."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "raw" / "week3_yahoo"
OUT = ROOT / "data" / "processed" / "week3_price_screening_metrics.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

cand = pd.read_csv(DATA / "candidate_prices_exploratory.csv", parse_dates=["date"])
spy = pd.read_csv(DATA / "spy_market_prices.csv", parse_dates=["date"])
coverage = pd.read_csv(DATA / "candidate_price_coverage.csv")
rows = []
for _, c in coverage.iterrows():
    sub = cand[(cand.treated_ticker == c.treated_ticker) & (cand.ticker == c.ticker)].sort_values("date")
    if sub.empty:
        rows.append({"treated_ticker":c.treated_ticker,"ticker":c.ticker,"fit_sessions":0,
                     "beta_vs_SPY":None,"pre_event_fit_adj_return":None,"median_fit_dollar_volume":None,
                     "status":"not calculable: no candidate price rows"})
        continue
    event = pd.Timestamp(c.event_day_zero)
    event_dates = sorted(pd.to_datetime(sub.date.unique()))
    if event not in event_dates:
        rows.append({"treated_ticker":c.treated_ticker,"ticker":c.ticker,"fit_sessions":0,
                     "beta_vs_SPY":None,"pre_event_fit_adj_return":None,"median_fit_dollar_volume":None,
                     "status":"not calculable: event date absent"})
        continue
    eidx = event_dates.index(event)
    fit_dates = set(event_dates[max(0,eidx-252):max(0,eidx-20)])
    fit = sub[sub.date.isin(fit_dates)].copy()
    market = spy[spy.window_start.eq(c.window_start)].copy()
    market["date"] = pd.to_datetime(market.date)
    fit["ret"] = pd.to_numeric(fit.adj_close,errors="coerce").pct_change()
    fit["dollar_volume"] = pd.to_numeric(fit.close_raw,errors="coerce") * pd.to_numeric(fit.volume_raw,errors="coerce")
    market["mret"] = pd.to_numeric(market.adj_close,errors="coerce").pct_change()
    joined = fit.merge(market[["date","mret"]],on="date",how="inner").dropna(subset=["ret","mret"])
    beta = joined.ret.cov(joined.mret) / joined.mret.var() if len(joined)>1 and joined.mret.var() else None
    cum = (1+fit.ret.dropna()).prod()-1 if fit.ret.notna().any() else None
    rows.append({"treated_ticker":c.treated_ticker,"ticker":c.ticker,"fit_sessions":len(fit),
                 "beta_vs_SPY":beta,"pre_event_fit_adj_return":cum,
                 "median_fit_dollar_volume":fit.dollar_volume.median(),
                 "status":"price-based descriptive only; donor eligibility not established"})
pd.DataFrame(rows).to_csv(OUT,index=False)

