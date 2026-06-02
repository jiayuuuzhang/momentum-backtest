from data import load_all_data
from signals import compute_momentum_signal
from backtest import compute_monthly_returns, run_backtest
from analytics import ff_regression, summary_statistics
from tearsheet import plot_tearsheet

def main():
    print("Loading data...")
    monthly_prices, benchmark_returns, ff_factors = load_all_data()

    print("Computing momentum signals...")
    signals = compute_momentum_signal(monthly_prices)

    print("Computing monthly returns...")
    monthly_returns = compute_monthly_returns(monthly_prices)

    print("Running backtest...")
    backtest_results = run_backtest(monthly_returns, signals)

    print("Running Fama-French regression...")
    ff_model = ff_regression(backtest_results['long_short'], ff_factors)
    print(ff_model.summary())

    print("Computing summary statistics...")
    stats = summary_statistics(backtest_results, benchmark_returns)

    print("Generating tearsheet...")
    plot_tearsheet(backtest_results, benchmark_returns, ff_model, stats)
    print("Done. Tearsheet saved to tearsheet.png")

if __name__ == "__main__":
    main()
