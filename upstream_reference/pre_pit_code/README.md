# 基础 S&P 500 动量策略

基于 https://github.com/adithya1309/momentum-backtest 修改。本项目只使用历史价格，不使用新闻或情绪模型。

## 策略规则

1. 股票池沿用当前 S&P 500 成分股。
2. 每个月末计算 12–1 动量：P(t−1) / P(t−12) − 1，跳过最近一个月。
3. 买入动量最高的 10 只，做空最低的 10 只；两端分别等权，各 100% 名义敞口，每只多头 +10%、每只空头 −10%。固定数量配置为 `config.py` 的 `LONG_COUNT` 和 `SHORT_COUNT`。
4. 持有一个月，每月再平衡；形成月末复权价格不足 $5 的股票不进入新持仓。
5. 默认单边交易成本 10 bps，按换手计算；SPY 为基准。

默认回测 2021-10-01 至 2026-09-30，共五年、60 个完整月份（2021 年和 2026 年为部分自然年）。额外下载 15 个月价格作为信号预热，不计入回测收益。本次完整行情缓存为 2020-07-01 至 2026-09-30，共 1,570 个交易日，包含 502 个股票代码及 SPY；部分股票历史较短。

## 本机运行

双击同目录的 `run.command`，或在终端运行：

```bash
cd "/Users/zhangjiayu/Desktop/momentum-backtest"
.venv/bin/python main.py
```

环境已安装，真实行情已缓存。其他机器先运行 `python3 -m venv .venv`，再运行 `.venv/bin/python -m pip install -r requirements.txt`。

可选参数：

```bash
# 修改日期：起点须为月初，终点非月末时只计算完整月份
.venv/bin/python main.py --start 2021-10-01 --end 2026-09-30
# 不计算交易成本
.venv/bin/python main.py --cost-bps 0 --output outputs_no_cost
# 从其他来源导入复权日收盘价：首列日期，其余列为 ticker，必须含 SPY
.venv/bin/python main.py --prices-csv /absolute/path/prices.csv
# 重新下载价格；成分股名单仍使用缓存
.venv/bin/python main.py --refresh
```

## 结果文件

- `outputs/tearsheet.png`：净值、回撤、逐年收益图。
- `outputs/annual_returns.csv`：逐年收益和有效月数。
- `outputs/report.json`：总收益、年化收益、波动率、Sharpe、最大月末回撤及数据来源。
- `outputs/monthly_returns.csv`：每月策略毛收益、成本、净收益、SPY 收益、换手及持仓数。
- `outputs/holdings.csv`：每月持仓、权重、形成日期和信号。
- `outputs/data_coverage.csv`：各股票行情覆盖数量。
- `data_cache/`：Yahoo 真实复权行情和股票池缓存。

最新固定 10/10 策略结果见 `outputs/report.json`。原百分比策略的 2021-10 至 2026-09 结果保存在 `outputs_deciles_2021-10_2026-09/`。旧版 2021–2025 结果保存在 `outputs_2021-2025/`。年度收益表中的 2021 年仅含 10–12 月，2026 年仅含 1–9 月，不能当作完整年度收益。

## 回测口径

使用当前成分股存在幸存者偏差，不是历史逐时点成分股回测。没有价格的股票记录在 report.json；新上市股票需有足够历史后才能选入。选股只使用形成时已知数据；持仓收益缺失时明确报错。回撤按月末计算；不含借券费用、融资成本、现金利息和最终清仓成本。$5 筛选使用复权价格近似。原仓库 20 年图仅存于 `upstream_reference/` 作为参考。

验证命令：`.venv/bin/python -m unittest discover -s tests -v`。
