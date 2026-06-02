# Momentum Factor Backtest

A cross-sectional momentum strategy backtest on the S&P 500, with Fama-French 3-factor attribution and a performance tearsheet comparing against SPY.

## Strategy

- **Universe:** S&P 500 (current constituents, scraped from Wikipedia)
- **Signal:** 12-minus-1 month trailing return — cumulative return from t-12 to t-1, skipping the most recent month to avoid short-term reversal
- **Construction:** Monthly cross-sectional ranking into 10 deciles
  - Long: top decile (best 12-1 momentum), equal-weighted
  - Short: bottom decile (worst 12-1 momentum), equal-weighted
- **Rebalancing:** End of each month
- **Filter:** Stocks priced below $5 excluded (penny stock filter)
- **Date range:** 2005-01-01 to 2025-12-31

## Project Structure

```
Backtest/
├── requirements.txt    # Dependencies
├── config.py           # All tunable parameters
├── data.py             # Data pipeline (tickers, prices, FF factors, cache)
├── signals.py          # 12-1 momentum signal
├── backtest.py         # Portfolio construction + backtest loop
├── analytics.py        # Performance metrics + FF regression
├── tearsheet.py        # 4-panel visualization
├── main.py             # Entry point
└── data_cache/         # Parquet cache (auto-created)
```

## Installation

```powershell
pip install -r requirements.txt
```

## Usage

```powershell
python main.py
```

First run downloads ~500 tickers from yfinance and caches them as Parquet. Subsequent runs load from cache in seconds.

Output:
- `tearsheet.png` — 4-panel performance summary
- Fama-French regression summary printed to console

## Tearsheet Panels

| Panel | Content |
|-------|---------|
| Top-left | Cumulative returns: strategy vs SPY (log scale) |
| Top-right | Strategy drawdown (filled area) |
| Bottom-left | Rolling 36-month Sharpe ratio |
| Bottom-right | Summary stats + Fama-French factor coefficients |

## Performance Metrics

- **Annualized Return** — Geometric, compounded from monthly returns
- **Annualized Volatility** — Monthly std × √12
- **Sharpe Ratio** — Mean / std × √12 (no risk-free adjustment by default)
- **Max Drawdown** — Worst peak-to-trough decline in cumulative returns

## Fama-French 3-Factor Regression

Model:
```
R_strategy - R_f = alpha + beta_mkt(Mkt-RF) + beta_smb(SMB) + beta_hml(HML) + epsilon
```

Decomposes strategy returns into:
- **Alpha** — Return unexplained by the three factors (the "true" momentum premium)
- **Mkt-RF beta** — Market exposure
- **SMB beta** — Small-cap tilt
- **HML beta** — Value tilt (negative is expected for momentum, since it tilts toward growth/winners)

Factor data is fetched from Ken French's data library via `pandas_datareader`.

## Known Limitations

### Survivorship Bias

The backtest uses the **current** S&P 500 constituent list, not the point-in-time historical list. This means:

- Only companies that survived to be in the current index are included
- Companies that were dropped (often due to underperformance or bankruptcy) are excluded
- The **short leg is particularly biased** — we systematically short prior losers that, by definition, recovered enough to remain in the index today

A production system would use a point-in-time constituent database (e.g., from CRSP or Compustat).

### No Transaction Costs

The backtest is frictionless. With realistic costs (5–30 bps one-way) and ~30% monthly turnover, expect a 2–3% annual return drag.

### Momentum Crash Sensitivity

The strategy is exposed to "momentum crashes" — periods like March 2009 when prior losers violently rebound. See Daniel & Moskowitz (2016), "Momentum Crashes" for the canonical reference.

## Interpreting the Results

The observed strategy performance (negative Sharpe, large drawdown in 2009) is consistent with academic findings on naive momentum strategies. The two main drivers:

1. **2009 momentum crash** — Short leg got destroyed when beaten-down stocks rebounded
2. **Survivorship bias** in the short leg — Compounds the above effect

The Fama-French regression typically shows:
- Strongly negative HML beta — the textbook momentum signature
- No statistically significant alpha — momentum offers no free lunch in this naive form
- R² around 15–20% — most variance is idiosyncratic

## Dependencies

- `pandas`, `numpy` — Data manipulation
- `yfinance` — Price data
- `pandas-datareader` — Fama-French factor data
- `statsmodels` — OLS regression
- `matplotlib` — Tearsheet visualization
- `lxml`, `html5lib`, `beautifulsoup4` — HTML parsing for Wikipedia scrape
- `requests` — HTTP with custom User-Agent for Wikipedia

## Configuration

All parameters live in `config.py`. Common adjustments:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MOMENTUM_WINDOW` | 12 | Lookback window in months |
| `SKIP_RECENT` | 1 | Months to skip (reversal avoidance) |
| `N_QUANTILES` | 10 | Number of ranking buckets |
| `LONG_QUANTILE` | 10 | Which quantile to go long |
| `SHORT_QUANTILE` | 1 | Which quantile to short |
| `MIN_PRICE` | 5.0 | Penny stock filter threshold |
| `BACKTEST_START_DATE` | 2005-01-01 | Data download start |
| `BACKTEST_END_DATE` | 2025-12-31 | Data download end |
