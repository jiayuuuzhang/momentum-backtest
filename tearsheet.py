import matplotlib.pyplot as plt
import numpy as np
from analytics import drawdown_series, rolling_sharpe

def plot_tearsheet(backtest_results, benchmark_returns, ff_model, stats, save_path='tearsheet.png'):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Cumulative returns
    cumulative_strategy = (1 + backtest_results['long_short']).cumprod()
    cumulative_benchmark = (1 + benchmark_returns).cumprod()
    axes[0, 0].plot(cumulative_strategy.index, cumulative_strategy.values, label='Strategy')
    axes[0, 0].plot(cumulative_benchmark.index, cumulative_benchmark.values, label='Benchmark')
    axes[0, 0].set_yscale('log')
    axes[0, 0].set_title('Cumulative Returns')
    axes[0, 0].legend()
    
    # Drawdown
    drawdown = drawdown_series(backtest_results['long_short'])
    axes[0, 1].plot(drawdown.index, drawdown.values)
    axes[0, 1].fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
    axes[0, 1].set_title('Drawdown')
    
    # Rolling Sharpe
    rolling_sharpe_series = rolling_sharpe(backtest_results['long_short'])
    axes[1, 0].plot(rolling_sharpe_series.index, rolling_sharpe_series.values)
    axes[1, 0].set_title('Rolling Sharpe Ratio')
    
    # Summary stats + Fama-French regression coefficients
    axes[1, 1].axis('off')
    coeffs = ff_model.params
    text = (
        f"Strategy Sharpe:       {stats['strategy_sharpe']:.2f}\n"
        f"Strategy Ann. Return:  {stats['strategy_annual_return']:.2%}\n"
        f"Strategy Ann. Vol:     {stats['strategy_annual_vol']:.2%}\n"
        f"Strategy Max DD:       {stats['strategy_max_dd']:.2%}\n"
        f"\n"
        f"Benchmark Sharpe:      {stats['benchmark_sharpe']:.2f}\n"
        f"Benchmark Ann. Return: {stats['benchmark_annual_return']:.2%}\n"
        f"Benchmark Max DD:      {stats['benchmark_max_dd']:.2%}\n"
        f"\n"
        f"Alpha (monthly): {coeffs['const']:.4f}\n"
        f"Mkt-RF beta:     {coeffs['Mkt-RF']:.4f}\n"
        f"SMB beta:        {coeffs['SMB']:.4f}\n"
        f"HML beta:        {coeffs['HML']:.4f}\n"
        f"R-squared:       {ff_model.rsquared:.3f}"
    )
    axes[1, 1].text(0.05, 0.5, text, fontsize=10, family='monospace', verticalalignment='center')
    axes[1, 1].set_title('Summary Statistics & Factor Attribution')
    
    plt.tight_layout()
    plt.savefig(save_path)

    return fig