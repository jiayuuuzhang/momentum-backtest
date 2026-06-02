import pandas as pd
import numpy as np
import yfinance as yf
import pandas_datareader.data as pdr
import urllib.request, zipfile, io
import requests
from pathlib import Path
from config import (
    DATA_DIR,
    SP500_URL,
    BACKTEST_START_DATE,
    BACKTEST_END_DATE,
    MOMENTUM_WINDOW,
    SKIP_RECENT,
    MIN_HISTORY_MONTHS,
    N_QUANTILES,
    LONG_QUANTILE,
    SHORT_QUANTILE,
    MIN_PRICE,
    BENCHMARK_TICKER,
    ANNUALIZATION_FACTOR,
    ROLLING_SHARPE_WINDOW
)

def get_sp500_tickers() -> list[str]:
    """Fetches the list of S&P 500 tickers from Wikipedia."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(SP500_URL, headers=headers)
    tables = pd.read_html(io.StringIO(response.text))
    sp500_table = tables[0]
    tickers = sp500_table["Symbol"].tolist()
    tickers = [t.replace(".", "-") for t in tickers]
    return tickers

def download_prices(tickers: list[str], start_date: str = BACKTEST_START_DATE, end_date: str = BACKTEST_END_DATE) -> pd.DataFrame:
    """Downloads historical price data for the given tickers and date range."""
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)
    prices = data['Close'].dropna(axis=1, how='all')
    return prices

def resample_monthly(prices: pd.DataFrame) -> pd.DataFrame:
    """Resamples daily price data to monthly frequency, taking the last price of each month."""
    monthly_prices = prices.resample('ME').last()
    return monthly_prices

def filter_penny_stocks(prices: pd.DataFrame, min_price: float = MIN_PRICE) -> pd.DataFrame:
    """Filters out stocks that are below the specified minimum price."""
    return prices[prices >= min_price].dropna(axis=1, how='all')

def download_benchmark(ticker: str = BENCHMARK_TICKER, start_date: str = BACKTEST_START_DATE, end_date: str = BACKTEST_END_DATE) -> pd.Series:
    """Downloads historical price data for the benchmark ticker."""
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    benchmark_prices = data['Close'].squeeze().dropna()
    benchmark_prices = benchmark_prices.resample('ME').last()
    benchmark_returns = benchmark_prices.pct_change().dropna()
    return benchmark_returns

def get_ff_factors(start_date: str = BACKTEST_START_DATE, end_date: str = BACKTEST_END_DATE) -> pd.DataFrame:
    """Downloads Fama-French factors from Kenneth French's data library."""
    ff_factors = pdr.DataReader("F-F_Research_Data_Factors", "famafrench", start=start_date, end=end_date)
    ff_monthly = ff_factors[0]
    ff_monthly.index = ff_monthly.index.to_timestamp(how='end')
    ff_monthly = ff_monthly / 100
    return ff_monthly

def load_all_data() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Loads all necessary data: stock prices, benchmark returns, and Fama-French factors."""
    DATA_DIR.mkdir(exist_ok=True)
    cache_file = DATA_DIR / "prices.parquet"
    if cache_file.exists():
        print("Loading data from cache...")
        prices = pd.read_parquet(cache_file)
    else:
        tickers = get_sp500_tickers()
        prices = download_prices(tickers)
        prices.to_parquet(cache_file)
    monthly_prices = resample_monthly(prices)
    filtered_prices = filter_penny_stocks(monthly_prices)
    benchmark_returns = download_benchmark()
    ff_factors = get_ff_factors()
    return filtered_prices, benchmark_returns, ff_factors