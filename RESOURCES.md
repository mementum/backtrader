# Backtrader 与多因子研究资源

## Knowledge

- [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
  Fama-French 三因子和五因子的官方数据与构造说明。用于理解规模、价值、盈利能力和投资风格的学术基线。
- [MSCI Factor Indexes](https://www.msci.com/indexes/factor-indexes/msci-factor-indexes)
  MSCI 对价值、低规模、低波动、高股息、质量和动量等实务因子的分类。用于确定透明多因子基线的因子家族。
- [Backtrader: Momentum Strategy](https://www.backtrader.com/blog/2019-05-20-momentum-strategy/momentum-strategy/)
  官方横截面动量示例与 Timer、数据就绪、调仓实现建议。用于组合排名和执行层设计。
- [Backtrader: Extending a Data Feed](https://www.backtrader.com/docu/extending-a-datafeed/)
  官方演示如何给 Data Feed 增加 P/E 等自定义 line。用于接入基本面和另类因子。
- [Alphalens performance.py](https://github.com/quantopian/alphalens/blob/master/alphalens/performance.py)
  因子 IC、分组收益等评价方法的参考实现。注意其 IC 默认使用 Spearman 相关。
- [Microsoft Qlib: Alpha Evaluation](https://github.com/microsoft/qlib/blob/main/qlib/contrib/eva/alpha.py)
  同时计算 Pearson IC 与 Spearman Rank IC 的实现。用于核对评价口径。
- [Microsoft Qlib: Alpha158 Loader](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/loader.py)
  人工设计价量特征的官方实现，包括收益、波动、相关性、成交量和位置类特征。用于后续对比透明风格因子与机器学习特征集。
- [Microsoft Qlib: Data Framework](https://qlib.readthedocs.io/en/latest/component/data.html)
  因子生成、截面处理、数据集和处理器的完整分层。用于设计 Backtrader 之前的研究流水线。
- [AKShare: 业绩报表](https://akshare.akfamily.xyz/data/stock/stock.html#id148)
  东方财富当前财务指标快照，包含报告指标和最新公告日期。用于教学和数据审计，不等同于版本化历史库。
- [AKShare: 巨潮信息披露公告](https://akshare.akfamily.xyz/data/stock/stock.html#id153)
  按股票和报告类型查询原始公告日期及链接。用于核对定期报告首次披露日。

## Wisdom (Communities)

- [Backtrader Community](https://community.backtrader.com/)
  查找框架行为、订单与多数据源历史讨论。项目已较老，代码结论应以本地源码验证。

## Gaps

- A 股可复现的 point-in-time 财务数据库尚未确定；已确认免费当前快照会在后续年份更新旧报告指标，缺少修订前版本。
- 历史指数成分、ST、停牌、退市和行业分类数据仍需建立统一数据源。
