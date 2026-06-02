import pandas as pd
from config import MOMENTUM_WINDOW, SKIP_RECENT

def compute_momentum_signal(monthly_prices: pd.DataFrame) -> pd.DataFrame:
    signal = (monthly_prices.shift(SKIP_RECENT) / monthly_prices.shift(MOMENTUM_WINDOW)) - 1
    return signal