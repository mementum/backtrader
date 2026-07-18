#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之四：动量轮动
#
# 与前几版「每个标的独立跑均线信号」不同，轮动策略把 N 个标的看作一个
# 候选池，定期比较相对强弱、只持有最强的 K 只：
#
#   - 每月第一个交易日调仓（按月份变化检测，不依赖定时器）
#   - 动量 = 过去 momentum 日的涨幅（bt.ind.ROC）
#   - 排序取前 K 名：新入选的用 order_target_percent 买到目标权重，
#     掉出榜单的清仓；动量为负的不买（宁可空仓，不接下跌趋势）
#
# 核心知识点（在前几版之上新增）：
#
#   - order_target_percent(data, target) —— 按「目标权重」调仓，
#     backtrader 自动算出应买/应卖的差额，是轮动/组合策略的标准下单方式
#     （注意：target 系列下单不经过 Sizer）
#   - 按月调仓的月份变化检测写法
#
# 费率与绩效报告沿用 multidata-strategy5（A 股真实费率 + Analyzers）：
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy6.py --quiet
#   .venv/bin/python samples/multidata-strategy/multidata-strategy6.py --topk 1 --momentum 60
#   .venv/bin/python samples/multidata-strategy/multidata-strategy6.py --symbols 600519,000001,601318,300750,600036
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import os
import os.path
import sys

# 东财等国内数据源直连即可，绕过系统代理（代理常导致连接失败）
os.environ['NO_PROXY'] = '*'

# 未 pip 安装 backtrader 时，直接使用仓库根目录下的源码
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import akshare as ak
import pandas as pd

import backtrader as bt


class AStockCommission(bt.CommInfoBase):
    '''A 股费率：佣金按成交额百分比双边收（有最低门槛），印花税只在卖出时收'''

    params = dict(
        commission=0.00025,   # 佣金万 2.5
        stamp_duty=0.0005,    # 印花税千 0.5（卖出单边）
        min_comm=5.0,         # 最低佣金 5 元
        stocklike=True,
        commtype=bt.CommInfoBase.COMM_PERC,
    )

    def _getcommission(self, size, price, pseudoexec):
        comm = max(abs(size) * price * self.p.commission, self.p.min_comm)
        if size < 0:  # 卖出加收印花税
            comm += abs(size) * price * self.p.stamp_duty
        return comm


class MomentumRotation(bt.Strategy):
    '''动量轮动：每月初持有候选池中动量最强的 topk 只

    所有数据源都是候选标的（本版本不含指数择时，动量为负不买
    本身就是一种择时）。
    '''

    params = dict(
        momentum=20,     # 动量回看天数
        topk=2,          # 持有最强的前 K 只
        reserve=0.05,    # 预留现金比例（防止满仓时费用导致下单失败）
        printout=True,
    )

    def __init__(self):
        # 每个标的一个动量指标：过去 momentum 日的收益率
        self.rocs = {d: bt.ind.ROC(d, period=self.p.momentum)
                     for d in self.datas}
        self.last_month = None

    def log(self, txt):
        if self.p.printout:
            print('{} {}'.format(self.data.datetime.date(0), txt))

    def notify_order(self, order):
        if order.status == order.Completed:
            self.log('{} {} {}@{:.2f} 费用 {:.2f}'.format(
                order.data._name,
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price,
                order.executed.comm))
        elif not order.alive():
            self.log('{} 订单未成交: {}'.format(
                order.data._name, order.getstatusname()))

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log('{} 毛利 {:.2f} 净利 {:.2f}'.format(
                trade.data._name, trade.pnl, trade.pnlcomm))

    def next(self):
        # 只在每月第一个交易日调仓
        month = self.data.datetime.date(0).month
        if month == self.last_month:
            return
        self.last_month = month

        # 按动量降序排名，取前 K 且动量为正的进入目标组合
        ranked = sorted(self.datas,
                        key=lambda d: self.rocs[d][0], reverse=True)
        targets = [d for d in ranked[:self.p.topk] if self.rocs[d][0] > 0]

        self.log('调仓: 目标持仓 [{}]'.format(
            ', '.join('{}({:+.1%})'.format(d._name, self.rocs[d][0])
                      for d in targets) or '空仓'))

        # 先清掉落榜的（腾出资金），再买入/调整入选的
        for d in self.datas:
            if d not in targets and self.getposition(d):
                self.order_target_percent(data=d, target=0.0)

        if targets:
            weight = (1.0 - self.p.reserve) / len(targets)
            for d in targets:
                self.order_target_percent(data=d, target=weight)


