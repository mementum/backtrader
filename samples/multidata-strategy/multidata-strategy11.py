#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之九：PyFolio 分析器 + quantstats 专业报告
#
# 把回测结果导出成一份完整的 HTML 绩效报告（收益曲线、回撤、月度热力图、
# 滚动夏普、分布直方图等几十项指标，含基准对比）。链路：
#
#   bt.analyzers.PyFolio  ——  backtrader 官方分析器，把回测过程整理成
#     4 个 pandas 对象：日收益、持仓、成交、杠杆。它本是为 pyfolio
#     设计的，但 pyfolio 已停止维护多年（与新版 pandas 不兼容）
#   quantstats  ——  pyfolio 的现代替代品，只需要日收益序列就能出报告，
#     正好接住 PyFolio 分析器输出的第一项
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy11.py
#   打开生成的 quantstats-report.html 查看完整报告
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
import quantstats as qs

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
    '''动量轮动（同 multidata-strategy6）'''

    params = dict(
        momentum=20,     # 动量回看天数
        topk=2,          # 持有最强的前 K 只
        reserve=0.05,    # 预留现金比例
    )

    def __init__(self):
        self.rocs = {d: bt.ind.ROC(d, period=self.p.momentum)
                     for d in self.datas}
        self.last_month = None

    def next(self):
        month = self.data.datetime.date(0).month
        if month == self.last_month:
            return
        self.last_month = month

        ranked = sorted(self.datas,
                        key=lambda d: self.rocs[d][0], reverse=True)
        targets = [d for d in ranked[:self.p.topk] if self.rocs[d][0] > 0]

        for d in self.datas:
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

    cerebro.addstrategy(MomentumRotation,
                        momentum=args.momentum,
                        topk=args.topk)

    # PyFolio 分析器：把回测整理成 pandas 对象
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    strat = cerebro.run()[0]
    print('期末资产: {:,.2f}'.format(cerebro.broker.getvalue()))

    # ---- 提取 4 个 pandas 对象 ----
    returns, positions, transactions, gross_lev = \
        strat.analyzers.pyfolio.get_pf_items()
    # PyFolio 输出的索引带 UTC 时区，quantstats 需要朴素时间戳
    returns.index = returns.index.tz_convert(None)

    print('日收益序列: {} 天；成交记录: {} 笔'.format(
        len(returns), len(transactions)))

    # ---- 基准：买入持有指数的日收益 ----
    print('正在拉取基准指数 {} ...'.format(args.benchmark))
    dfi = fetch_index(args.benchmark, args.fromdate, args.todate)
    bench = dfi['close'].pct_change().fillna(0.0)
    bench.name = args.benchmark

    # ---- 控制台摘要 ----
    print('=' * 46)
    print('quantstats 摘要（vs {}）'.format(args.benchmark))
    print('-' * 46)
    for label, fn in [('CAGR 年化', qs.stats.cagr),
                      ('夏普', qs.stats.sharpe),
                      ('索提诺', qs.stats.sortino),
                      ('最大回撤', qs.stats.max_drawdown),
                      ('波动率(年化)', qs.stats.volatility)]:
        print('{:<12} 策略 {:>8.2%}   基准 {:>8.2%}'.format(
            label, float(fn(returns)), float(fn(bench)))
            if label in ('CAGR 年化', '最大回撤', '波动率(年化)') else
            '{:<12} 策略 {:>8.2f}   基准 {:>8.2f}'.format(
                label, float(fn(returns)), float(fn(bench))))
    print('=' * 46)

    # ---- HTML 完整报告 ----
    out = os.path.abspath(args.output)
    qs.reports.html(returns, benchmark=bench, output=out,
                    title='动量轮动 vs {}'.format(args.benchmark))
    print('HTML 报告已生成: {}'.format(out))


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy11 - PyFolio 分析器 + quantstats 报告')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001,601318,300750,600036',
                        help='候选池 A 股代码，逗号分隔')

    parser.add_argument('--benchmark', required=False, default='sh000001',
                        help='基准指数代码（新浪格式）')

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

    parser.add_argument('--output', required=False,
                        default='quantstats-report.html',
                        help='HTML 报告输出路径')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
