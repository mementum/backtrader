#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之十：多因子选股
#
# 这是 strategy6「单一动量排序」的自然扩展：
#
#   1. 每只股票先计算时间序列因子
#      - momentum: 过去 N 日收益，越高越好
#      - trend: 当前价格相对长期均线的位置，越高越好
#      - volatility: 日收益波动率，越低越好
#   2. 每个调仓日对所有股票做横截面 robust z-score
#   3. 将标准化后的因子按权重合成为总分
#   4. 持有总分最高且动量为正的 topk 只股票
#
# 这里使用价格类因子，是为了让示例可以直接运行。接入 PE、ROE 等基本面
# 因子时，交易与排名部分无需变化，只需给 PandasData 增加自定义 lines。
#
# 所有信号只读取 [0] 和负索引历史数据。默认 Market 订单在下一根 bar 成交，
# 避免用未来价格计算当期信号。
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import math
import os
import os.path
import sys

os.environ['NO_PROXY'] = '*'

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import akshare as ak
import numpy as np
import pandas as pd

import backtrader as bt


class AStockCommission(bt.CommInfoBase):
    """A 股费率：双边佣金、最低 5 元、卖出单边印花税。"""

    params = dict(
        commission=0.00025,
        stamp_duty=0.0005,
        min_comm=5.0,
        stocklike=True,
        commtype=bt.CommInfoBase.COMM_PERC,
    )

    def _getcommission(self, size, price, pseudoexec):
        comm = max(abs(size) * price * self.p.commission, self.p.min_comm)
        if size < 0:
            comm += abs(size) * price * self.p.stamp_duty
        return comm


def robust_zscore(values, clip=3.0):
    """用中位数和 MAD 做截面标准化，并限制极端值。"""
    arr = np.asarray(values, dtype=float)
    median = np.median(arr)
    scale = np.median(np.abs(arr - median)) * 1.4826

    if scale < 1e-12:
        scale = np.std(arr)
    if scale < 1e-12:
        return np.zeros_like(arr)

    return np.clip((arr - median) / scale, -clip, clip)


class MultiFactorSelection(bt.Strategy):
    """月度多因子选股：截面标准化后加权打分，等权持有前 K 名。"""

    params = dict(
        momentum=60,
        trend=120,
        volatility=20,
        topk=2,
        momentum_weight=0.5,
        trend_weight=0.2,
        lowvol_weight=0.3,
        reserve=0.05,
        printout=True,
    )

    def __init__(self):
        self.factors = {}
        for data in self.datas:
            daily_return = bt.ind.PercentChange(data.close, period=1)
            trend_ma = bt.ind.SMA(data.close, period=self.p.trend)
            self.factors[data] = dict(
                momentum=bt.ind.ROC(data.close, period=self.p.momentum),
                trend=data.close / trend_ma - 1.0,
                volatility=bt.ind.StdDev(
                    daily_return, period=self.p.volatility),
            )

        self.last_rebalance = None

    def log(self, text):
        if self.p.printout:
            print('{} {}'.format(self.datetime.date(0), text))

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

    def next(self):
        current_date = self.datetime.date(0)
        year_month = (current_date.year, current_date.month)
        if year_month == self.last_rebalance:
            return
        self.last_rebalance = year_month

        rows = self._collect_factor_rows(current_date)
        if len(rows) < 2:
            self.log('可用股票不足 2 只，本月跳过')
            return

        self._score_rows(rows)
        rows.sort(key=lambda row: row['score'], reverse=True)

        candidates = [row for row in rows if row['momentum'] > 0]
        targets = [row['data'] for row in candidates[:self.p.topk]]

        self.log('因子排名:')
        for rank, row in enumerate(rows, 1):
            self.log(
                '  {:>2}. {} score={:+.2f} '
                'mom={:+.1%} trend={:+.1%} vol={:.1%}'.format(
                    rank,
                    row['data']._name,
                    row['score'],
                    row['momentum'],
                    row['trend'],
                    row['volatility'] * math.sqrt(252)))

        self.log('目标持仓: [{}]'.format(
            ', '.join(data._name for data in targets) or '空仓'))

        for data in self.datas:
            if data not in targets and self.getposition(data):
                self.order_target_percent(data=data, target=0.0)

        if targets:
            target_weight = (1.0 - self.p.reserve) / len(targets)
            for data in targets:
                self.order_target_percent(
                    data=data, target=target_weight)

    def _collect_factor_rows(self, current_date):
        rows = []
        for data in self.datas:
            # 数据停牌或不同步时，不拿旧值参与当日横截面排名。
            if not len(data) or data.datetime.date(0) != current_date:
                continue

            values = {
                name: float(line[0])
                for name, line in self.factors[data].items()
            }
            if not all(math.isfinite(value) for value in values.values()):
                continue

            values['data'] = data
            rows.append(values)
        return rows

    def _score_rows(self, rows):
        directions = {
            'momentum': 1.0,
            'trend': 1.0,
            'volatility': -1.0,
        }
        weights = {
            'momentum': self.p.momentum_weight,
            'trend': self.p.trend_weight,
            'volatility': self.p.lowvol_weight,
        }

        total_weight = sum(abs(weight) for weight in weights.values())
        if total_weight <= 0:
            raise ValueError('因子权重之和必须大于 0')

        for row in rows:
            row['score'] = 0.0

        for name in ('momentum', 'trend', 'volatility'):
            normalized = robust_zscore([row[name] for row in rows])
            for row, zscore in zip(rows, normalized):
                contribution = (
                    directions[name] * weights[name] * float(zscore)
                    / total_weight)
                row[name + '_z'] = float(zscore)
                row['score'] += contribution


