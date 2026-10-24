"""Independent verification of historical membership, rankings and return arithmetic."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=root/'outputs')
args=parser.parse_args(); out=args.output
report=json.loads((out/'report.json').read_text())
raw=pd.read_csv(report['price_cache'],index_col=0,parse_dates=True)
raw.index=pd.to_datetime(raw.index,utc=True).tz_convert(None).normalize()
source_path=Path(report['membership']['file'])
assert hashlib.sha256(source_path.read_bytes()).hexdigest()==report['membership']['sha256']
snapshots=pd.read_csv(source_path,parse_dates=['date'])
aliases=report['ticker_aliases']; rejected=report.get('rejected_reused_symbols',{})
# Independently reconstruct historical labels; don't import selection or data code.
symbols=set()
for entry in snapshots.tickers:
    symbols.update(x.strip().replace('.','-') for x in entry.split(','))
prices={}
for ticker in symbols:
    provider=aliases.get(ticker,ticker)
    if ticker not in rejected and provider in raw:
        prices[ticker]=raw[provider]
mark_dates=raw['SPY'].dropna().index.to_series().resample('ME').last().dropna()
p=pd.DataFrame(prices,index=raw.index).reindex(pd.DatetimeIndex(mark_dates.to_numpy()))
p.index=mark_dates.index
returns=p.pct_change(fill_method=None)
h=pd.read_csv(out/'holdings.csv',parse_dates=['Return_Month','Formation_Date'])
r=pd.read_csv(out/'monthly_returns.csv',index_col=0,parse_dates=True)
previous=pd.Series(0.,index=p.columns)
checks,contributions=[],[]
for date,positions in h.groupby('Return_Month'):
    formation=positions.Formation_Date.iloc[0]
    assert formation<=pd.Timestamp(report['membership']['valid_through'])
    snapshot=snapshots[snapshots.date<=formation].iloc[-1]
    members={x.strip().replace('.','-') for x in snapshot.tickers.split(',')}
    assert set(positions.Ticker)<=members
    assert (positions.Membership_Snapshot_Date==str(snapshot.date.date())).all()
    j=p.index.get_loc(formation)
    signal=(p.iloc[j-1]/p.iloc[j-12]-1).reindex(sorted(members))
    signal=signal.where(p.iloc[j].reindex(signal.index)>=5).dropna()
    ordered=signal.sort_index().sort_values(kind='stable')
    longs,shorts=positions[positions.Weight>0],positions[positions.Weight<0]
    assert len(longs)==10 and len(shorts)==10 and positions.Ticker.nunique()==20
    assert set(longs.Ticker)==set(ordered.tail(10).index)
    assert set(shorts.Ticker)==set(ordered.head(10).index)
    assert np.allclose(longs.Weight,.1) and np.allclose(shorts.Weight,-.1)
    assert (positions.Formation_Date<date).all()
    assert not set(positions.Ticker)&set(rejected)
    weights=pd.Series(0.,index=p.columns)
    weights.loc[longs.Ticker]=.1; weights.loc[shorts.Ticker]=-.1
    gross=sum(row.Weight*returns.loc[date,row.Ticker] for row in positions.itertuples())
    cost=(weights-previous).abs().sum()*report['cost_bps']/10000
    error=max(abs(gross-r.loc[date,'gross']),abs(cost-r.loc[date,'cost']),abs(gross-cost-r.loc[date,'strategy']))
    assert error<1e-12
    previous=weights*(1+returns.loc[date].fillna(0))/(1+gross-cost)
    checks.append([date,formation,snapshot.date,len(members),len(signal),10,10,True,weights.abs().sum(),error])
    for row in positions.itertuples():
        contributions.append([date,row.Ticker,row.Weight,returns.loc[date,row.Ticker],row.Weight*returns.loc[date,row.Ticker]])
assert len(checks)==report['metrics']['strategy']['months']==len(r)
assert np.isclose((1+r.strategy).prod()-1,report['metrics']['strategy']['total_return'])
# Explicit regressions for the former pre-inclusion look-ahead examples.
for ticker,join in {'APP':'2025-09-22','CVNA':'2025-12-22','SMCI':'2024-03-18','PLTR':'2024-09-23','BE':'2026-09-21','COIN':'2025-05-19'}.items():
    assert not ((h.Ticker==ticker)&(h.Formation_Date<pd.Timestamp(join))).any(),ticker
pd.DataFrame(checks,columns=['Date','Formation_Date','Membership_Snapshot_Date','Historical_Members','Eligible_With_Data','verified_long_count','verified_short_count','all_holdings_were_members','gross_exposure','max_arithmetic_error']).to_csv(out/'audit_checks.csv',index=False)
pd.DataFrame(contributions,columns=['Date','Ticker','Weight','Stock_Return','Monthly_Return_Contribution']).to_csv(out/'stock_contributions.csv',index=False)
print(f'PASS: {len(checks)} months; every holding is a historical member; exact top/bottom 10; costs and returns independently reproduced.')
print('Caveat: missing historical prices remain a documented coverage limitation; this is not a complete delisting-return database.')
