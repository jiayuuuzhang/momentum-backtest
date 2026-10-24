# Momentum Strategy Research Review

Review date: October 23, 2026. Scope: the desktop `momentum-backtest` project, using historical membership and fixed top/bottom 10 selection. The review did not change strategy parameters, source prices, or official outputs. Numerical diagnostics were recomputed from the existing cache and do not constitute independent vendor validation.

## Research assessment

The project is a basic momentum research prototype. It does not yet establish stable, executable excess returns. Main concerns are missing histories, security identity and corporate-action handling, monthly risk reporting, short execution and borrowing costs, and dependence on extreme 2026 returns. High returns alone do not prove an error; reducing total return to 107.56% does not prove correctness either.

## Confirmed internal consistency

- The backtest covers October 2021 through September 2026: 60 months, with exactly 10 longs and 10 shorts per month. Each leg targets 100% notional exposure; selection is by fixed count, not 10% of the universe.
- Formation-date historical membership is enforced and checked. There is no evidence that selection still directly uses today's constituent list.
- Independently recomputed monthly gross returns, costs, and compounded net returns match the saved results.
- All 11 tests passed. They establish consistency for specified behaviors, not the correctness of vendor histories, membership records, or execution assumptions.

## 1. High priority: the historical universe remains an available-price subset

The historical union contains 608 ticker labels. Forty-four have no price series, and 46 have no valid price at any formation date. Historical membership counts range from 503 to 505; eligible ranking counts range from 465 to 498, averaging 480.7. Of 30,197 member-month records, 1,256 lack a formation-date price, 97 lack a signal endpoint, and two fail the price threshold.

Missingness cannot be assumed random: delisted, acquired, and failed companies are harder to retrieve. Correcting inclusion and removal dates does not supply missing prices or delisting returns. The direction of the bias cannot be inferred from ticker names alone; complete data are needed to measure it.

In `backtest.py`, `eligible_signals` drops missing values before ranking. The missing-held-return error protects selected positions but cannot protect companies that were never selected because their histories were unavailable.

Required work: obtain missing and delisted histories and terminal returns; at minimum, document each missing security, date, and reason. Distinguish complete-universe results from available-subset results.

## 2. High priority: daily risk materially exceeds month-end reported risk

Daily closing equity was reconstructed using the original fixed monthly holdings, the same adjusted daily prices, and the same monthly costs, without daily rebalancing. There were 1,254 valid dates and no missing daily marks. The maximum month-end reconciliation error was approximately 2.22e-16.

- Official maximum month-end drawdown: **36.16%**.
- Reconstructed maximum daily closing drawdown: **51.15%**, reached on July 29, 2026.
- Maximum within-month gross notional exposure divided by equity: approximately **342.33%**, despite a 200% target at each rebalance.

Daily closing drawdown still excludes intraday lows. The program does not check daily margin, liquidation, loan recalls, or equity exhaustion. This does not establish that a particular broker would have liquidated the account; it means the ability to maintain positions until month-end has not been demonstrated.

Required work: daily valuation, exposure, cash, and margin checks, while retaining month-end statistics as a separate reporting frequency.

## 3. High priority: profits depend heavily on the final nine months

- October 2021-December 2025: 51 months, cumulative return **-8.93%**.
- January-September 2026: nine months, cumulative return **+127.91%**.
- All 60 months: cumulative return **+107.56%**, annualized return **15.73%**.

The three largest positive net-return months were April 2026 (+40.58%), June 2026 (+25.51%), and January 2026 (+24.84%). As a concentration diagnostic only, setting those three returns to zero while leaving the other months unchanged produces a cumulative return of -5.77%. This is not an executable alternative strategy or a recommendation to discard extreme months.

April 2026 longs were CIEN, COHR, FIX, LITE, MU, SNDK, STX, TER, VRT, and WDC. MU, SNDK, STX, and WDC represented 40% of long notional exposure, illustrating substantial exposure to related businesses.

An attempt to cross-check important 2026 prices against Stooq returned HTTP 404 responses. Independent vendor price validation was not completed, and that limitation must remain explicit.

Required work: independently verify important price moves and corporate actions, then examine longer fixed-parameter histories, rolling windows, and industry attribution. Do not tune parameters merely to reduce reported returns.

## 4. High priority: short execution and financing assumptions are incomplete

The program assumes that all selected losers can be shorted at their target weights. It has no historical borrow inventory, borrow rates, recalls, forced buy-ins, collateral, or cash-interest model. A 10-basis-point trading charge is not a substitute for borrowing fees accrued over holding time.

The following is only a rough sensitivity exercise: assume short notional remains approximately 100% of equity and deduct the assumed annual borrow rate divided by 12 each month. Financing and cash interest are not included.

| Assumed annual borrow fee | Annualized strategy return |
|---|---:|
| 0%, current convention | 15.73% |
| 1% | 14.58% |
| 3% | 12.32% |
| 5% | 10.10% |
| 10% | 4.72% |

These are hypothetical rates, not historical observed borrowing costs or a complete after-cost backtest. Interest effects need not all be negative; actual account, collateral, and financing rules matter.

