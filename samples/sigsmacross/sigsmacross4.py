#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# sigsmacross 的 AKShare 数据版本
#
# 用 AKShare 在线拉取 A 股日线数据（前复权），转成 pandas DataFrame 后
# 通过 bt.feeds.PandasData 喂给 backtrader 跑双均线信号策略。
#
# 依赖：pip install akshare（本仓库 .venv 已安装，可直接用）
#
#   .venv/bin/python samples/sigsmacross/sigsmacross4.py
#   .venv/bin/python samples/sigsmacross/sigsmacross4.py --symbol 000001
#   .venv/bin/python samples/sigsmacross/sigsmacross4.py --strat sma1=5,sma2=30 --plot
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


class SmaCross(bt.SignalStrategy):
    params = dict(sma1=10, sma2=20)

    def notify_order(self, order):
        if order.status == order.Completed:
            print('{} {} {}@{}'.format(
                bt.num2date(order.executed.dt),
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price)
            )
        elif not order.alive():
            # 订单未成交（如 Margin 资金不足、Rejected 被拒），打印原因
            print('{} 订单未成交: {}'.format(
                self.data.datetime.date(0), order.getstatusname()))

    def notify_trade(self, trade):
        if trade.isclosed:
            print('profit {}'.format(trade.pnlcomm))

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.params.sma1)
        sma2 = bt.ind.SMA(period=self.params.sma2)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


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


def fetch_data(symbol, fromdate, todate):
    """用 AKShare 拉取 A 股日线（前复权），转成 backtrader 可用的 DataFrame

    优先使用东财源；部分网络环境下东财会拒绝 python 的请求，此时自动
    降级到新浪源。
    """
    try:
        df = fetch_eastmoney(symbol, fromdate, todate)
    except Exception as e:
        print('东财源获取失败（{}），改用新浪源...'.format(type(e).__name__))
        df = fetch_sina(symbol, fromdate, todate)

    if df is None or df.empty:
        raise SystemExit('未获取到 {} 的数据，请检查代码或网络'.format(symbol))

    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    return df[['open', 'high', 'low', 'close', 'volume']]


def runstrat(pargs=None):
    args = parse_args(pargs)

    print('正在从 AKShare 拉取 {} 的日线数据...'.format(args.symbol))
    df = fetch_data(args.symbol, args.fromdate, args.todate)
    print('获取 {} 根 K 线（{} ~ {}）'.format(
        len(df), df.index[0].date(), df.index[-1].date()))

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)

    data0 = bt.feeds.PandasData(dataname=df)
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
        description='sigsmacross4 - 用 AKShare 拉取 A 股数据的双均线信号策略')

    parser.add_argument('--symbol', required=False, default='600519',
                        help='A 股代码，如 600519（贵州茅台）、000001（平安银行）')

    parser.add_argument('--fromdate', required=False, default='2023-01-01',
                        help='起始日期 YYYY-MM-DD')

    parser.add_argument('--todate', required=False, default='2024-12-31',
                        help='结束日期 YYYY-MM-DD')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=1000000, help='初始资金（默认 100 万，够买一手茅台）')

    parser.add_argument('--stake', required=False, action='store', type=int,
                        default=100, help='每笔交易股数（A 股一手为 100 股）')

    parser.add_argument('--strat', required=False, action='store', default='',
                        help='策略参数，如: sma1=5,sma2=30')

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help='绘图并可传入 kwargs，如: --plot style="candle"')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