def print_report(cerebro, result, args):
    strat = result[0]
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.dd.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    returns = strat.analyzers.returns.get_analysis()

    total = trades.get('total', {}).get('closed', 0)
    won = trades.get('won', {}).get('total', 0)

    print('=' * 58)
    print('绩效报告（多因子 / 持有前 {} 名）'.format(args.topk))
    print('-' * 58)
    print('期末资产:     {:,.2f}'.format(cerebro.broker.getvalue()))
    total_return = math.expm1(returns.get('rtot', 0.0))
    print('总收益率:     {:.2%}'.format(total_return))
    print('年化收益率:   {:.2%}'.format(returns.get('rnorm', 0.0)))
    print('最大回撤:     {:.2%}'.format(drawdown.max.drawdown / 100))
    print('夏普比率:     {}'.format(
        '{:.3f}'.format(sharpe['sharperatio'])
        if sharpe.get('sharperatio') is not None else 'N/A'))
    if total:
        print('胜率:         {:.1%}（{}/{}）'.format(won / total, won, total))
    print('=' * 58)


def fetch_eastmoney(symbol, fromdate, todate):
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
    prefix = 'sh' if symbol.startswith(('5', '6', '9')) else 'sz'
    return ak.stock_zh_a_daily(
        symbol=prefix + symbol,
        start_date=fromdate.replace('-', ''),
        end_date=todate.replace('-', ''),
        adjust='qfq')


def normalize(df, symbol):
    if df is None or df.empty:
        raise SystemExit('未获取到 {} 的数据，请检查代码或网络'.format(symbol))
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    return df[['open', 'high', 'low', 'close', 'volume']]


def fetch_stock(symbol, fromdate, todate):
    try:
        df = fetch_eastmoney(symbol, fromdate, todate)
    except Exception as exc:
        print('{} 东财源获取失败（{}），改用新浪源...'.format(
            symbol, type(exc).__name__))
        df = fetch_sina(symbol, fromdate, todate)
    return normalize(df, symbol)


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)
    cerebro.broker.addcommissioninfo(AStockCommission())

    symbols = [item.strip() for item in args.symbols.split(',')
               if item.strip()]
    if len(symbols) < 2:
        raise SystemExit('多因子选股至少需要 2 个标的')

    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        frame = fetch_stock(symbol, args.fromdate, args.todate)
        print('{} 获取 {} 根 K 线（{} ~ {}）'.format(
            symbol, len(frame),
            frame.index[0].date(), frame.index[-1].date()))
        cerebro.adddata(bt.feeds.PandasData(dataname=frame), name=symbol)

    cerebro.addstrategy(
        MultiFactorSelection,
        momentum=args.momentum,
        trend=args.trend,
        volatility=args.volatility,
        topk=args.topk,
        momentum_weight=args.momentum_weight,
        trend_weight=args.trend_weight,
        lowvol_weight=args.lowvol_weight,
        printout=not args.quiet)

    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        _name='sharpe',
        timeframe=bt.TimeFrame.Days,
        riskfreerate=0.02,
        annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', tann=252)

    result = cerebro.run(runonce=not args.runnext)
    print_report(cerebro, result, args)

    if args.plot:
        cerebro.plot(style='candle')


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy12 - 多因子选股')

    parser.add_argument(
        '--symbols',
        default='600519,000001,601318,300750,600036',
        help='候选池 A 股代码，逗号分隔')
    parser.add_argument('--momentum', type=int, default=60,
                        help='动量因子回看天数')
    parser.add_argument('--trend', type=int, default=120,
                        help='趋势因子均线天数')
    parser.add_argument('--volatility', type=int, default=20,
                        help='波动率因子回看天数')
    parser.add_argument('--topk', type=int, default=2,
                        help='持有综合得分最高的前 K 只')
    parser.add_argument('--momentum-weight', type=float, default=0.5)
    parser.add_argument('--trend-weight', type=float, default=0.2)
    parser.add_argument('--lowvol-weight', type=float, default=0.3)
    parser.add_argument('--fromdate', default='2020-01-01')
    parser.add_argument('--todate', default='2024-12-31')
    parser.add_argument('--cash', type=float, default=1000000)
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--runnext', action='store_true',
                        help='逐 bar 计算指标，用于和默认 runonce 对照')
    parser.add_argument('--plot', action='store_true')
    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