Reference: [IBKR explanation of borrow fees](https://www.interactivebrokers.com/campus/traders-insight/securities/short-selling/the-risks-of-shorting-series-part-ii-borrow-fees/).

## 5. Confirmed implementation gap: genuine zero terminal values cannot be ingested

At the reviewed version's `data.py` lines 71-72, any price less than or equal to zero raises `Nonpositive adjusted prices`.

An independent temporary CSV reproduced the issue: a prior price of 10, a genuine terminal settlement value of zero, and valid SPY prices cause rejection of the entire file. This is a gap in handling a security's total loss. A documented zero terminal payment is not the same as bad price data; not every delisting should be assigned a zero value either.

Required work: separate ordinary trading-price validation from event-based terminal returns. Use a documented terminal-payment or delisting-return table with sources, dates, and event types. Support a security-level -100% return and remaining cash without fabricating values.

Reference: [CRSP delisting-return definitions](https://wrds-www.wharton.upenn.edu/documents/400/CRSP_Programmers_Guide.pdf).

## 6. Execution timing and corporate actions remain approximations

The code checks the $5 threshold using the formation month's adjusted close and also uses that close as the next holding period's entry reference. It has no order submission, opening-price, volume, or matching model. Momentum skips the latest month, so this is not evidence that the signal directly uses next month's performance. The issue is the failure to separate formation-time filtering, target quantities, and idealized same-close execution.

Price ratios with `auto_adjust=True` can approximate total returns, but adjusted prices are not executable prices or actual share counts. Applying today's adjusted-price scale to a historical $5 threshold can be affected by subsequent dividends or splits. Only two records failed the current threshold, so its effect should not be blamed for the principal performance differences without a separate calculation.

Rename mappings use ticker strings rather than a complete stable security-ID, share-class, conversion, spin-off distribution, and terminal-cash-flow master. The review found no held rename event causing duplicate trades in this run, but the mapping design requires improvement before extending the data. Rejecting reused PARA and INFO histories does not establish that all other historical identities have been independently checked.

Required work: separate executable prices, total returns, corporate actions, and security identities. Specify information cutoffs and the next executable trading time, then test execution sensitivity.

## 7. Beating SPY in raw return does not establish excess-return skill

| Metric | Current strategy | SPY |
|---|---:|---:|
| Annualized return | 15.73% | 13.70% |
| Annualized volatility from monthly returns | 40.86% | 15.67% |
| Zero-risk-free-rate Sharpe | 0.558 | 0.901 |

The strategy takes substantially more risk and starts each month with 200% gross notional exposure, compared with a 100% long SPY position. Zero net notional does not imply zero market beta or zero industry exposure. A diagnostic market-only regression over these 60 months estimates beta near 0.25, but it is not a complete risk attribution.

The simple independent-and-identically-distributed t-statistic for mean monthly returns is approximately 1.25, which is weak evidence. Extreme observations and dependence also limit that simple statistic.

Required work: consistent cash and risk-free-rate accounting, risk-matched benchmarks, industry and momentum/size/value factor attribution, and uncertainty estimates rather than point estimates alone.

## 8. The benefit of the short leg has not been established

Using the same monthly selections, independently compound each leg at 100% notional exposure without trading or borrowing costs: the long leg returns +293.56%, while the short leg returns -49.75%. These cumulative returns cannot be added to recover the combined portfolio return; this is a standalone-leg diagnostic.

Required work: formally compare the full long-short strategy, the same long selections without shorts, SPY, and an equal-weight universe, with their own costs and risk measures. The original GitHub strategy's use of shorts does not establish that shorts add value here.

## 9. Robustness and research design are insufficient

There are only 60 months, and their outcomes have already been examined. This is not a strictly unseen sample. Changing from 10% to 10 stocks was the user's explicit specification and is not automatically performance-driven overfitting. Repeatedly choosing counts or windows based on this same period would, however, introduce data snooping.

Missing work includes a prespecified in-sample/out-of-sample design, multiple market regimes, parameter-neighborhood stability, rebalance-date and execution-delay sensitivity, industry-concentration and capacity analysis, and confidence intervals for net performance. A basic strategy does not need every possible risk control, but its exposures must be measured.

Required work: fix the study design before running comparisons rather than selecting the best parameters after observing results.

## 10. Engineering and result-state issues

- `main.py` writes `complete_available_data` before all metrics, charts, and independent audits finish. A later failure can leave an outdated completed status.
- Files in one `outputs` directory are overwritten individually, without atomic publication or a unique run ID. A failed run can mix new coverage tables with old return files.
- Membership snapshots have a SHA-256 checksum, but price caches are recorded by path rather than content hash. `--refresh` can replace a same-named file, so a report is not fully bound to its original price contents.
- The community-history coverage declaration and official extension have not undergone complete event-by-event, two-source verification.

Required work: separate run directories; hashes for prices, configurations, code, and sources; atomic updates to a `latest` pointer after audit success; and distinct states for calculation completion, data completeness, and independent validation.

## Recommended order of work

1. Establish security identities and corporate-action records. Complete missing and delisted price histories and terminal returns, and verify the important 2026 price moves.
2. Add daily valuation, explicit execution timing, borrowing and funding constraints, daily drawdowns, and exposure reporting.
3. Fix the research plan and compare subperiods, long-only versus long-short portfolios, matched-risk benchmarks, and parameter stability.
4. Only then consider strategy changes. Do not suppress or embellish returns to make them appear more normal.
