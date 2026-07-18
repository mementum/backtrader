#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# sigsmacross 的本地数据版本
#
# 原版 sigsmacross.py 依赖 Yahoo 在线接口（已失效），本版本改用仓库自带的
# datas/ 目录下的 CSV 数据，克隆仓库后可直接运行：
#
#   python sigsmacross3.py
#   python sigsmacross3.py --strat sma1=5,sma2=30
#   python sigsmacross3.py --data ../../datas/nvda-1999-2014.txt --plot
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import os.path
import sys

# 未 pip 安装 backtrader 时，直接使用仓库根目录下的源码
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import backtrader as bt

# 默认数据文件：相对本脚本定位，保证在任意目录下运行都能找到
DEFAULT_DATA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'datas', 'yhoo-1996-2014.txt')

# datas/nvda-1999-2014.txt
# yhoo-1996-2014.txt


class SmaCross(bt.SignalStrategy):
    params = dict(sma1=10, sma2=20)

    def notify_order(self, order):
        if not order.alive():
            print('{} {} {}@{}'.format(
                bt.num2date(order.executed.dt),
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price)
            )

    def notify_trade(self, trade):
        if trade.isclosed:
            print('profit {}'.format(trade.pnlcomm))

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.params.sma1)
        sma2 = bt.ind.SMA(period=self.params.sma2)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)

    # 本地 Yahoo 格式 CSV，替代原版的在线下载
    data0 = bt.feeds.YahooFinanceCSVData(
        dataname=args.data,
        fromdate=datetime.datetime.strptime(args.fromdate, '%Y-%m-%d'),
        todate=datetime.datetime.strptime(args.todate, '%Y-%m-%d'))
    cerebro.adddata(data0)

    cerebro.addstrategy(SmaCross, **(eval('dict(' + args.strat + ')')))
    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)

    cerebro.run()
    print('期末资产: {:.2f}'.format(cerebro.broker.getvalue()))

    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='sigsmacross3 - 使用本地 CSV 数据的双均线信号策略')

    parser.add_argument('--data', required=False, default=DEFAULT_DATA,
                        help='Yahoo 格式 CSV 数据文件路径')

    parser.add_argument('--fromdate', required=False, default='2011-01-01',
                        help='起始日期 YYYY-MM-DD')

    parser.add_argument('--todate', required=False, default='2012-12-31',
                        help='结束日期 YYYY-MM-DD')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=10000, help='初始资金')

    parser.add_argument('--stake', required=False, action='store', type=int,
                        default=1, help='每笔交易股数')

    parser.add_argument('--strat', required=False, action='store', default='',
                        help='策略参数，如: sma1=5,sma2=30')

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help='绘图并可传入 kwargs，如: --plot style="candle"')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
