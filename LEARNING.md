# backtrader 学习档案

> 个人学习记录：从零到完整回测工具链的实践路线。所有自制示例都可直接运行，
> 新对话时让 AI 先读本文件即可接上进度。

## 环境

- **运行方式**：仓库自带 `.venv`（Python 3.12），已装 akshare / pandas / quantstats。
  所有自制示例统一用 `.venv/bin/python -W ignore <脚本>` 运行
  （系统 Python 3.14 会报大量 backtrader 老代码的 SyntaxWarning，`-W ignore` 屏蔽）
- **自制示例无需 pip 安装 backtrader**：脚本开头已把仓库根目录插入 `sys.path`
- **网络注意**：
  - 本机代理（127.0.0.1:7897）对东财接口不通，脚本内已设 `NO_PROXY='*'` 直连
  - 东财行情接口会掐 Python 的请求（风控），所有数据脚本都做了
    **东财失败自动降级新浪源**，看到 `ConnectionError 改用新浪源` 属正常
  - 高频请求东财会触发 IP 级临时封禁（几十分钟自动解除）

## 学习路线（已完成 ✅）

### 第一阶段：跑通与数据接入

| 文件 | 内容 |
|---|---|
| `samples/sigsmacross/sigsmacross3.py` | 原版示例的本地 CSV 版（Yahoo 在线接口已死）；双均线 SignalStrategy 入门 |
| `samples/sigsmacross/sigsmacross4.py` | **AKShare 接入 A 股**：`fetch_data` → DataFrame → `bt.feeds.PandasData`；东财→新浪降级模板的起源 |

### 第二阶段：multidata 系列（核心学习线，3→11 递进）

均在 `samples/multidata-strategy/`：

| 文件 | 课题 | 核心 API / 概念 |
|---|---|---|
| `multidata-strategy3.py` | 多标的独立信号 | `for d in self.datas` 建指标、`getposition(d)`、`buy(data=d)`、`adddata(name=)` |
| `multidata-strategy4.py` | 指数择时过滤 | 指数作为"只算信号不交易"的数据源，约定 `datas[-1]`；大盘跌破均线清仓 |
| `multidata-strategy5.py` | 真实成本+仓位+评估 | `AStockCommission`（继承 CommInfoBase：万2.5佣金+最低5元+卖出印花税）、百分比 Sizer（整手取整）、Analyzers 绩效报告、`--no-filter` 对照 |
| `multidata-strategy6.py` | 动量轮动 | `order_target_percent`（不经过 Sizer）、月份变化检测、动量为负不买；样本内 +33% |
| `multidata-strategy7.py` | optstrategy 参数优化 | 网格扫描、OptReturn、`maxcpus=1`（macOS spawn 问题）；**过拟合实证：样本内冠军参数换时间段垫底** |
| `multidata-strategy8.py` | timer + 多周期 | `add_timer(monthdays=[1], monthcarry=True)` + `notify_timer`、`resampledata` 合成周线、**timer 不等指标热身要自查就绪** |
| `multidata-strategy9.py` | 订单执行族 | `StopTrail` 移动止损 + 订单管理（stops 字典、平仓前先 cancel）、`set_slippage_perc`、`fillers.FixedBarPerc` 量限；5 场景对比 |
| `multidata-strategy10.py` | Benchmark 基准对比 | `observers.Benchmark`、`TimeReturn(data=基准)` 算买入持有、分年超额表 |
| `multidata-strategy11.py` | 专业报告 | `analyzers.PyFolio` → `get_pf_items()` → quantstats HTML 报告（pyfolio 本体已死，quantstats 是替代品） |

### 第三阶段：自定义指标与底层机制

| 内容 | 位置 |
|---|---|
| 自定义 Indicator 实战 | `samples/custom-indicator/custom-indicator.py`：Bias（纯声明式，一行算式）+ Streak（递归指标，必须写 next；含 once 向量化直接操作 array） |
| lines/metabase 底层 | 已学（无文件，见下方"核心机制速记"） |

## 核心机制速记（lines/metabase）

- **LineBuffer**（`backtrader/linebuffer.py:162`）：数组+游标 idx，`close[0]`=`array[idx]`=现在，
  `[-1]`=昨天；每根 bar 全体 `forward()`，物理上读不到未来
- **运算符重载**（lineroot.py）：`__init__`（stage1）里 line 运算返回"计算图"对象；
  `next()`（stage2）里返回数值。同一表达式两个阶段含义不同
- **MetaBase 五段构造**（`metabase.py:84`）：doprenew→donew→dopreinit→doinit→dopostinit，
  框架魔法全部注入在这五个钩子里
- **MetaParams**：类属性 `params = dict(...)` → `self.p.xxx`，继承自动合并
- **findowner**（`metabase.py:42`）：新建指标时**爬调用栈**找 owner 策略自动注册——
  这就是 `bt.ind.SMA(...)` 不用传 self 的原因
- **minperiod 传播**：声明式指标沿计算图自动推导；手写 next 的要 `addminperiod`；
  策略取所有指标最大值，不足时走 `prenext`
- **runonce vs runnext**：默认向量化（指标走 once 批量算）；`--runnext` 逐 bar。
  自定义指标必测两种模式输出一致

