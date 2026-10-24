"""Independently verify saved top/bottom holdings, ranks, costs and returns."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent
report = json.loads((root/'outputs/report.json').read_text())
prices = pd.read_csv(root/'data_cache'/f"prices_{report['warmup_start']}_{report['requested_end']}.csv",index_col=0,parse_dates=True)
p = prices.resample('ME').last().drop(columns='SPY')
returns = p.pct_change(fill_method=None)
h = pd.read_csv(root/'outputs/holdings.csv',parse_dates=['Return_Month','Formation_Date'])
r = pd.read_csv(root/'outputs/monthly_returns.csv',index_col=0,parse_dates=True)
previous = pd.Series(0.,index=p.columns)
checks, contributions = [], []
for date, positions in h.groupby('Return_Month'):
    formation = positions.Formation_Date.iloc[0]
    j = p.index.get_loc(formation)
    # Reconstruct directly from historical prices; do not import strategy code.
    signal = (p.iloc[j-1]/p.iloc[j-12]-1).where(p.iloc[j]>=5).dropna()
    ordered = signal.sort_index().sort_values(kind='stable')
    longs, shorts = positions[positions.Weight>0], positions[positions.Weight<0]
    assert len(longs)==10 and len(shorts)==10 and positions.Ticker.nunique()==20
    assert set(longs.Ticker)==set(ordered.tail(10).index)
    assert set(shorts.Ticker)==set(ordered.head(10).index)
    assert np.allclose(longs.Weight,.1) and np.allclose(shorts.Weight,-.1)
    assert (positions.Formation_Date<date).all()
    weights = pd.Series(0.,index=p.columns)
    weights.loc[longs.Ticker]=.1
    weights.loc[shorts.Ticker]=-.1
    gross = sum(row.Weight*returns.loc[date,row.Ticker] for row in positions.itertuples())
    turnover = (weights-previous).abs().sum()
    cost = turnover*report['cost_bps']/10000
    error = max(abs(gross-r.loc[date,'gross']),abs(cost-r.loc[date,'cost']),abs(gross-cost-r.loc[date,'strategy']))
    assert error < 1e-12
    previous = weights*(1+returns.loc[date].fillna(0))/(1+gross-cost)
    checks.append([date,10,10,weights.abs().sum(),error])
    for row in positions.itertuples():
        contributions.append([date,row.Ticker,row.Weight,returns.loc[date,row.Ticker],row.Weight*returns.loc[date,row.Ticker]])
assert len(checks)==60
assert np.isclose((1+r.strategy).prod()-1,report['metrics']['strategy']['total_return'])
pd.DataFrame(checks,columns=['Date','verified_long_count','verified_short_count','gross_exposure','max_arithmetic_error']).to_csv(root/'outputs/audit_checks.csv',index=False)
pd.DataFrame(contributions,columns=['Date','Ticker','Weight','Stock_Return','Monthly_Return_Contribution']).to_csv(root/'outputs/stock_contributions.csv',index=False)
print('PASS: 60 months; actual historical ranks top 10/bottom 10; weights +/-0.1; costs and net returns independently reproduced.')
print('Scope: verifies saved data and calculations; does not independently verify vendor prices or remove current-universe survivorship bias.')
