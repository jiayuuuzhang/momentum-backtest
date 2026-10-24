# 基础 S&P 500 动量策略：历史成分股版本

基于 https://github.com/adithya1309/momentum-backtest 修改。每个形成日期只在当时属于 S&P 500 的股票中排名，禁止退回到当前成分股名单。

## 运行

双击 `run.command`，或运行：

```bash
cd "/Users/zhangjiayu/Desktop/momentum-backtest"
.venv/bin/python main.py
.venv/bin/python audit_results.py
.venv/bin/python -m unittest discover -s tests -v
```

结果默认保存到 `outputs/`。日期为 **2021-10-01 至 2026-09-30，共 60 个月**。行情从 2020-07-01 开始，前 15 个月用于信号预热。年度表 2021 年仅含 10–12 月，2026 年仅含 1–9 月。

## 策略

1. 在每个形成月末查找最后一个生效日期不晚于该日的历史成员快照。加入日期之后才允许选入；移除后不能形成新持仓，之后重新加入则重新具备成员资格。
2. 所有股票按 SPY 当月最后实际交易日取价，不把提前停牌/退市前的旧报价前填到月末。对当时成员计算 12–1 动量：P(t−1)/P(t−12)−1。信号端点需有价格，形成月末复权价至少 $5。
3. 买入排名最高的 **10 只**，做空最低的 **10 只**；每只多头 +10%、每只空头 −10%，总名义敞口 200%。并列按 ticker 稳定排序。
4. 持有下一个月，月末重新平衡。月内被指数移除不触发额外交易，仍持有至下次调仓；如果退市导致持仓缺少收益，回测报错，不能随意删除持仓或填零。
5. 默认单边交易成本 10 bps，按包含持仓漂移的换手计算，含首次建仓，不含最后清仓；SPY 使用同一回测月份。

## 历史成员数据与来源

历史记录来自 [fja05680/sp500](https://github.com/fja05680/sp500) 的 `S&P 500 Historical Components & Changes (Updated).csv`，固定到提交 `a2430f2af0c79ddf0748e91de11bdeb1616ab5a7`。原始文件、变更日志和 MIT 许可证都保存在 `data_cache/membership/`。

源文件最后一项变更是 2026-08-18，另根据 [S&P 官方公告](https://press.spglobal.com/2026-09-04-Bloom-Energy%2C-Illumina%2C-and-Everpure-Set-to-Join-S-P-500-Others-to-Join-S-P-100%2C-S-P-MidCap-400%2C-and-S-P-SmallCap-600) 补入 2026-09-21 生效的 BE、P、ILMN 加入与 TAP、TTD、BLDR 移除。公告日不等于加入日。9 月持仓在 8 月末形成，因此 9 月 21 日的新成员不能提前进入 9 月组合。

规范化快照在 `data_cache/membership/snapshots.csv`，每行是一个生效日期及当日完整成员集合；有效性持续到下一次变更。`.metadata.json` 记录来源、提交、覆盖截止和 SHA-256。超过明确覆盖日期或早于首个快照，程序报错。

这是社区重建的成员历史，并非 S&P 许可的完整证券主表；维护者也注明 Wikipedia 的 Selected Changes 不是完整历史。它纠正了直接使用当前名单的问题，但不能宣称数据绝对无误。

## 价格、旧代码与退市数据

价格来自 Yahoo Finance，显式 `auto_adjust=True`。下载范围是所有形成日期历史成员的并集，包含后来被移除的股票，不只是今天仍在指数里的股票。

纯更名映射及来源保存在 `ticker_aliases.csv`，例如 FB→META、GPS→GAP。形成日期仍使用历史成员代码，不能因行情供应商使用新标签而提前获得指数资格。First Republic 历史代码 FRC 使用同一失败银行的 OTC 代码 FRCB 历史行情；没有使用收购方 JPM 的价格替代。FBHS 使用同股更名 FBIN 的复权历史。

已核实 Yahoo 的 `PARA` 被 Banzai/Parabolic 复用，不是历史 Paramount；`INFO` 是 Harbor PanAgora ETF，不是历史 IHS Markit。这两个错误序列明确拒绝使用。没有用收购方或不相关公司的行情来填缺口。证券身份检查记录保存在 `identity_checks_*.json`。

**部分退市/收购证券的历史行情仍不可获取。**这些股票仍保留在历史成员审计表中，因缺行情或动量端点不足而不能排名，不会被当前幸存公司替换。因此结果是“历史成员中可获取行情的子集”，仍有数据覆盖偏差，不能称为完整无幸存者偏差回测。已持有股票缺收益则停止，绝不自行推断退市归零或收益为零。

`--prices-csv` 可提供更完整的真实复权日价格（包括 SPY）；列名可以使用历史代码或映射后的 provider 代码，请按 data.py 口径准备。用户提供的真实历史 PARA/INFO 可用，不适用对 Yahoo 当前复用代码的拒绝规则。

## 结果与审计文件

- `report.json`：累计收益、年化收益、年化波动率、零无风险利率 Sharpe、最大月末回撤、成员来源、缺失股票、价格路径和限制。
- `monthly_returns.csv`：月度毛/净收益、成本、SPY、换手、持仓数、历史成员数和可用排名数。
- `annual_returns.csv`：自然年内复合收益及有效月数。
- `holdings.csv`：形成日期、持有月份、历史代码、价格代码、权重、信号及所用成员快照日期。
- `membership_audit.csv`：每个形成日期的所有历史成员、行情/信号、是否可排名及原因。
- `unavailable_members.csv`：上述成员中因价格缺失、历史不足或低价过滤而未能排名的条目。
- `data_coverage.csv`：历史代码对应行情代码、数据条数和首尾日期。
- `audit_checks.csv`：独立核对每期成员资格、最高/最低各 10 只及收益算术。
- `stock_contributions.csv`：每只股票每个月对毛收益的贡献；跨月简单求和不是复合累计利润归因。
- `tearsheet.png`：净值、月末回撤、年度/部分年度收益与摘要。
- `run_status.json`：运行是否完成或因持仓价格缺失而停止。

旧的当前股票池 top/bottom 10 结果保存在 `outputs_current_universe_top10_2021-10_2026-09/`，原来 617.82% 不应作为本次修正后的收益。旧百分比分组结果另有归档。

## 参数

```bash
.venv/bin/python main.py --cost-bps 0 --output outputs_no_cost
.venv/bin/python main.py --prices-csv /absolute/path/adjusted_prices.csv
# 自定义有效日期快照，须显式给出已核实的覆盖截止
.venv/bin/python main.py --membership-csv /absolute/path/snapshots.csv --membership-through 2026-09-30
```

当前固定快照覆盖截至 2026-09-30。`--refresh` 重新下载价格，不会自动更新成员历史。扩展回测时间必须同时补充成员记录和覆盖说明。

月末回撤不包含月内低点；不含借券费、融资成本、借券可得性及实际成交限制。此次只修正股票池和证券映射，不为降低或提高收益而调参。