## 踩过的坑（重要经验）

1. **Margin 拒单静默失败**：现金不够时订单被拒但无提示，日志显示 `buy 0@0.0`。
   `notify_order` 里打印 `order.getstatusname()` 排查
2. **递归指标 NaN 污染**：`next()` 首次调用时自己线的 `[-1]` 是 NaN，
   `max(NaN,0)+1` 会污染整条线且症状隐蔽（runonce 正常、runnext 全灭）。初值必须兜底
3. **决策/成交时点差一根 bar 影响巨大**：同一策略 timer 开盘触发 vs next 收盘后决策，
   收益 +33% vs +14%——侧面证明样本内收益脆弱
4. **收益口径**：`Returns` 分析器的 `rtot` 是**对数收益**，`TimeReturn` 是普通百分比。
   ln(1.3946)=0.3326，两者说的是同一件事
5. **跨库指标不可直接比**：backtrader SharpeRatio 0.75 vs quantstats 0.83（同一组收益），
   无风险利率与年化方式不同
6. **样本外验证是铁律**：strategy7 实证——2023-24 最优参数(momentum=20)在 2020-22 垫底；
   momentum=40 两段都不差。任何"惊艳"结果先换时间段重跑
7. **趋势过滤的性格**：躲得过阴跌、必然错过 V 型反转（strategy8 实证：2024-09 暴涨完美踏空）
8. **PyFolio 输出带 UTC 时区**：喂 quantstats 前 `returns.index.tz_convert(None)`
9. **动态 import 含 backtrader 类的模块**：必须先注册 `sys.modules['名字']`，
   否则 MetaParams 的 donew 按 `__module__` 回查会 KeyError

## 结果基准（2023-01-01 ~ 2024-12-31，5 只候选股，含 A 股真实费率）

| 策略 | 总收益 | 备注 |
|---|---|---|
| 双均线独立信号（strategy3） | -9.2% | 震荡市双均线的真实面貌 |
| +指数择时（strategy4/5） | -7.5% | 回撤砍半但救不了烂策略 |
| 动量轮动（strategy6） | +33.3%（对数口径） | 参数敏感，含运气成分 |
| 轮动+8%移动止损（strategy9） | +53.3% | 止损参数未经样本外检验 |
| 基准买入持有上证 | +8.6% | 2023 年策略跑输大盘 11.7% |

## 未学清单（按需取用）

- **正在学习：多因子选股**
  - 课程：`lessons/0001-backtrader-multifactor-selection.html`
  - 因子评价课：`lessons/0002-factor-ic-rankic.html`
  - 基本面时点课：`lessons/0003-fundamental-point-in-time.html`
  - 四因子打分课：`lessons/0004-four-factor-cross-sectional-scoring.html`
  - 示例：`samples/multidata-strategy/multidata-strategy12.py`
  - 研究脚本：`samples/factor-research/factor-research13.py`
  - 基本面审计：`samples/factor-research/fundamental-pit14.py`
  - 四因子截面打分：`samples/factor-research/factor-scoring15.py`
  - 速查：`reference/multifactor-checklist.html`
  - 当前实现：价格类因子、截面 robust z-score、加权排名、月度调仓、
    IC/RankIC、五分组收益、2023 年前后样本切分；单日四因子样例已实现
    MAD 缩尾、统一方向、行业/对数市值中性化、Z-score 和等权合成
  - 当前结论：15 只股票、2020-2024 月度样本中，Momentum/Trend/LowVol
    与复合因子均无稳定正 IC；strategy12 的正收益不能证明因子有效
  - 基本面审计：报告期法在 35/60 条观察中提前使用财报；25/25 份当前
    快照在首次披露后被更新，免费快照不具备完整 point-in-time 安全性
  - 待完成：完成课程回忆题，建立版本化财务采集表、历史股票池；把单日
    四因子截面扩展为月度面板，检验 IC、RankIC、边际贡献和样本外稳定性
- **replay 实战**：概念已学（大周期 bar 逐日"长大"，`replaydata` 替代 `resampledata`），
  未写实战文件；做日内多周期时再补
- **TradingCalendar**（A 股交易日历）、**exactbars 内存优化**、**btrun CLI**——工程边角料
- **实盘接口**（stores/brokers 三件套）：对接 IB/Oanda，A 股需自写 Store，暂无必要
- **写自己的真实策略**——学习线终点，随时可以开始

## 常用命令

```bash
# 任意自制示例
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy6.py --quiet

# 参数优化 + 样本外验证
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy7.py
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy7.py --fromdate 2020-01-01 --todate 2022-12-31

# 三大打折器对比 / 基准对比 / HTML 报告
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy9.py
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy10.py
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy11.py

# 多因子选股 / runonce 与 runnext 对照
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy12.py
.venv/bin/python -W ignore samples/multidata-strategy/multidata-strategy12.py --runnext --quiet

# 因子 IC / RankIC / 五分组收益
.venv/bin/python -W ignore samples/factor-research/factor-research13.py

# 基本面首次披露日 / 快照修订风险
.venv/bin/python -W ignore samples/factor-research/fundamental-pit14.py

# 单日四因子缩尾 / 中性化 / 标准化 / 等权合成
.venv/bin/python samples/factor-research/factor-scoring15.py
```
