"""Download the union of historical members, including former constituents."""
import hashlib
import json
import warnings
from pathlib import Path
import pandas as pd
import yfinance as yf
from config import DATA_DIR
from membership import formation_dates

if hasattr(pd.errors, 'Pandas4Warning'):
    warnings.filterwarnings('ignore', category=pd.errors.Pandas4Warning, module=r'yfinance\..*')

# Provider labels for the SAME company's renamed shares, not successor/acquirer
# proxies. Membership always uses the historical ticker before applying this map.
# Dates/reasons are documented in data_cache/membership/ticker_aliases.csv.
ALIASES = {'ABC':'COR', 'ANTM':'ELV', 'BK':'BNY', 'BLL':'BALL',
           'CDAY':'DAY', 'FB':'META', 'FI':'FISV', 'FLT':'CPAY',
           'GPS':'GAP', 'MMC':'MRSH', 'NLOK':'GEN', 'PKI':'RVTY',
           'RE':'EG', 'WLTW':'WTW', 'FBHS':'FBIN', 'FRC':'FRCB'}

REUSED_SYMBOLS = {'INFO':'Yahoo now resolves to Harbor PanAgora ETF, not historical IHS Markit',
                  'PARA':'Yahoo now resolves to Banzai/Parabolic, not historical Paramount Global'}


def provider_symbol(ticker):
    return ALIASES.get(ticker, ticker)


def load_prices(start, end, membership, csv=None, refresh=False):
    warmup = (pd.Timestamp(start)-pd.DateOffset(months=15)).strftime('%Y-%m-%d')
    historical = membership.union(formation_dates(start,end))
    providers = sorted(set(map(provider_symbol,historical)) | {'SPY'})
    DATA_DIR.mkdir(exist_ok=True)
    key = hashlib.sha256(','.join(providers).encode()).hexdigest()[:12]
    cache = DATA_DIR/f'prices_pit_{warmup}_{end}_{key}.csv'
    source = 'Yahoo Finance; auto_adjust=True; historical-member union'
    if csv:
        frame = pd.read_csv(csv,index_col=0,parse_dates=True)
        source = str(Path(csv).resolve())
        cache = Path(csv)
    elif cache.exists() and not refresh:
        frame = pd.read_csv(cache,index_col=0,parse_dates=True)
    else:
        frame = pd.DataFrame()
        # Reuse genuine adjusted prices from the preceding run; membership is
        # reconstructed independently and the historical union is still fetched.
        old_cache = DATA_DIR/f'prices_{warmup}_{end}.csv'
        if old_cache.exists() and not refresh:
            old = pd.read_csv(old_cache,index_col=0,parse_dates=True)
            available = [x for x in providers if x in old and old[x].notna().any()]
            frame = old[available].copy()
        missing = [x for x in providers if x not in frame or frame[x].dropna().empty]
        for offset in range(0,len(missing),30):
            batch = missing[offset:offset+30]
            print(f'Downloading historical symbols {offset+1}-{min(offset+30,len(missing))}/{len(missing)}',flush=True)
            raw = yf.download(batch,start=warmup,end=(pd.Timestamp(end)+pd.Timedelta(days=1)).strftime('%Y-%m-%d'),auto_adjust=True,progress=False,threads=4)
            if not raw.empty:
                closes = raw['Close']
                if isinstance(closes,pd.Series):
                    closes = closes.to_frame(batch[0])
                frame = pd.concat([frame,closes],axis=1)
        frame = frame.reindex(columns=providers)
        frame.to_csv(cache)
    frame.index = pd.to_datetime(frame.index,utc=True).tz_convert(None).normalize()
    frame = frame.sort_index().loc[warmup:end].apply(pd.to_numeric,errors='raise')
    if frame.index.has_duplicates or frame.columns.has_duplicates:
        raise ValueError('Duplicate price dates or tickers')
    if 'SPY' not in frame or frame.SPY.dropna().empty:
        raise ValueError('SPY benchmark missing')
    if (frame<=0).any().any():
        raise ValueError('Nonpositive adjusted prices')
    if not csv:
        for ticker in REUSED_SYMBOLS:
            if ticker in frame:
                frame[ticker] = float('nan')
    # Historical symbols remain distinct membership identities, even where a
    # provider serves an old ticker's series under a later rename.
    resolved = {t:(t if csv and t in frame else provider_symbol(t)) for t in historical}
    prices = pd.DataFrame({t:frame[resolved[t]] if resolved[t] in frame else float('nan') for t in historical},index=frame.index)
    prices.attrs['price_symbols'] = resolved
    prices['SPY'] = frame.SPY
    coverage = pd.DataFrame([{'Ticker':t,'Price_Ticker':resolved[t],'observations':int(prices[t].notna().sum()),
                             'first_price':str(prices[t].first_valid_index().date()) if prices[t].notna().any() else None,
                             'last_price':str(prices[t].last_valid_index().date()) if prices[t].notna().any() else None} for t in historical])
    metadata = {'source':source,'price_cache':str(cache.resolve()),'warmup_start':warmup,
                'requested_stock_count':len(historical),'stocks_without_prices':coverage.loc[coverage.observations==0,'Ticker'].tolist(),
                'universe':'point-in-time historical S&P 500 membership; available-price subset',
                'membership':membership.metadata,'ticker_aliases':resolved,
                'rejected_reused_symbols':REUSED_SYMBOLS if not csv else {},
                'limitations':['Community reconstructed membership, not a licensed official full security master.',
                               'Historical member prices unavailable from Yahoo are explicitly reported, not replaced by surviving companies.',
                               'No inferred delisting returns. Missing held-stock returns stop the backtest.',
                               'Borrow availability, borrow fees and financing are not modelled.']}
    return prices, metadata, coverage
