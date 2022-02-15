import backtrader as bt # 导入 Backtrader 
import backtrader.indicators as btind # 导入策略分析模块
from backtest.feeds.datafeeds import StockCsvData
 
# 创建策略
class StrategyTemplate(bt.Strategy):
    # 可选，设置回测的可变参数：如移动均线的周期
    params = (
        (...,...), # 最后一个“,”最好别删！
    )
    def log(self, txt, dt=None):
        '''可选，构建策略打印日志的函数：可用于打印订单记录或交易记录等'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
 
    def __init__(self):
        '''必选，初始化属性、计算指标等'''
        pass

    def start(self):
        '''在回测开始之前调用,对应第0根bar'''
        # 回测开始之前的有关处理逻辑可以写在这里
        # 默认调用空的 start() 函数，用于启动回测 
        pass

    def prenext(self):
        '''策略准备阶段,对应第1根bar-第 min_period-1 根bar'''
        # 该函数主要用于等待指标计算，指标计算完成前都会默认调用prenext()空函数
        # min_period 就是 __init__ 中计算完成所有指标的第1个值所需的最小时间段
        pass
    
    def nextstart(self):
        '''策略正常运行的第一个时点，对应第 min_period 根bar'''
        # 只有在 __init__ 中所有指标都有值可用的情况下，才会开始运行策略
        # nextstart()只运行一次，主要用于告知后面可以开始启动 next() 了
        # nextstart()的默认实现是简单地调用next(),所以next中的策略逻辑从第 min_period根bar就已经开始执行
        pass
 
    def next(self):
        '''必选，编写交易策略逻辑'''
        sma = btind.SimpleMovingAverage(...) # 计算均线
        pass

    def notify_order(self, order):
        '''可选，打印订单信息'''
        pass
 
    def notify_trade(self, trade):
        '''可选，打印交易信息'''
        pass

    def notify_cashvalue(self, cash, value):
        '''通知当前资金和总资产'''
        pass
    
    def notify_fund(self, cash, value, fundvalue, shares):
        '''返回当前资金、总资产、基金价值、基金份额'''
        pass
    
    def notify_store(self, msg, *args, **kwargs):
        '''返回供应商发出的信息通知'''
        pass
    
    def notify_data(self, data, status, *args, **kwargs):
        '''返回数据相关的通知'''
        pass
    
    def notify_timer(self, timer, when, *args, **kwargs):
        '''返回定时器的通知'''
        # 定时器可以通过函数add_time()添加
        pass
 
# 实例化 cerebro
cerebro = bt.Cerebro()
# 通过 feeds 读取数据
data = StockCsvData(...) 
# 将数据传递给 “大脑”
cerebro.adddata(data) 
# 通过经纪商设置初始资金
cerebro.broker.setcash(...)
# 设置单笔交易的数量
cerebro.addsizer(...)
# 设置交易佣金，双边各 0.0003
cerebro.broker.setcommission(commission=0.0003)
# 设置滑点，双边各0.0001
cerebro.broker.set_slippage_perc(perc=0.0001)
# 订单成交量不超过当日成交量的50%
cerebro.broker.set_filler(bt.broker.fillers.FixedBarPerc(perc=50))
# 添加策略
cerebro.addstrategy(...)
# 优化策略
# cerebro.optstrategy(StrategyTemplate, maperiod=range(10, 31))
# 添加策略分析指标
cerebro.addanalyzer(...)
# 添加观测器
cerebro.addobserver(...)
# 启动回测
result = cerebro.run()
# 从返回的 result 中提取回测结果
# strat = result[0]
# 返回日度收益率序列
# daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
# 可视化回测结果
cerebro.plot()