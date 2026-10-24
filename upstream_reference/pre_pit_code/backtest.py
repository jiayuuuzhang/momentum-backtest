"""Monthly 12-1 momentum; positions selected using formation-time data only."""
import pandas as pd
from signals import compute_momentum_signal
from config import LONG_COUNT, SHORT_COUNT, MIN_PRICE


def run_strategy(daily, start, end, cost_bps=10.0):
    # Drop unfinished calendar months, including when end falls mid-month.
    end_ts = pd.Timestamp(end)
    last_complete = end_ts.to_period("M") if end_ts.is_month_end else end_ts.to_period("M")-1
    monthly = daily.resample("ME").last()
    monthly = monthly.loc[monthly.index.to_period("M") <= last_complete]
    stocks = monthly.drop(columns="SPY")
    signals = compute_momentum_signal(stocks)
    returns = stocks.pct_change(fill_method=None)
    benchmark = monthly["SPY"].pct_change(fill_method=None)
    previous = pd.Series(0.0, index=stocks.columns)
    rows, holdings = [], []
    for i in range(1, len(monthly)):
        date, formation = monthly.index[i], monthly.index[i-1]
        if date < pd.Timestamp(start) or date > end_ts:
            continue
        sig = signals.loc[formation].where(stocks.loc[formation] >= MIN_PRICE).dropna()
        if len(sig) < LONG_COUNT + SHORT_COUNT:
            raise ValueError(f"Only {len(sig)} eligible stocks at {formation.date()}; need >={LONG_COUNT + SHORT_COUNT} and warmup history")
        ordered = sig.sort_index().sort_values(kind="stable")
        weights = pd.Series(0.0, index=stocks.columns)
        weights.loc[ordered.index[-LONG_COUNT:]] = 1/LONG_COUNT
        weights.loc[ordered.index[:SHORT_COUNT]] = -1/SHORT_COUNT
        active = weights[weights != 0]
        realized = returns.loc[date, active.index]
        if realized.isna().any():
            raise ValueError(f"Missing held-stock return at {date.date()}: {realized[realized.isna()].index.tolist()}. Supply complete/delisting data; no silent survivor filtering.")
        turnover = (weights-previous).abs().sum()
        gross = (active*realized).sum()
        fee = turnover*cost_bps/10000
        net = gross-fee
        if net <= -1:
            raise ValueError("Portfolio equity exhausted")
        if pd.isna(benchmark.loc[date]):
            raise ValueError(f"Missing benchmark return: {date}")
        rows.append([date, gross, fee, net, benchmark.loc[date], turnover, LONG_COUNT, SHORT_COUNT])
        for ticker, weight in active.items():
            holdings.append([date, formation, ticker, weight, float(sig[ticker])])
        # Drifted risky weights after the holding period; residual capital is cash.
        previous = weights*(1+returns.loc[date].fillna(0))/(1+net)
    if not rows:
        raise ValueError("No backtest months; check requested dates and warmup data")
    result = pd.DataFrame(rows, columns=["Date","gross","cost","strategy","SPY","turnover","n_long","n_short"]).set_index("Date")
    expected = pd.period_range(pd.Timestamp(start).to_period("M"), last_complete, freq="M")
    if list(result.index.to_period("M")) != list(expected):
        raise ValueError("Incomplete requested backtest period")
    return result, pd.DataFrame(holdings, columns=["Return_Month","Formation_Date","Ticker","Weight","Signal"])
