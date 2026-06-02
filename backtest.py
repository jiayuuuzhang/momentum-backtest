import pandas as pd
from config import N_QUANTILES, LONG_QUANTILE, SHORT_QUANTILE

def compute_monthly_returns(monthly_prices: pd.DataFrame) -> pd.DataFrame:
    """Computes monthly returns from monthly price data."""
    monthly_returns = monthly_prices.pct_change(fill_method=None)
    return monthly_returns

def run_backtest(monthly_returns: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    """Runs the backtest by applying the signals to the monthly returns."""
    months = monthly_returns.index
    results = {}
    for i in range(1, len(months)):
        signal_date = months[i-1]
        return_date = months[i]
        sig = signals.loc[signal_date].dropna()
        ret = monthly_returns.loc[return_date].dropna()
        valid = sig.index.intersection(ret.index)
        if len(valid) < 50:
            continue
        ranks = pd.qcut(sig[valid].rank(method='first'), N_QUANTILES, labels=False) + 1
        long_stocks = ranks[ranks == LONG_QUANTILE].index
        short_stocks = ranks[ranks == SHORT_QUANTILE].index
        long_ret = ret[long_stocks].mean()
        short_ret = ret[short_stocks].mean()
        results[return_date] = (long_ret, short_ret, long_ret - short_ret, len(long_stocks), len(short_stocks))
    return pd.DataFrame.from_dict(results, orient='index', columns=['long', 'short', 'long_short', 'n_long', 'n_short'])