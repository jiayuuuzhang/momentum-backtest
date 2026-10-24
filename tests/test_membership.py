import unittest
import numpy as np
import pandas as pd
from membership import MembershipHistory
from backtest import run_strategy

class MembershipTests(unittest.TestCase):
    def test_effective_dates_removal_and_reentry(self):
        history=MembershipHistory(pd.DataFrame({'date':['2021-01-01','2021-06-15','2021-12-01'],'tickers':['A,B','B,C','A,C']}),'2022-01-31')
        self.assertEqual(history.as_of('2021-06-14')[0],{'A','B'})
        self.assertEqual(history.as_of('2021-06-15')[0],{'B','C'})
        self.assertEqual(history.as_of('2021-12-01')[0],{'A','C'})
        with self.assertRaises(ValueError): history.as_of('2020-12-31')
        with self.assertRaises(ValueError): history.as_of('2022-02-01')

    def test_highest_future_joiner_excluded_and_later_removed_included(self):
        dates=pd.date_range('2019-01-01','2022-12-31',freq='B')
        stocks={f'S{i:02}':100*np.exp(np.arange(len(dates))*(i-15)/100000) for i in range(30)}
        stocks['FUTURE']=100*np.exp(np.arange(len(dates))*.002)
        stocks['SPY']=100*np.exp(np.arange(len(dates))*.0001)
        prices=pd.DataFrame(stocks,index=dates)
        base=','.join(f'S{i:02}' for i in range(30))
        history=MembershipHistory(pd.DataFrame({'date':['2019-01-01','2021-06-01','2022-01-01'],
            'tickers':[base,base+',FUTURE',','.join(f'S{i:02}' for i in range(1,30))+',FUTURE']}),'2022-12-31')
        result,holdings=run_strategy(prices,'2021-01-01','2022-12-31',membership=history)
        self.assertFalse(((holdings.Ticker=='FUTURE')&(holdings.Formation_Date<'2021-06-01')).any())
        self.assertTrue(((holdings.Ticker=='FUTURE')&(holdings.Formation_Date>='2021-06-01')).any())
        self.assertTrue(((holdings.Ticker=='S00')&(holdings.Formation_Date<'2022-01-01')).any())
        self.assertFalse(((holdings.Ticker=='S00')&(holdings.Formation_Date>='2022-01-01')).any())

    def test_membership_mandatory(self):
        with self.assertRaisesRegex(ValueError,'membership is required'):
            run_strategy(pd.DataFrame(),'2021-01-01','2021-12-31')

class RealMembershipRegressionTests(unittest.TestCase):
    def test_source_late_joiners_and_removed_names(self):
        from membership import load_membership
        from config import DATA_DIR
        if not (DATA_DIR/'membership/snapshots.csv').exists():
            self.skipTest('Bundled historical dataset not installed in this staging directory')
        history=load_membership()
        before,_=history.as_of('2024-02-29')
        for ticker in ['APP','CVNA','SMCI','PLTR','BE','COIN']:
            self.assertNotIn(ticker,before)
        self.assertIn('SMCI',history.as_of('2024-03-18')[0])
        self.assertNotIn('BE',history.as_of('2026-08-31')[0])
        self.assertIn('BE',history.as_of('2026-09-21')[0])
        self.assertIn('FRC',history.as_of('2023-04-30')[0])
        self.assertNotIn('FRC',history.as_of('2023-05-04')[0])
        self.assertIn('AAL',history.as_of('2021-09-30')[0])
        self.assertNotIn('AAL',history.as_of('2024-09-23')[0])

    def test_reused_price_tickers_rejected(self):
        from data import REUSED_SYMBOLS,provider_symbol
        self.assertIn('PARA',REUSED_SYMBOLS)
        self.assertIn('INFO',REUSED_SYMBOLS)
        self.assertEqual(provider_symbol('FRC'),'FRCB')
        self.assertEqual(provider_symbol('FB'),'META')


class MonthEndMarkTests(unittest.TestCase):
    def test_early_delisting_quote_is_not_carried_to_month_end(self):
        from backtest import month_end_prices
        daily=pd.DataFrame({'SPY':[100,101,102],'OLD':[50,51,np.nan]},
            index=pd.to_datetime(['2021-01-27','2021-01-28','2021-01-29']))
        monthly=month_end_prices(daily)
        self.assertTrue(pd.isna(monthly.loc['2021-01-31','OLD']))
        self.assertEqual(monthly.loc['2021-01-31','SPY'],102)
