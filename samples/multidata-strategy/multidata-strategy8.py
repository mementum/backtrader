#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之六：timer 调仓 + 多周期趋势过滤
#
# 在 multidata-strategy6（动量轮动）基础上做两个正规化升级：
#
#   1. add_timer(monthdays=[1]) 替换手写的"月份变化检测"——
#      调仓逻辑挪进 notify_timer 回调，next() 不再参与调仓；
#      monthcarry=True 保证 1 号非交易日时顺延到下一个交易日触发
#   2. cerebro.resampledata 把指数日线合成周线，周线收盘价站上
#      周线均线才允许持仓——"大周期定方向、小周期（月度轮动）做动作"
#
# 核心知识点：
#
#   - resampledata(feed, timeframe=bt.TimeFrame.Weeks)：合成的周线
#     和普通数据一样出现在 self.datas 里；日线→周线的 bar 只在
#     每周结束时交付，所以周中读到的 [0] 是最近一根已完成的周线，
#     不含未来数据
#   - notify_timer 独立于指标的 min period 机制，回测初期指标还没
#     "热身"完 timer 就会触发，必须自己做就绪检查（见 rebalance 开头）
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy8.py --quiet
#   .venv/bin/python samples/multidata-strategy/multidata-strategy8.py --no-filter --quiet
#   .venv/bin/python samples/multidata-strategy/multidata-strategy8.py --trendsma 20
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


class MomentumRotationTimer(bt.Strategy):
    '''动量轮动 + timer 月度调仓 + 指数周线趋势过滤

    约定：最后一个数据源是 resample 出来的指数周线，只算趋势不交易；
    其余是候选个股（日线）。
    '''

    params = dict(
        momentum=20,      # 动量回看天数
        topk=2,           # 持有最强的前 K 只
        reserve=0.05,     # 预留现金比例
        trendsma=10,      # 指数周线均线周期（周）
        use_filter=True,  # 是否启用周线趋势过滤
        printout=True,
    )

    def __init__(self):
        self.stocks = self.datas[:-1]
        self.index_w = self.datas[-1]     # 指数周线（resample 合成）

        self.rocs = {d: bt.ind.ROC(d, period=self.p.momentum)
                     for d in self.stocks}
        self.trend_sma = bt.ind.SMA(self.index_w, period=self.p.trendsma)

        # 每月 1 号（非交易日顺延）开盘时触发，回调 notify_timer
        self.add_timer(
            when=bt.timer.SESSION_START,
            monthdays=[1],
            monthcarry=True,
        )

    def log(self, txt):
        if self.p.printout:
            print('{} {}'.format(self.data.datetime.date(0), txt))

    def notify_timer(self, timer, when, *args, **kwargs):
        self.rebalance()

    def rebalance(self):
        # timer 不等指标热身，就绪检查必不可少：
        # 个股动量需要 momentum 根日线，趋势线需要 trendsma 根周线
        if len(self) <= self.p.momentum or not len(self.trend_sma):
            return

        # 周线 bar 只在每周结束时交付，[0] 是最近一根已完成的周线
        bullish = (not self.p.use_filter or
                   self.index_w.close[0] > self.trend_sma[0])

        if not bullish:
            self.log('指数周线跌破 {} 周均线，全员空仓'.format(self.p.trendsma))
            for d in self.stocks:
                if self.getposition(d):
                    self.order_target_percent(data=d, target=0.0)
            return

        ranked = sorted(self.stocks,
                        key=lambda d: self.rocs[d][0], reverse=True)
        targets = [d for d in ranked[:self.p.topk] if self.rocs[d][0] > 0]

        self.log('调仓: 目标持仓 [{}]'.format(
            ', '.join('{}({:+.1%})'.format(d._name, self.rocs[d][0])
                      for d in targets) or '空仓'))

        for d in self.stocks:
            if d not in targets and self.getposition(d):
                self.order_target_percent(data=d, target=0.0)

        if targets:
            weight = (1.0 - self.p.reserve) / len(targets)
            for d in targets:
                self.order_target_percent(data=d, target=weight)

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
    print('绩效报告（动量 {} 日 / 前 {} 名 / 周线过滤: {}）'.format(
        args.momentum, args.topk, '关' if args.no_filter else
        '{} 周'.format(args.trendsma)))
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


def fetch_index(symbol, fromdate, todate):
    """指数日线：新浪源 stock_zh_index_daily，返回全部历史后按日期切片"""
    df = ak.stock_zh_index_daily(symbol=symbol)
    df = normalize(df, symbol)
    return df.loc[fromdate:todate]


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

    # 指数日线 resample 成周线加入——必须最后加，策略约定 datas[-1] 是它
    print('正在从 AKShare 拉取指数 {} 的日线数据...'.format(args.index))
    dfi = fetch_index(args.index, args.fromdate, args.todate)
    cerebro.resampledata(
        bt.feeds.PandasData(dataname=dfi),
        timeframe=bt.TimeFrame.Weeks,
        name=args.index + '_w')

    cerebro.addstrategy(MomentumRotationTimer,
                        momentum=args.momentum,
                        topk=args.topk,
                        trendsma=args.trendsma,
                        use_filter=not args.no_filter,
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
        description='multidata-strategy8 - timer 月度调仓 + 指数周线趋势过滤')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001,601318,300750,600036',
                        help='候选池 A 股代码，逗号分隔，至少 2 只')

    parser.add_argument('--index', required=False, default='sh000001',
                        help='趋势过滤用指数代码（新浪格式）')

    parser.add_argument('--trendsma', required=False, type=int, default=10,
                        help='指数周线均线周期（周）')

    parser.add_argument('--no-filter', action='store_true',
                        help='关闭周线趋势过滤（用于对比）')

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
                        help='策略参数，如: reserve=0.1')

    parser.add_argument('--quiet', action='store_true',
                        help='不打印逐笔日志，只看绩效报告')

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help='绘图并可传入 kwargs')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
