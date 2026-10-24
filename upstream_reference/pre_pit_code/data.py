"""Adjusted market prices with reproducible caches and CSV override."""
import io
import warnings
import json
import pandas as pd
import requests
import yfinance as yf
# Upstream yfinance uses deprecated pandas inplace APIs.
if hasattr(pd.errors, "Pandas4Warning"):
    warnings.filterwarnings("ignore", category=pd.errors.Pandas4Warning, module=r"yfinance\..*")
from config import DATA_DIR


def get_sp500_tickers():
    DATA_DIR.mkdir(exist_ok=True)
    cache = DATA_DIR / "universe.csv"
    if cache.exists():
        return pd.read_csv(cache)["Symbol"].tolist()
    response = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
    response.raise_for_status()
    table = pd.read_html(io.StringIO(response.text))[0]
    table["Symbol"] = table["Symbol"].str.replace(".", "-", regex=False)
    table.to_csv(cache, index=False)
    return table["Symbol"].tolist()


def load_prices(start, end, csv=None, refresh=False):
    warmup = (pd.Timestamp(start) - pd.DateOffset(months=15)).strftime("%Y-%m-%d")
    if csv:
        frame = pd.read_csv(csv, index_col=0, parse_dates=True)
        source = str(csv)
    else:
        DATA_DIR.mkdir(exist_ok=True)
        cache = DATA_DIR / f"prices_{warmup}_{end}.csv"
        source = "Yahoo Finance; auto_adjust=True"
        if cache.exists() and not refresh:
            frame = pd.read_csv(cache, index_col=0, parse_dates=True)
        else:
            tickers = sorted(set(get_sp500_tickers() + ["SPY"]))
            chunks = []
            for offset in range(0, len(tickers), 50):
                batch = tickers[offset:offset+50]
                print(f"Downloading {offset+1}-{min(offset+50,len(tickers))}/{len(tickers)}", flush=True)
                raw = yf.download(batch, start=warmup, end=(pd.Timestamp(end)+pd.Timedelta(days=1)).strftime("%Y-%m-%d"), auto_adjust=True, progress=False, threads=4)
                if not raw.empty:
                    chunks.append(raw["Close"])
            if not chunks:
                raise ValueError("No prices downloaded. Supply --prices-csv with adjusted close prices.")
            frame = pd.concat(chunks, axis=1).dropna(axis=1, how="all")
            frame.to_csv(cache)
    frame.index = pd.to_datetime(frame.index, utc=True).tz_convert(None).normalize()
    frame = frame.sort_index()
    if frame.index.has_duplicates or frame.columns.has_duplicates:
        raise ValueError("Duplicate price dates or tickers")
    if "SPY" not in frame or frame["SPY"].dropna().empty:
        raise ValueError("Price file must contain SPY benchmark")
    frame = frame.loc[warmup:end].apply(pd.to_numeric, errors="raise")
    if (frame <= 0).any().any():
        raise ValueError("Prices must be positive")
    coverage = frame.notna().sum().rename("observations")
    expected = get_sp500_tickers() if not csv else list(frame.drop(columns="SPY").columns)
    missing = sorted(set(expected) - set(frame.dropna(axis=1, how="all").columns))
    return frame, {"source": source, "warmup_start": warmup, "requested_stock_count": len(expected), "stocks_without_prices": missing}, coverage
