#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之七：订单执行族——回测三大打折器
#
# 以 multidata-strategy6 的动量轮动为基准（理想化成交，+33% 那个结果），
# 逐个加上真实交易的三重摩擦，一次运行跑 5 个场景输出对比表：
#
#   1. 滑点 —— broker.set_slippage_perc：市价单按开盘价 ± 滑点成交，
#      模拟冲击成本与买卖价差
#   2. 成交量限制 —— broker.set_filler(FixedBarPerc)：单根 bar 最多
#      吃掉成交量的 x%，大资金买不满目标仓位（本例资金小基本不触发，
#      资金规模上去后是主要约束）
#   3. 移动止损 —— StopTrail 订单：买入成交后挂一张追踪止损卖单，
#      价格回撤 trail% 自动触发；顺便学订单管理（挂单/撤单/追踪）
#
# 订单知识点：
#   - exectype：Market（默认）/ Limit / Stop / StopTrail / StopLimit
#   - StopTrail 的 trailpercent：止损价随最高价上移、永不下移
#   - 挂单是有状态的：调仓平仓前必须先 cancel 对应止损单，否则
#     仓位没了止损单还挂着，会凭空开出反向仓位
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy9.py
#   .venv/bin/python samples/multidata-strategy/multidata-strategy9.py --slip 0.002 --trail 0.05
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


class MomentumRotationST(bt.Strategy):
    '''动量轮动（同 multidata-strategy6）+ 可选 StopTrail 移动止损

    止损单管理规则：
      - 任何一笔订单成交后，先撤掉该标的旧止损单，若仍有持仓则按
        当前持仓量重新挂 StopTrail（覆盖建仓、加减仓所有情形）
      - 调仓平仓前先撤止损单，防止仓位清掉后止损单仍在场内
    '''

    params = dict(
        momentum=20,     # 动量回看天数
        topk=2,          # 持有最强的前 K 只
        reserve=0.05,    # 预留现金比例
        trail=0.0,       # 移动止损百分比（0 = 不启用）
        printout=False,
    )

    def __init__(self):
        self.rocs = {d: bt.ind.ROC(d, period=self.p.momentum)
                     for d in self.datas}
        self.last_month = None
        self.stops = {}          # data -> 在场的 StopTrail 订单

    def log(self, txt):
        if self.p.printout:
            print('{} {}'.format(self.data.datetime.date(0), txt))

    def cancel_stop(self, d):
        if d in self.stops:
            self.cancel(self.stops.pop(d))

    def notify_order(self, order):
        if order.alive():
            return

        d = order.data
        if order.status == order.Completed:
            is_stop = (order == self.stops.get(d))
            self.log('{} {} {}@{:.2f}{}'.format(
                d._name, 'buy' if order.isbuy() else 'sell',
                order.executed.size, order.executed.price,
                ' [止损触发]' if is_stop else ''))
            if is_stop:
                del self.stops[d]

        # 订单尘埃落定后统一整理止损单：撤旧、按现有持仓重挂
        if self.p.trail:
            self.cancel_stop(d)
            pos = self.getposition(d)
            if pos.size > 0:
                self.stops[d] = self.sell(
                    data=d, size=pos.size,
                    exectype=bt.Order.StopTrail,
                    trailpercent=self.p.trail)

    def next(self):
        month = self.data.datetime.date(0).month
        if month == self.last_month:
            return
        self.last_month = month

        ranked = sorted(self.datas,
                        key=lambda d: self.rocs[d][0], reverse=True)
        targets = [d for d in ranked[:self.p.topk] if self.rocs[d][0] > 0]

        self.log('调仓: [{}]'.format(
            ', '.join(d._name for d in targets) or '空仓'))

        for d in self.datas:
            if d not in targets and self.getposition(d):
                self.cancel_stop(d)      # 先撤止损，再平仓
                self.order_target_percent(data=d, target=0.0)

        if targets:
            weight = (1.0 - self.p.reserve) / len(targets)
            for d in targets:
                self.order_target_percent(data=d, target=weight)


