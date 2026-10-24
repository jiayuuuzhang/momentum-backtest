"""Fixed top/bottom counts ranked ONLY within effective historical membership."""
import pandas as pd
from signals import compute_momentum_signal
from config import LONG_COUNT, SHORT_COUNT, MIN_PRICE
from data import provider_symbol, REUSED_SYMBOLS


def month_end_prices(daily):
    # Mark all securities on SPY's actual last trading day of each month.
    # Do not carry a delisted/halted stock's earlier quote to month-end.
    benchmark_dates = daily['SPY'].dropna().index.to_series().resample('ME').last().dropna()
    monthly = daily.reindex(pd.DatetimeIndex(benchmark_dates.to_numpy())).copy()
    monthly.index = benchmark_dates.index
    return monthly


def eligible_signals(stocks, signals, formation, membership):
    members, snapshot_date = membership.as_of(formation)
    sig = signals.loc[formation].reindex(sorted(members))
    price = stocks.loc[formation].reindex(sorted(members))
    sig = sig.where(price>=MIN_PRICE).dropna()
    return sig, members, snapshot_date


def membership_diagnostics(daily, membership, dates):
    stocks = month_end_prices(daily).drop(columns='SPY')
    signals = compute_momentum_signal(stocks)
    rows = []
    for formation in dates:
        sig, members, snapshot = eligible_signals(stocks,signals,formation,membership)
        for ticker in sorted(members):
            price = stocks.loc[formation].get(ticker,float('nan'))
            signal = signals.loc[formation].get(ticker,float('nan'))
            reason = 'eligible' if ticker in sig else ('no_formation_price' if pd.isna(price) else ('price_below_minimum' if price<MIN_PRICE else 'missing_lookback_price'))
            identity_note = REUSED_SYMBOLS.get(ticker,'') if pd.isna(price) else ''
            rows.append([formation,snapshot,ticker,daily.attrs.get('price_symbols',{}).get(ticker,provider_symbol(ticker)),price,signal,ticker in sig,reason,identity_note])
    return pd.DataFrame(rows,columns=['Formation_Date','Membership_Snapshot_Date','Ticker','Price_Ticker','Formation_Price','Signal','Eligible','Reason','Identity_Note'])


def run_strategy(daily, start, end, cost_bps=10.0, membership=None):
    if membership is None:
        raise ValueError('Point-in-time membership is required; current-universe fallback is forbidden')
    end_ts = pd.Timestamp(end)
    last_complete = end_ts.to_period('M') if end_ts.is_month_end else end_ts.to_period('M')-1
    monthly = month_end_prices(daily)
    monthly = monthly.loc[monthly.index.to_period('M')<=last_complete]
    stocks = monthly.drop(columns='SPY')
    signals = compute_momentum_signal(stocks)
    returns = stocks.pct_change(fill_method=None)
    benchmark = monthly.SPY.pct_change(fill_method=None)
    previous = pd.Series(0.,index=stocks.columns)
    rows, holdings = [], []
    for i in range(1,len(monthly)):
        date, formation = monthly.index[i], monthly.index[i-1]
        if date<pd.Timestamp(start) or date>end_ts:
            continue
        sig, members, snapshot = eligible_signals(stocks,signals,formation,membership)
        if len(sig)<LONG_COUNT+SHORT_COUNT:
            raise ValueError(f'Only {len(sig)} eligible historical members at {formation.date()}')
        ordered = sig.sort_index().sort_values(kind='stable')
        weights = pd.Series(0.,index=stocks.columns)
        weights.loc[ordered.index[-LONG_COUNT:]] = 1/LONG_COUNT
        weights.loc[ordered.index[:SHORT_COUNT]] = -1/SHORT_COUNT
        active = weights[weights!=0]
        assert set(active.index).issubset(members)
        realized = returns.loc[date,active.index]
        if realized.isna().any():
            raise ValueError(f'Missing held-stock return at {date.date()}: {realized[realized.isna()].index.tolist()}. Supply actual delisting/terminal prices; no silent removal or zero return.')
        turnover = (weights-previous).abs().sum()
        gross = (active*realized).sum()
        fee = turnover*cost_bps/10000
        net = gross-fee
        if net<=-1:
            raise ValueError('Portfolio equity exhausted')
        if pd.isna(benchmark.loc[date]):
            raise ValueError(f'Missing benchmark return: {date}')
        rows.append([date,gross,fee,net,benchmark.loc[date],turnover,LONG_COUNT,SHORT_COUNT,len(members),len(sig)])
        for ticker,weight in active.items():
            holdings.append([date,formation,ticker,weight,float(sig[ticker]),snapshot,daily.attrs.get('price_symbols',{}).get(ticker,provider_symbol(ticker))])
        previous = weights*(1+returns.loc[date].fillna(0))/(1+net)
    if not rows:
        raise ValueError('No backtest months')
    result = pd.DataFrame(rows,columns=['Date','gross','cost','strategy','SPY','turnover','n_long','n_short','n_members','n_eligible']).set_index('Date')
    expected = pd.period_range(pd.Timestamp(start).to_period('M'),last_complete,freq='M')
    if list(result.index.to_period('M'))!=list(expected):
        raise ValueError('Incomplete requested backtest period')
    return result,pd.DataFrame(holdings,columns=['Return_Month','Formation_Date','Ticker','Weight','Signal','Membership_Snapshot_Date','Price_Ticker'])
