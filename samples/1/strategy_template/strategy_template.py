import backtrader as bt # 导入 Backtrader 
import backtrader.indicators as btind # 导入策略分析模块
import backtrader.feeds as btfeeds # 导入数据模块
import pandas as pd
 
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
 
    def notify_order(self, order):
        '''可选，打印订单信息'''
        pass
 
    def notify_trade(self, trade):
        '''可选，打印交易信息'''
        pass
 
    def next(self):
        '''必选，编写交易策略逻辑'''
        sma = btind.SimpleMovingAverage(...) # 计算均线
        pass
 
# 实例化 cerebro
cerebro = bt.Cerebro()
# 通过 feeds 读取数据
data = btfeeds.BacktraderCSVData(...) 
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