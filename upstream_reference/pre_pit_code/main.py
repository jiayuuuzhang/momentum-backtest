import argparse
import json
from pathlib import Path
import pandas as pd
import os
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).parent / "data_cache" / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import BACKTEST_START_DATE, BACKTEST_END_DATE, LONG_COUNT, SHORT_COUNT
from data import load_prices
from backtest import run_strategy
from analytics import summarize, drawdown_series


def main():
    parser = argparse.ArgumentParser(description="S&P 500 monthly momentum backtest")
    parser.add_argument("--start", default=BACKTEST_START_DATE)
    parser.add_argument("--end", default=BACKTEST_END_DATE)
    parser.add_argument("--prices-csv", type=Path)
    parser.add_argument("--cost-bps", type=float, default=10)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent/"outputs")
    args = parser.parse_args()
    if pd.Timestamp(args.start).day != 1 or pd.Timestamp(args.start)>pd.Timestamp(args.end):
        parser.error("start must be first day of month and <= end")
    if args.cost_bps < 0:
        parser.error("cost must be nonnegative")
    args.output.mkdir(parents=True, exist_ok=True)
    prices, metadata, coverage = load_prices(args.start,args.end,args.prices_csv,args.refresh)
    results, holdings = run_strategy(prices,args.start,args.end,args.cost_bps)
    stats, annual = summarize(results)
    results.to_csv(args.output/"monthly_returns.csv")
    holdings.to_csv(args.output/"holdings.csv",index=False)
    coverage.to_csv(args.output/"data_coverage.csv")
    annual.to_csv(args.output/"annual_returns.csv")
    metadata.update({"requested_start":args.start,"requested_end":args.end,"actual_first_month":str(results.index.min().date()),"actual_last_month":str(results.index.max().date()),"cost_bps":args.cost_bps,"universe":"current S&P500; survivorship bias", "long_count":LONG_COUNT,"short_count":SHORT_COUNT,"selection":"highest and lowest 12-1 momentum; fixed stock counts", "gross_exposure":2,"short_borrow_and_financing":"excluded", "drawdown_frequency":"monthly", "metrics":stats})
    (args.output/"report.json").write_text(json.dumps(metadata,indent=2,allow_nan=False))
    fig, axes = plt.subplots(2,2,figsize=(14,9))
    for name in ["strategy","SPY"]:
        axes[0,0].plot(results.index,(1+results[name]).cumprod(),label=name)
        axes[0,1].plot(results.index,drawdown_series(results[name]),label=name)
    axes[0,0].set_title("Growth of $1 (net of transaction costs)")
    axes[0,0].legend()
    axes[0,1].set_title("Month-end drawdown")
    annual[["strategy","SPY"]].plot.bar(ax=axes[1,0],rot=0)
    axes[1,0].set_title("Calendar-year returns")
    axes[1,1].axis("off")
    text = "\n".join(f"{name}: total {value['total_return']:.2%}, CAGR {value['annualized_return']:.2%}\nmax DD {value['max_drawdown_monthly']:.2%}" for name,value in stats.items())
    axes[1,1].text(0,.9,text+"\n\nCurrent constituents: survivorship bias\nLong top 10 / short bottom 10; each leg 100%\nBorrow fees and financing excluded",va="top")
    fig.tight_layout()
    fig.savefig(args.output/"tearsheet.png",dpi=160)
    plt.close(fig)
    print(annual.to_string())
    print(json.dumps(stats,indent=2))
    print(f"Outputs: {args.output.resolve()}")

if __name__ == "__main__":
    main()
