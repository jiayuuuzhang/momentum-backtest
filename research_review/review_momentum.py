from pathlib import Path
import json
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parents[1]
review_dir=Path(__file__).resolve().parent
report=json.loads((root/'outputs/report.json').read_text())
r=pd.read_csv(root/'outputs/monthly_returns.csv',index_col=0,parse_dates=True)
h=pd.read_csv(root/'outputs/holdings.csv',parse_dates=['Return_Month','Formation_Date'])
c=pd.read_csv(root/'outputs/stock_contributions.csv',parse_dates=['Date'])
d=pd.read_csv(root/'outputs/membership_audit.csv',parse_dates=['Formation_Date'])
raw=pd.read_csv(report['price_cache'],index_col=0,parse_dates=True)
raw.index=pd.to_datetime(raw.index,utc=True).tz_convert(None).normalize()

def summary(x):
    total=float((1+x).prod()-1)
    return {'months':len(x),'total_return':total,'cagr':float((1+total)**(12/len(x))-1),'vol':float(x.std()*np.sqrt(12)),'sharpe0':float(x.mean()/x.std()*np.sqrt(12))}
result={'baseline':summary(r.strategy),'pre_2026':summary(r.loc[:'2025-12-31','strategy']),
        '2026':summary(r.loc['2026-01-01':,'strategy']),
        'coverage_reason_counts':d.Reason.value_counts().to_dict(),
        'coverage_per_month':d.groupby('Formation_Date').Eligible.agg(['sum','count']).describe().to_dict(),
        'turnover_mean_monthly':float(r.turnover.mean()),'cost_sum_monthly':float(r.cost.sum()),
        'top_months':r.strategy.nlargest(5).rename('return').reset_index().astype({'Date':str}).to_dict('records'),
        'bottom_months':r.strategy.nsmallest(5).rename('return').reset_index().astype({'Date':str}).to_dict('records')}
for n in [1,3,5]:
    changed=r.strategy.copy();changed.loc[changed.nlargest(n).index]=0
    result[f'top_{n}_months_set_zero_total']=float((1+changed).prod()-1)
result['hypothetical_borrow_fee_sensitivity']={str(rate):summary(r.strategy-rate/12) for rate in [.01,.03,.05,.10]}
result['cash_funded_half_exposure']=summary(r.strategy*.5)
result['zero_rf_mean_t_stat_iid']=float(r.strategy.mean()/(r.strategy.std()/np.sqrt(len(r))))
# Rebuild daily mark-to-market from saved fixed monthly holdings; no daily rebalancing.
# Keep missing observations missing, never fill a delisted security to fabricate marks.
equity=1.;daily_records=[]; month_end_error=[];prev_actual=None;rename_events=[]
weights_previous={}
for month,pos in h.groupby('Return_Month'):
    formation=pos.Formation_Date.iloc[0]
    startdate=raw.SPY.dropna().loc[:formation].index[-1]
    dates=raw.SPY.dropna().loc[(raw.index>startdate)&(raw.index<=month)].index
    providers=pos.Price_Ticker.tolist();weights=pos.Weight.to_numpy()
    mark=raw.loc[dates,providers].copy();mark.columns=pos.Ticker.tolist()
    startprices=raw.loc[startdate,providers].to_numpy()
    rel=mark.to_numpy()/startprices
    good=np.isfinite(rel).all(axis=1)
    for date,g,row in zip(dates,good,rel):
        if not g:
            daily_records.append([date,np.nan,np.nan,False]);continue
        local=1-r.loc[month,'cost']+float(np.sum(weights*(row-1)))
        risky=np.sum(np.abs(weights*row))/local if local>0 else float('inf')
        daily_records.append([date,equity*local,risky,True])
    final_local=1-r.loc[month,'cost']+float(np.sum(weights*(rel[-1]-1)))
    month_end_error.append(abs(final_local-(1+r.loc[month,'strategy'])))
    equity*=1+r.loc[month,'strategy']
# Benchmark trade-day-based daily marks.
marked=pd.DataFrame(daily_records,columns=['Date','Equity','Gross_Exposure','Complete']).set_index('Date')
valid=marked.Equity.dropna(); draw=valid/valid.cummax().clip(lower=1)-1
result['daily_mark_check']={'valid_days':len(valid),'missing_days':int((~marked.Complete).sum()),'max_drawdown':float(draw.min()),
 'max_drawdown_date':str(draw.idxmin().date()),'max_gross_exposure_between_rebalances':float(marked.Gross_Exposure.max()),
 'maximum_month_end_reconciliation_error':float(max(month_end_error))}
# Aliases held across a rename: same provider appears as two separate security columns.
for j in range(1,len(r)):
    oldmonth=r.index[j-1]; newmonth=r.index[j]
    old=h[h.Return_Month==oldmonth]; new=h[h.Return_Month==newmonth]
    byprovider={row.Price_Ticker:row for row in old.itertuples()}
    for row in new.itertuples():
        if row.Price_Ticker in byprovider:
            before=byprovider[row.Price_Ticker]
            if before.Ticker!=row.Ticker:
                rename_events.append({'month':str(newmonth.date()),'old':before.Ticker,'new':row.Ticker,'provider':row.Price_Ticker,'before_weight':before.Weight,'after_weight':row.Weight})
result['rename_double_trades']=rename_events
# Contribution diagnostics; arithmetic monthly contributions, not compounded capital P&L.
result['largest_stock_month_contributions']=c.nlargest(12,'Monthly_Return_Contribution').astype({'Date':str}).to_dict('records')
result['largest_2026_contribution_sums']=c[c.Date>='2026-01-01'].groupby('Ticker').Monthly_Return_Contribution.sum().nlargest(12).to_dict()
result['long_short_monthly_sums']=c.groupby(c.Weight>0).Monthly_Return_Contribution.sum().to_dict()
# Beta / HAC 3-lag alpha approximation, monthly data, zero rf used only to inspect exposures.
y=r.strategy.to_numpy(); x=np.column_stack([np.ones(len(r)),r.SPY.to_numpy()]);coef=np.linalg.lstsq(x,y,rcond=None)[0];e=y-x@coef
bread=np.linalg.inv(x.T@x);z=x*e[:,None];meat=z.T@z
for lag in range(1,4):
 g=z[lag:].T@z[:-lag];meat+=(1-lag/4)*(g+g.T)
cov=bread@meat@bread*(len(r)/(len(r)-2));se=np.sqrt(np.diag(cov))
result['single_factor_diagnostic']={'monthly_intercept_rf0':float(coef[0]),'market_beta':float(coef[1]),'alpha_t_hac3':float(coef[0]/se[0]),'r_squared':float(1-e@e/np.sum((y-y.mean())**2))}
marked.to_csv(review_dir/'daily_marks.csv')
(review_dir/'evidence.json').write_text(json.dumps(result,indent=2,default=str))
print(json.dumps(result,indent=2,default=str))
