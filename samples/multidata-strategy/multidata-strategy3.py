#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 的改造版：多标的各自独立跑双均线
#
# 与原版 multidata-strategy.py（用 data1 的信号交易 data0）不同，本版本
# 每个标的用自己的均线交叉信号、独立开平仓，互不干扰。核心知识点：
#
#   - for d in self.datas 遍历所有数据源，指标按数据各建一份
#   - self.getposition(d) 查询指定标的的持仓（self.position 只看 data0）
#   - 下单时用 data=d 指定交易哪个标的
#   - cerebro.adddata(data, name=...) 给数据命名，日志才分得清谁是谁
#
# 数据用 AKShare 在线拉取（前复权日线，东财失败自动切新浪源）：
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy3.py
#   .venv/bin/python samples/multidata-strategy/multidata-strategy3.py --symbols 600519,000001,601318
#   .venv/bin/python samples/multidata-strategy/multidata-strategy3.py --strat sma1=5,sma2=30
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


class MultiSmaCross(bt.Strategy):
    '''多标的独立双均线：每个数据源各建一组 SMA 交叉信号，各自开平仓'''

    params = dict(sma1=10, sma2=20, stake=100)

    def __init__(self):
        # 每个数据源一份信号，顺序与 self.datas 一致
        self.signals = []
        for d in self.datas:
            sma1 = bt.ind.SMA(d, period=self.p.sma1)
            sma2 = bt.ind.SMA(d, period=self.p.sma2)
            self.signals.append(bt.ind.CrossOver(sma1, sma2))

    def log(self, txt):
        print('{} {}'.format(self.data.datetime.date(0), txt))

    def notify_order(self, order):
        if order.status == order.Completed:
            self.log('{} {} {}@{:.2f}'.format(
                order.data._name,
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price))
        elif not order.alive():
            # 订单未成交（如 Margin 资金不足、Rejected 被拒），打印原因
            self.log('{} 订单未成交: {}'.format(
                order.data._name, order.getstatusname()))

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log('{} profit {:.2f}'.format(trade.data._name, trade.pnlcomm))

    def next(self):
        for i, d in enumerate(self.datas):
            pos = self.getposition(d)
            if not pos and self.signals[i] > 0:      # 金叉且空仓 → 买入
                self.buy(data=d, size=self.p.stake)
            elif pos and self.signals[i] < 0:        # 死叉且持仓 → 平仓
                self.close(data=d)

    def stop(self):
        print('=' * 50)
        for d in self.datas:
            pos = self.getposition(d)
            if pos:
                print('{} 期末持仓 {} 股 @ {:.2f}'.format(
                    d._name, pos.size, pos.price))
        print('期末资产: {:.2f}'.format(self.broker.getvalue()))


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
    """用 AKShare 拉取 A 股日线（前复权），东财失败自动降级到新浪源"""
    try:
        df = fetch_eastmoney(symbol, fromdate, todate)
    except Exception as e:
        print('{} 东财源获取失败（{}），改用新浪源...'.format(
            symbol, type(e).__name__))
        df = fetch_sina(symbol, fromdate, todate)

    if df is None or df.empty:
        raise SystemExit('未获取到 {} 的数据，请检查代码或网络'.format(symbol))

    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    return df[['open', 'high', 'low', 'close', 'volume']]


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)

    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        df = fetch_data(symbol, args.fromdate, args.todate)
        print('{} 获取 {} 根 K 线（{} ~ {}）'.format(
            symbol, len(df), df.index[0].date(), df.index[-1].date()))
        # name 参数给数据命名，订单/成交日志用它区分标的
        cerebro.adddata(bt.feeds.PandasData(dataname=df), name=symbol)

    cerebro.addstrategy(MultiSmaCross,
                        stake=args.stake,
                        **(eval('dict(' + args.strat + ')')))

    cerebro.run()

    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy3 - 多标的各自独立跑双均线（AKShare 数据）')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001',
                        help='A 股代码，逗号分隔，如: 600519,000001,601318')

    parser.add_argument('--fromdate', required=False, default='2023-01-01',
                        help='起始日期 YYYY-MM-DD')

    parser.add_argument('--todate', required=False, default='2024-12-31',
                        help='结束日期 YYYY-MM-DD')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=1000000, help='初始资金')

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
