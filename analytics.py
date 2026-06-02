import pandas as pd
import numpy as np
import statsmodels.api as sm
from config import ROLLING_SHARPE_WINDOW


def annualized_return(monthly_returns):
    total = (1 + monthly_returns).prod()
    n_years = len(monthly_returns) / 12
    return total ** (1/n_years) - 1

def annualized_volatility(monthly_returns):
    monthly_vol = monthly_returns.std()
    annual_vol = monthly_vol * np.sqrt(12)
    return annual_vol

def sharpe_ratio(monthly_returns, rf_monthly=None):
    if rf_monthly is not None:
        excess_returns = monthly_returns - rf_monthly
    else:
        excess_returns = monthly_returns
        
    mean = excess_returns.mean()
    std = excess_returns.std()
    result = mean / std * np.sqrt(12)
    return result

def max_drawdown(monthly_returns):
    cumulative = (1 + monthly_returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    return drawdown.min()

def drawdown_series(monthly_returns):
    cumulative = (1 + monthly_returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    return drawdown

def rolling_sharpe(monthly_returns, window=ROLLING_SHARPE_WINDOW):
    rolling_window = monthly_returns.rolling(window)
    rolling_mean = rolling_window.mean()
    rolling_std = rolling_window.std()
    rolling_sharpe = rolling_mean / rolling_std * np.sqrt(12)
    return rolling_sharpe

def ff_regression(strategy_returns, ff_factors):
    strategy_returns = strategy_returns.copy()
    strategy_returns.name = 'strategy'
    strategy_returns.index = strategy_returns.index.to_period('M')
    ff_factors = ff_factors.copy()
    ff_factors.index = ff_factors.index.to_period('M')
    merged = pd.concat([strategy_returns, ff_factors], axis=1, join='inner').dropna()
    y = merged['strategy'] - merged['RF']
    X = merged[['Mkt-RF', 'SMB', 'HML']]
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    return model


def summary_statistics(backtest_results, benchmark_returns):
    ls = backtest_results['long_short']
    stats = {
        'strategy_annual_return': annualized_return(ls),
        'strategy_annual_vol': annualized_volatility(ls),
        'strategy_sharpe': sharpe_ratio(ls),
        'strategy_max_dd': max_drawdown(ls),
        'benchmark_annual_return': annualized_return(benchmark_returns),
        'benchmark_annual_vol': annualized_volatility(benchmark_returns),
        'benchmark_sharpe': sharpe_ratio(benchmark_returns),
        'benchmark_max_dd': max_drawdown(benchmark_returns),
    }
    return stats


