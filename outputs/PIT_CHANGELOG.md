# Historical-Universe Correction Log

Backtest interval: October 1, 2021 through September 30, 2026, covering 60 months. Signal-initialization prices begin on July 1, 2020.

- Look up historical constituents by effective date before ranking. Securities that were not members on the formation date cannot be selected.
- Buy the highest-ranked 10 stocks and short the lowest-ranked 10 stocks. Each leg targets 100% notional exposure. One-way transaction costs remain 10 basis points. Strategy parameters were not changed to target a preferred result.
- Independently verify all 1,200 holding records for membership, ranking, target weights, and return arithmetic. All 11 tests passed.
- The union contains 608 historical ticker labels. Forty-four have no price series; see `unavailable_members.csv` for data and eligibility gaps.
- Historical FRC prices use the same bank's available FRCB history, not JPMorgan or another acquirer as a proxy.
- Reject Yahoo's reused PARA and INFO symbols when they identify unrelated securities.
- Mark positions on SPY's actual final trading day of each month. Do not carry suspended or delisted securities' earlier quotes forward to month-end.

Corrected available-data results, net of the specified transaction costs: total return **107.56%**, annualized return **15.73%**, and maximum month-end drawdown **-36.16%**.

The former current-universe result of 617.82% is no longer the default. Its desktop archive is `outputs_current_universe_top10_2021-10_2026-09/`.

Missing historical prices, possible gaps in community membership reconstruction, and excluded borrowing and financing costs remain. These results must not be described as fully survivorship-bias-free or executable live-trading performance.