def run_scenario(name, dfs, args, slip=0.0, volperc=0.0, trail=0.0):
    '''按给定摩擦参数跑一次回测，返回绩效指标'''
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)
    cerebro.broker.addcommissioninfo(AStockCommission())

    if slip:
        # 市价单在次日开盘价基础上加/减滑点成交
        cerebro.broker.set_slippage_perc(perc=slip)
    if volperc:
        # 单根 bar 最多成交该 bar 成交量的 volperc%
        cerebro.broker.set_filler(
            bt.broker.fillers.FixedBarPerc(perc=volperc))

    for symbol, df in dfs:
        cerebro.adddata(bt.feeds.PandasData(dataname=df), name=symbol)

    cerebro.addstrategy(MomentumRotationST,
                        momentum=args.momentum,
                        topk=args.topk,
                        trail=trail,
                        printout=args.verbose)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.02,
                        annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', tann=252)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    strat = cerebro.run()[0]
    ret = strat.analyzers.returns.get_analysis()
    sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio')
    dd = strat.analyzers.dd.get_analysis()
    ntrades = strat.analyzers.trades.get_analysis().get(
        'total', {}).get('closed', 0)

    return dict(
        name=name,
        value=cerebro.broker.getvalue(),
        rtot=ret.get('rtot', 0.0),
        rnorm=ret.get('rnorm', 0.0),
        maxdd=dd.max.drawdown / 100,
        sharpe=sharpe,
        ntrades=ntrades,
    )


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

    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    dfs = []
    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        dfs.append((symbol, fetch_stock(symbol, args.fromdate, args.todate)))

    scenarios = [
        ('基准(理想成交)', dict()),
        ('+滑点 {:.2%}'.format(args.slip), dict(slip=args.slip)),
        ('+量限 {:.0f}%/bar'.format(args.volperc), dict(volperc=args.volperc)),
        ('+移动止损 {:.0%}'.format(args.trail), dict(trail=args.trail)),
        ('全开', dict(slip=args.slip, volperc=args.volperc,
                      trail=args.trail)),
    ]

    rows = []
    for name, kw in scenarios:
        print('回测场景: {} ...'.format(name))
        rows.append(run_scenario(name, dfs, args, **kw))

    print('=' * 78)
    print('{:<18} {:>12} {:>8} {:>8} {:>8} {:>7} {:>5}'.format(
        '场景', '期末资产', '总收益', '年化', '最大回撤', '夏普', '笔数'))
    print('-' * 78)
    for r in rows:
        print('{:<18} {:>12,.0f} {:>7.2%} {:>7.2%} {:>7.2%} {:>7} {:>5}'.format(
            r['name'], r['value'], r['rtot'], r['rnorm'], r['maxdd'],
            '{:.2f}'.format(r['sharpe']) if r['sharpe'] is not None else 'N/A',
            r['ntrades']))
    print('=' * 78)


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy9 - 滑点/量限/止损三大打折器对比')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001,601318,300750,600036',
                        help='候选池 A 股代码，逗号分隔')

    parser.add_argument('--momentum', required=False, type=int, default=20,
                        help='动量回看天数')

    parser.add_argument('--topk', required=False, type=int, default=2,
                        help='持有动量最强的前 K 只')

    parser.add_argument('--slip', required=False, type=float, default=0.001,
                        help='滑点比例（0.001 = 0.1%%）')

    parser.add_argument('--volperc', required=False, type=float, default=10.0,
                        help='单 bar 最大成交量占比（%%）')

    parser.add_argument('--trail', required=False, type=float, default=0.08,
                        help='移动止损回撤比例（0.08 = 8%%）')

    parser.add_argument('--fromdate', required=False, default='2023-01-01',
                        help='起始日期 YYYY-MM-DD')

    parser.add_argument('--todate', required=False, default='2024-12-31',
                        help='结束日期 YYYY-MM-DD')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=1000000, help='初始资金')

    parser.add_argument('--verbose', action='store_true',
                        help='打印逐笔成交与调仓日志')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
