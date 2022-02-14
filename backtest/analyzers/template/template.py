import backtrader as bt
from backtrader.analyzer import Analyzer
from backtrader.dataseries import TimeFrame # 导入 Backtrader 
 
# 社区自定义分析器示例：https://community.backtrader.com/topic/1274/closed-trade-list-including-mfe-mae-analyzer
# 创建分析器
class MyAnalyzer(bt.Analyzer):
    # 初始化参数：比如内置分析器支持设置的那些参数
    params = (
        (...,...), # 最后一个“,”最好别删！
    )
    # 初始化函数
    def __init__(self):
        '''初始化属性、计算指标等'''
        pass
    
    # analyzer与策略一样，都是从第0根bar开始运行
    # 都会面临 min_period 问题
    # 所以都会通过 prenext、nextstart 来等待 min_period 被满足
    def start(self):
        pass
    
    def prenext(self):
        pass
    
    def nextstart(self):
        pass
    
    def next(self):
        pass
    
    def stop(self):
        # 一般对策略整体的评价指标是在策略结束后开始计算的
        pass
    
  # 支持与策略一样的信息打印函数
    def notify_order(self, order):
        '''通知订单信息'''
        pass
 
    def notify_trade(self, trade):
        '''通知交易信息'''
        pass
    
    def notify_cashvalue(self, cash, value):
        '''通知当前资金和总资产'''
        pass
    
    def notify_fund(self, cash, value, fundvalue, shares):
        '''返回当前资金、总资产、基金价值、基金份额'''
        pass
    
    def get_analysis(self):
        pass
 