def print_report(cerebro, result, args):
    '''从 analyzers 取值，打印绩效报告'''
    strat = result[0]
    sharpe = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.dd.get_analysis()
    sqn = strat.analyzers.sqn.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    returns = strat.analyzers.returns.get_analysis()

    total = trades.get('total', {}).get('closed', 0)
    won = trades.get('won', {}).get('total', 0)
    pnl_won = trades.get('won', {}).get('pnl', {}).get('total', 0.0)
    pnl_lost = trades.get('lost', {}).get('pnl', {}).get('total', 0.0)

    print('=' * 50)
    print('绩效报告（动量 {} 日 / 持有前 {} 名）'.format(
        args.momentum, args.topk))
    print('-' * 50)
    print('期末资产:     {:,.2f}'.format(cerebro.broker.getvalue()))
    print('总收益率:     {:.2%}'.format(returns.get('rtot', 0.0)))
    print('年化收益率:   {:.2%}'.format(returns.get('rnorm', 0.0)))
    print('最大回撤:     {:.2%}（金额 {:,.2f}）'.format(
        dd.max.drawdown / 100, dd.max.moneydown))
    print('夏普比率:     {}'.format(
        '{:.3f}'.format(sharpe['sharperatio'])
        if sharpe.get('sharperatio') is not None else 'N/A'))
    print('SQN:          {:.3f}（{} 笔）'.format(
        sqn.get('sqn', 0.0), sqn.get('trades', 0)))
    if total:
        print('胜率:         {:.1%}（{}/{}）'.format(won / total, won, total))
        if pnl_lost:
            print('盈亏比:       {:.2f}'.format(abs(pnl_won / pnl_lost)))
    print('=' * 50)


def fetch_eastmoney(symbol, fromdate, todate):
    """东财源：stock_zh_a_hist，返回中文列名"""
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period='daily',
        start_date=fromdate.replace('-', ''),
        end_date=todate.replace('-', ''),
        adjust='qfq')
    return df.rename(columns={
        '日期': 'date',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume',
    })


def fetch_sina(symbol, fromdate, todate):
    """新浪源：stock_zh_a_daily，代码需带 sh/sz 前缀，列名已是英文"""
    prefix = 'sh' if symbol.startswith(('5', '6', '9')) else 'sz'
    return ak.stock_zh_a_daily(
        symbol=prefix + symbol,
        start_date=fromdate.replace('-', ''),
        end_date=todate.replace('-', ''),
        adjust='qfq')


def normalize(df, symbol):
    """统一索引与列，转成 backtrader 可用的 DataFrame"""
    if df is None or df.empty:
        raise SystemExit('未获取到 {} 的数据，请检查代码或网络'.format(symbol))
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    return df[['open', 'high', 'low', 'close', 'volume']]


def fetch_stock(symbol, fromdate, todate):
    """个股日线（前复权）：东财失败自动降级到新浪源"""
    try:
        df = fetch_eastmoney(symbol, fromdate, todate)
    except Exception as e:
        print('{} 东财源获取失败（{}），改用新浪源...'.format(
            symbol, type(e).__name__))
        df = fetch_sina(symbol, fromdate, todate)
    return normalize(df, symbol)


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)
    cerebro.broker.addcommissioninfo(AStockCommission())

    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    if len(symbols) < 2:
        raise SystemExit('轮动策略至少需要 2 个标的')

    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        df = fetch_stock(symbol, args.fromdate, args.todate)
        print('{} 获取 {} 根 K 线（{} ~ {}）'.format(
            symbol, len(df), df.index[0].date(), df.index[-1].date()))
        cerebro.adddata(bt.feeds.PandasData(dataname=df), name=symbol)

    cerebro.addstrategy(MomentumRotation,
                        momentum=args.momentum,
                        topk=args.topk,
                        printout=not args.quiet,
                        **(eval('dict(' + args.strat + ')')))

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.02,
                        annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', tann=252)

    result = cerebro.run()
    print_report(cerebro, result, args)

    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy6 - 动量轮动（AKShare 数据 + A 股费率）')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001,601318,300750,600036',
                        help='候选池 A 股代码，逗号分隔，至少 2 只')

    parser.add_argument('--momentum', required=False, type=int, default=20,
                        help='动量回看天数')

    parser.add_argument('--topk', required=False, type=int, default=2,
                        help='持有动量最强的前 K 只')

    parser.add_argument('--fromdate', required=False, default='2023-01-01',
                        help='起始日期 YYYY-MM-DD')

    parser.add_argument('--todate', required=False, default='2024-12-31',
                        help='结束日期 YYYY-MM-DD')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=1000000, help='初始资金')

    parser.add_argument('--strat', required=False, action='store', default='',
                        help='策略参数，如: momentum=60,reserve=0.1')

    parser.add_argument('--quiet', action='store_true',
                        help='不打印逐笔日志，只看调仓记录与绩效报告')

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help='绘图并可传入 kwargs，如: --plot style="candle"')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
