import numpy as np
import pandas as pd


def drawdown_series(r):
    equity = (1+r).cumprod()
    return equity/equity.cummax().clip(lower=1)-1


def metrics(r):
    total = (1+r).prod()-1
    vol = r.std()*np.sqrt(12)
    return {"months":len(r), "total_return":total, "annualized_return":(1+total)**(12/len(r))-1,
            "annualized_volatility":vol, "sharpe_rf_zero":r.mean()*12/vol if vol>0 else None,
            "max_drawdown_monthly":drawdown_series(r).min()}


def summarize(result):
    stats = {name:metrics(result[name]) for name in ["strategy","SPY"]}
    annual = pd.DataFrame({name:result[name].groupby(result.index.year).apply(lambda x:(1+x).prod()-1) for name in stats})
    annual.index.name = "Year"
    annual["months"] = result.groupby(result.index.year).size()
    return stats, annual
