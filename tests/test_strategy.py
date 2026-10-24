import unittest
import numpy as np
import pandas as pd
from analytics import drawdown_series
from backtest import run_strategy
from membership import MembershipHistory

def synthetic_membership():
    return MembershipHistory(pd.DataFrame({'date':['2019-01-01'],'tickers':[','.join(f'S{i:02}' for i in range(60))]}),'2023-12-31')


def run_test_strategy(*args, **kwargs):
    return run_strategy(*args, membership=synthetic_membership(), **kwargs)


class StrategyTests(unittest.TestCase):
    def prices(self):
        dates = pd.date_range('2019-09-01','2022-12-31',freq='B')
        return pd.DataFrame({**{f'S{i:02}':100*np.exp(np.arange(len(dates))*(i-25)/100000) for i in range(60)},'SPY':100*np.exp(np.arange(len(dates))*.0001)},index=dates)

    def test_initial_loss_drawdown(self):
        self.assertAlmostEqual(drawdown_series(pd.Series([-.1,.05])).min(),-.1)

    def test_complete_period_and_cost(self):
        result, holdings = run_test_strategy(self.prices(),'2021-01-01','2022-12-31')
        self.assertEqual(len(result),24)
        self.assertAlmostEqual(result.cost.iloc[0],.002)
        self.assertTrue((holdings.Formation_Date < holdings.Return_Month).all())

    def test_exact_ten_each_side(self):
        result, holdings = run_test_strategy(self.prices(),'2021-01-01','2022-12-31')
        self.assertTrue((result.n_long == 10).all())
        self.assertTrue((result.n_short == 10).all())
        for _, positions in holdings.groupby('Return_Month'):
            self.assertEqual(set(positions.Ticker[positions.Weight > 0]), {f'S{i:02}' for i in range(50,60)})
            self.assertEqual(set(positions.Ticker[positions.Weight < 0]), {f'S{i:02}' for i in range(10)})
            self.assertTrue(np.allclose(positions.Weight.abs(), .1))

    def test_future_returns_do_not_select_positions(self):
        prices = self.prices()
        _, before = run_test_strategy(prices,'2021-01-01','2022-12-31')
        prices.loc['2021-01-01':,'S59'] *= .5
        _, after = run_test_strategy(prices,'2021-01-01','2022-12-31')
        pd.testing.assert_frame_equal(before[before.Return_Month=='2021-01-31'].reset_index(drop=True),after[after.Return_Month=='2021-01-31'].reset_index(drop=True))

    def test_missing_held_return_fails(self):
        prices = self.prices()
        prices.loc['2021-01-01':'2021-01-31','S59'] = np.nan
        with self.assertRaisesRegex(ValueError,'Missing held-stock'):
            run_test_strategy(prices,'2021-01-01','2022-12-31')

if __name__ == '__main__':
    unittest.main()
