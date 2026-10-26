# S&P 500 Momentum Strategy with Historical Membership

## Installation and execution

From a fresh checkout:

```bash
cd momentum-backtest
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

The desktop copy already has a virtual environment and cached prices. On macOS, you can also double-click `run.command`. After downloading through GitHub, run `chmod +x run.command` if necessary.

The first run in a fresh environment downloads market prices. The repository package includes the strategy, tests, historical-membership inputs, saved results, and research review; it excludes the local virtual environment and bulk price caches. Downloaded prices may change if the vendor revises its history.

Results are written to `outputs/`. The default backtest runs from **October 1, 2021 through September 30, 2026**, covering 60 complete months. Price history begins on July 1, 2020; the preceding 15 months initialize the signal and do not contribute to backtest performance. Calendar-year results cover only October-December in 2021 and January-September in 2026.

## Strategy rules

1. At each formation month-end, select the latest historical-membership snapshot whose effective date is no later than the formation date. A stock becomes eligible only once its addition is effective. A removed stock cannot enter a new portfolio unless it subsequently rejoins.
2. Mark all securities on SPY's last actual trading day of the month. Do not carry a suspended or delisted stock's earlier quote forward to month-end. Compute 12-1 momentum as `P(t-1) / P(t-12) - 1`, skipping the latest month. Both signal endpoints must have prices, and the formation-date adjusted price must be at least $5.
3. Buy the **10 highest-ranked stocks** and short the **10 lowest-ranked stocks**. Each long has a +10% target weight; each short has a -10% target weight. Each leg has 100% notional exposure, for 200% gross exposure. Ties are resolved by a stable ticker sort.
4. Hold for the following month and rebalance monthly. An index removal during the holding month does not trigger an additional trade. If a held security has no return because of a delisting or another data gap, the backtest stops rather than silently deleting the position or assigning a zero return.
5. Apply a default one-way transaction cost of 10 basis points to turnover, including position drift and initial establishment. Final liquidation is excluded. Evaluate SPY over the same return months.

## Historical-membership inputs

The history comes from `S&P 500 Historical Components & Changes (Updated).csv` in [fja05680/sp500](https://github.com/fja05680/sp500), pinned to commit `a2430f2af0c79ddf0748e91de11bdeb1616ab5a7`. Source records, the change log, and the MIT license are retained locally under `data_cache/membership/`. The upload package includes the normalized snapshots, provenance metadata, change log, license, ticker mappings, and identity checks.

The upstream file's last change is dated August 18, 2026. An [official S&P announcement](https://press.spglobal.com/2026-09-04-Bloom-Energy%2C-Illumina%2C-and-Everpure-Set-to-Join-S-P-500-Others-to-Join-S-P-100%2C-S-P-MidCap-400%2C-and-S-P-SmallCap-600) supplies the September 21, 2026 additions of BE, P, and ILMN and removals of TAP, TTD, and BLDR. An announcement date is not an effective inclusion date. September positions are formed at the end of August, so September 21 additions cannot enter that September portfolio early.

Normalized snapshots are stored in `data_cache/membership/snapshots.csv`. Each row contains an effective date and the complete constituent set on that date; membership remains effective until the next change. The accompanying `.metadata.json` records the source, commit, coverage endpoint, and SHA-256 checksum. Dates before the first snapshot or beyond the declared coverage endpoint are rejected.

This is a community reconstruction, not a licensed official security master. Its maintainer notes that Wikipedia's selected changes do not provide a complete history. It corrects the direct use of today's members but does not establish that every historical record is error-free.

## Market prices, ticker changes, and delistings

Prices come from Yahoo Finance with `auto_adjust=True` explicitly enabled. The download universe is the union of historical members across all formation dates, including companies subsequently removed from the index.

Ticker mappings and their sources are stored in `ticker_aliases.csv`, including FB to META and GPS to GAP. Membership is checked under the historical ticker before using a provider's current price label. A renamed price series does not grant early index eligibility. Historical FRC prices use the same failed bank's OTC ticker FRCB; JPMorgan's prices are not used as an acquirer proxy. FBHS uses the adjusted history served under the same company's renamed FBIN ticker.

Yahoo currently resolves `PARA` to Banzai/Parabolic rather than historical Paramount, and `INFO` to a Harbor PanAgora ETF rather than historical IHS Markit. Both incorrect series are explicitly rejected. Acquirer or unrelated-company prices are not substituted for missing histories. Identity checks are retained in `identity_checks_*.json`.

**Some delisted or acquired securities still lack historical prices.** They remain visible in the membership audit but cannot be ranked when prices or signal endpoints are unavailable. They are not replaced with present-day survivors. Results therefore describe the **available-price subset of historical members**, with residual data-coverage bias; they are not a complete survivorship-bias-free backtest. Missing held-security returns stop the run. The program never assumes that every delisted security becomes worthless or earns a zero return.

Use `--prices-csv` to supply more complete genuine adjusted daily prices, including SPY. Columns may use historical tickers or mapped provider tickers as supported by `data.py`. Genuine user-supplied historical PARA or INFO data are allowed; the rejection applies to Yahoo's currently reused symbols.

## Output files

All files below are written under `outputs/`:

| File | Contents |
|---|---|
| `report.json` | Total return, annualized return and volatility, zero-risk-free-rate Sharpe, month-end maximum drawdown, membership provenance, missing symbols, price paths, and limitations |
| `monthly_returns.csv` | Monthly gross and net returns, transaction costs, SPY returns, turnover, position counts, historical-member counts, and eligible-stock counts |
| `annual_returns.csv` | Compounded calendar-year or partial-year returns and the number of included months |
| `holdings.csv` | Formation date, return month, historical ticker, provider ticker, target weight, signal, and membership-snapshot date |
| `membership_audit.csv` | Every historical member at each formation date, prices, signals, eligibility, and exclusion reasons |
| `unavailable_members.csv` | Members excluded because of missing prices, insufficient signal history, or the minimum-price filter |
| `data_coverage.csv` | Historical-to-provider ticker mapping, observation count, and first and last available prices |
| `audit_checks.csv` | Independent checks of membership, exact top/bottom 10 selection, and return arithmetic |
| `stock_contributions.csv` | Individual monthly contributions to gross returns; summing these across months is not compounded capital-profit attribution |
| `tearsheet.png` | Equity curves, month-end drawdowns, annual or partial-year returns, and summary metrics |
| `run_status.json` | Completion status or missing-held-price error |
| `PIT_CHANGELOG.md` | Historical-universe correction notes |

The desktop's former current-universe top/bottom 10 results are archived in `outputs_current_universe_top10_2021-10_2026-09/`. The old 617.82% result is not the corrected strategy result. Earlier percentage-based runs are archived separately. These local archives are not part of the latest-results upload package.

## Configuration and verification

```bash
# Disable transaction costs and save a separate run
.venv/bin/python main.py --cost-bps 0 --output outputs_no_cost

# Supply adjusted daily prices from another source
.venv/bin/python main.py --prices-csv /absolute/path/adjusted_prices.csv

# Supply effective-date membership snapshots and a verified coverage endpoint
.venv/bin/python main.py --membership-csv /absolute/path/snapshots.csv --membership-through 2026-09-30

# Recheck saved results and run the tests
.venv/bin/python audit_results.py
.venv/bin/python -m unittest discover -s tests -v
```

The bundled membership history is covered through September 30, 2026. `--refresh` redownloads prices but does not update membership. Extending the backtest requires updated membership records and coverage metadata as well as prices.

Month-end drawdown excludes within-month lows. Borrow fees, financing, borrow availability, and actual execution constraints are not modeled. The research review in `research_review/RESEARCH_REVIEW.md` documents these limitations and the reconstructed daily-risk diagnostics. Universe and ticker corrections do not tune the strategy to raise or lower returns.
