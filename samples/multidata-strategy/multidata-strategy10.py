#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之八：Benchmark——策略到底跑没跑赢躺平？
#
# 给 multidata-strategy6 的动量轮动加上基准对比（买入持有上证指数）：
#
#   1. bt.observers.Benchmark —— 观察器：逐 bar 记录策略收益与基准收益
#      两条曲线，--plot 时画在同一子图，肉眼可见何时跑赢/跑输
#   2. bt.analyzers.TimeReturn 的 data= 参数 —— 同一个分析器类，
#      不传 data 算的是"策略组合"的收益，传 data=指数 算的就是
#      "买入持有该指数"的收益；两个一减就是超额收益（alpha 的朴素版）
#
# 观察器 vs 分析器：Observer 也是 lines 对象，逐 bar 记录、主要为画图；
# Analyzer 结束时给统计结果、主要为报表。两者常配套使用。
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy10.py
#   .venv/bin/python samples/multidata-strategy/multidata-strategy10.py --plot
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
    '''动量轮动（同 multidata-strategy6）

    约定：最后一个数据源是基准指数，只用于对比，不参与轮动。
    '''

    params = dict(
        momentum=20,     # 动量回看天数
        topk=2,          # 持有最强的前 K 只
        reserve=0.05,    # 预留现金比例
        printout=False,
    )

    def __init__(self):
        self.stocks = self.datas[:-1]    # 最后一个是基准指数
        self.rocs = {d: bt.ind.ROC(d, period=self.p.momentum)
                     for d in self.stocks}
        self.last_month = None

    def next(self):
        month = self.data.datetime.date(0).month
        if month == self.last_month:
            return
        self.last_month = month

        ranked = sorted(self.stocks,
                        key=lambda d: self.rocs[d][0], reverse=True)
        targets = [d for d in ranked[:self.p.topk] if self.rocs[d][0] > 0]

        if self.p.printout:
            print('{} 调仓: [{}]'.format(
                self.data.datetime.date(0),
                ', '.join(d._name for d in targets) or '空仓'))

        for d in self.stocks:
            if d not in targets and self.getposition(d):
                self.order_target_percent(data=d, target=0.0)

        if targets:
            weight = (1.0 - self.p.reserve) / len(targets)
            for d in targets:
                self.order_target_percent(data=d, target=weight)


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
    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        df = fetch_stock(symbol, args.fromdate, args.todate)
        cerebro.adddata(bt.feeds.PandasData(dataname=df), name=symbol)

    # 基准指数：最后加入，参与对比但不参与轮动
    print('正在从 AKShare 拉取基准指数 {} ...'.format(args.benchmark))
    dfi = fetch_index(args.benchmark, args.fromdate, args.todate)
    benchdata = bt.feeds.PandasData(dataname=dfi, name=args.benchmark)
    cerebro.adddata(benchdata)

    cerebro.addstrategy(MomentumRotation,
                        momentum=args.momentum,
                        topk=args.topk,
                        printout=args.verbose)

    # 观察器：策略收益 vs 基准收益两条曲线（--plot 时可见）
    cerebro.addobserver(bt.observers.Benchmark,
                        data=benchdata,
                        timeframe=bt.TimeFrame.NoTimeFrame)

    # 分析器：TimeReturn 不传 data = 算策略；传 data=基准 = 算买入持有
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='port_total',
                        timeframe=bt.TimeFrame.NoTimeFrame)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='bench_total',
                        data=benchdata,
                        timeframe=bt.TimeFrame.NoTimeFrame)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='port_yearly',
                        timeframe=bt.TimeFrame.Years)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='bench_yearly',
                        data=benchdata,
                        timeframe=bt.TimeFrame.Years)

    strat = cerebro.run()[0]

    # NoTimeFrame 的结果只有一个键值对：{起始日: 总收益}
    port_total = list(strat.analyzers.port_total.get_analysis().values())[0]
    bench_total = list(strat.analyzers.bench_total.get_analysis().values())[0]
    port_yearly = strat.analyzers.port_yearly.get_analysis()
    bench_yearly = strat.analyzers.bench_yearly.get_analysis()

    print('=' * 56)
    print('{:<10} {:>12} {:>14} {:>12}'.format(
        '年份', '策略', '基准(买入持有)', '超额'))
    print('-' * 56)
    for dt, pret in port_yearly.items():
        bret = bench_yearly.get(dt, 0.0)
        print('{:<10} {:>11.2%} {:>13.2%} {:>11.2%}'.format(
            dt.year, pret, bret, pret - bret))
    print('-' * 56)
    print('{:<10} {:>11.2%} {:>13.2%} {:>11.2%}'.format(
        '总计', port_total, bench_total, port_total - bench_total))
    print('=' * 56)
    print('期末资产: {:,.2f}'.format(cerebro.broker.getvalue()))

    if args.plot:
        cerebro.plot(style='candle')


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy10 - 动量轮动 vs 买入持有基准')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001,601318,300750,600036',
                        help='候选池 A 股代码，逗号分隔')

    parser.add_argument('--benchmark', required=False, default='sh000001',
                        help='基准指数代码（新浪格式），如 sh000001 上证指数、'
                             'sh000300 沪深300')

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

    parser.add_argument('--verbose', action='store_true',
                        help='打印每月调仓日志')

    parser.add_argument('--plot', '-p', action='store_true',
                        help='绘图（含策略 vs 基准收益曲线子图）')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
