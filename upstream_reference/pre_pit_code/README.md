# Basic S&P 500 Momentum Strategy: Archived Current-Universe Version

Adapted from https://github.com/adithya1309/momentum-backtest. This archived version uses historical prices only, without news or sentiment models. It predates the point-in-time membership correction and must not be mistaken for the current production version.

## Strategy rules

1. Use the current S&P 500 constituent list as the stock universe.
2. Compute monthly 12-1 momentum as `P(t-1) / P(t-12) - 1`, skipping the latest month.
3. Buy the 10 highest-momentum stocks and short the 10 lowest-momentum stocks. Equal-weight each leg at 100% notional exposure: +10% per long and -10% per short. Fixed counts are configured by `LONG_COUNT` and `SHORT_COUNT` in `config.py`.
4. Hold for one month and rebalance monthly. Exclude stocks whose formation-date adjusted price is below $5.
5. Apply a default one-way transaction cost of 10 basis points to turnover. Compare with SPY.

The default backtest interval is October 1, 2021 through September 30, 2026, covering 60 complete months. Calendar years 2021 and 2026 are partial. Download an additional 15 months for signal initialization, excluded from reported returns. At the time of this archived run, the price cache covered July 1, 2020 through September 30, 2026: 1,570 trading dates, 502 stock tickers, and SPY. Some securities have shorter histories.

## Running the project

Run the current project's `run.command`, or use the terminal from the project root:

```bash
cd momentum-backtest
.venv/bin/python main.py
```

The desktop environment and price cache were prepared locally. On another machine, first run `python3 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt`.

Options supported by the archived version:

```bash
# The start must be the first day of a month; incomplete ending months are excluded
.venv/bin/python main.py --start 2021-10-01 --end 2026-09-30
# Disable transaction costs
.venv/bin/python main.py --cost-bps 0 --output outputs_no_cost
# Import adjusted daily closes; the first column is the date, and SPY is required
.venv/bin/python main.py --prices-csv /absolute/path/prices.csv
# Redownload prices while retaining the cached constituent list
.venv/bin/python main.py --refresh
```

## Files and archives

- `outputs/tearsheet.png`: equity curves, drawdown, and annual returns.
- `outputs/annual_returns.csv`: annual or partial-year returns and included months.
- `outputs/report.json`: total return, annualized return, volatility, Sharpe, maximum month-end drawdown, and provenance.
- `outputs/monthly_returns.csv`: gross return, cost, net return, SPY return, turnover, and position counts.
- `outputs/holdings.csv`: monthly securities, weights, formation dates, and signals.
- `outputs/data_coverage.csv`: price observation counts.
- `data_cache/`: Yahoo adjusted price histories and the cached stock universe.

Current corrected results live in the project root's `outputs/`. The earlier percentage-based October 2021-September 2026 results are in `outputs_deciles_2021-10_2026-09/`; the earlier 2021-2025 results are in `outputs_2021-2025/`. These archives may be present only in the desktop project. The 2021 rows cover October-December, and the 2026 rows cover January-September, not full calendar years.

## Archived backtest conventions and limitations

This version uses current constituents, introducing survivorship bias, and is not a point-in-time universe backtest. Missing symbols are listed in `report.json`. New listings require sufficient historical prices before selection. Selection uses formation-time price inputs; missing held-stock returns raise an error. Drawdown uses month-end marks. Borrow fees, financing, cash interest, and final liquidation costs are excluded. The $5 screen uses adjusted prices as an approximation. The original upstream 20-year chart is retained under `upstream_reference/` for reference only.

Verification command: `.venv/bin/python -m unittest discover -s tests -v`.
