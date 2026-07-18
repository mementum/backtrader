#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之二：多标的独立双均线 + 指数择时过滤
#
# 在 multidata-strategy3.py（每个标的独立跑双均线）的基础上，加入大盘
# 择时开关：
#
#   - 指数收盘价站上其均线（默认 20 日）→ 允许个股按各自信号开仓
#   - 指数跌破均线 → 禁止开新仓，并立即清掉所有持仓（空仓避险）
#
# 核心知识点（在 multidata-strategy3 之上新增）：
#
#   - 指数作为一个"只用来算信号、从不交易"的数据源加入 cerebro
#   - 约定 self.datas[-1] 是指数，self.datas[:-1] 是可交易的个股
#
# 数据用 AKShare 在线拉取（个股：东财失败自动切新浪；指数：新浪源）：
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy4.py
#   .venv/bin/python samples/multidata-strategy/multidata-strategy4.py --symbols 600519,000001,601318
#   .venv/bin/python samples/multidata-strategy/multidata-strategy4.py --index-period 60
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


class IndexFilterSmaCross(bt.Strategy):
    '''多标的独立双均线 + 指数择时

    约定：最后一个数据源（self.datas[-1]）是指数，只算信号不交易；
    其余数据源是可交易的个股。
    '''

    params = dict(sma1=10, sma2=20, index_period=20, stake=100)

    def __init__(self):
        self.stocks = self.datas[:-1]
        self.index = self.datas[-1]

        # 每只个股一组独立的均线交叉信号
        self.signals = []
        for d in self.stocks:
            sma1 = bt.ind.SMA(d, period=self.p.sma1)
            sma2 = bt.ind.SMA(d, period=self.p.sma2)
            self.signals.append(bt.ind.CrossOver(sma1, sma2))

        # 指数择时开关：收盘价在均线上方为 True
        self.index_sma = bt.ind.SMA(self.index, period=self.p.index_period)

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
        bullish = self.index.close[0] > self.index_sma[0]

        if not bullish:
            # 大盘走弱：清掉所有持仓，不再开新仓
            for d in self.stocks:
                if self.getposition(d):
                    self.log('{} 大盘跌破均线，清仓避险'.format(d._name))
                    self.close(data=d)
            return

        for i, d in enumerate(self.stocks):
            pos = self.getposition(d)
            if not pos and self.signals[i] > 0:      # 大盘走强 + 金叉 → 买入
                self.buy(data=d, size=self.p.stake)
            elif pos and self.signals[i] < 0:        # 死叉 → 平仓
                self.close(data=d)

    def stop(self):
        print('=' * 50)
        for d in self.stocks:
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

    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        df = fetch_stock(symbol, args.fromdate, args.todate)
        print('{} 获取 {} 根 K 线（{} ~ {}）'.format(
            symbol, len(df), df.index[0].date(), df.index[-1].date()))
        cerebro.adddata(bt.feeds.PandasData(dataname=df), name=symbol)

    # 指数必须最后加入——策略里约定 self.datas[-1] 是指数
    print('正在从 AKShare 拉取指数 {} 的日线数据...'.format(args.index))
    dfi = fetch_index(args.index, args.fromdate, args.todate)
    print('{} 获取 {} 根 K 线（{} ~ {}）'.format(
        args.index, len(dfi), dfi.index[0].date(), dfi.index[-1].date()))
    cerebro.adddata(bt.feeds.PandasData(dataname=dfi), name=args.index)

    cerebro.addstrategy(IndexFilterSmaCross,
                        index_period=args.index_period,
                        stake=args.stake,
                        **(eval('dict(' + args.strat + ')')))

    cerebro.run()

    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy4 - 多标的双均线 + 指数择时过滤（AKShare 数据）')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001',
                        help='A 股代码，逗号分隔，如: 600519,000001,601318')

    parser.add_argument('--index', required=False, default='sh000001',
                        help='择时用指数代码（新浪格式），如: sh000001 上证指数、sz399001 深证成指')

    parser.add_argument('--index-period', required=False, type=int, default=20,
                        help='指数择时均线周期')

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
