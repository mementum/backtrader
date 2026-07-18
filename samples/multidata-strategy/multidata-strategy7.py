#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# multidata-strategy 改造版之五：optstrategy 参数优化
#
# 把 multidata-strategy6 的动量轮动放进 cerebro.optstrategy 做网格扫描，
# 一次回测所有参数组合，输出按年化收益排序的对比表。
#
# 核心知识点：
#
#   - cerebro.optstrategy(策略, 参数=可迭代对象)：笛卡尔积展开所有组合，
#     替代 addstrategy；数据只需加载一次
#   - cerebro.run() 返回「运行结果的列表的列表」，每个元素对应一组参数
#   - optreturn=True（默认）时返回轻量的 OptReturn 对象：只有 .p（参数）
#     和 .analyzers，没有完整策略实例，省内存
#   - 评估靠 Analyzers：优化时不能靠肉眼看日志，必须用统一指标打分
#
# ⚠️ 参数优化的正确姿势：样本内最优 ≠ 未来最优。扫出来的"最优参数"
# 应该用另一段时间（样本外）验证——本脚本用 --fromdate/--todate 换个
# 区间重跑即可，结果大概率会变脸，这正是要学的一课。
#
#   .venv/bin/python samples/multidata-strategy/multidata-strategy7.py
#   .venv/bin/python samples/multidata-strategy/multidata-strategy7.py --momentum 10,20,30,40,60 --topk 1,2,3
#   .venv/bin/python samples/multidata-strategy/multidata-strategy7.py --fromdate 2020-01-01 --todate 2022-12-31
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import os
import os.path
import sys
import time

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
    '''动量轮动（同 multidata-strategy6，优化场景默认不打日志）'''

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


def runstrat(pargs=None):
    args = parse_args(pargs)

    momentums = [int(x) for x in args.momentum.split(',')]
    topks = [int(x) for x in args.topk.split(',')]

    cerebro = bt.Cerebro(maxcpus=args.maxcpus)
    cerebro.broker.set_cash(args.cash)
    cerebro.broker.addcommissioninfo(AStockCommission())

    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    for symbol in symbols:
        print('正在从 AKShare 拉取 {} 的日线数据...'.format(symbol))
        df = fetch_stock(symbol, args.fromdate, args.todate)
        cerebro.adddata(bt.feeds.PandasData(dataname=df), name=symbol)

    # optstrategy 替代 addstrategy：参数传可迭代对象，自动做笛卡尔积
    cerebro.optstrategy(MomentumRotation,
                        momentum=momentums,
                        topk=topks)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.02,
                        annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns', tann=252)

    ncombo = len(momentums) * len(topks)
    print('开始优化：momentum={} × topk={}，共 {} 组...'.format(
        momentums, topks, ncombo))
    tstart = time.time()
    stratruns = cerebro.run()
    print('优化完成，耗时 {:.1f} 秒'.format(time.time() - tstart))

    # 收集每组参数的绩效指标
    rows = []
    for run in stratruns:
        for strat in run:  # optreturn=True 时是轻量 OptReturn 对象
            ret = strat.analyzers.returns.get_analysis()
            sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio')
            dd = strat.analyzers.dd.get_analysis()
            sqn = strat.analyzers.sqn.get_analysis()
            rows.append(dict(
                momentum=strat.p.momentum,
                topk=strat.p.topk,
                rnorm=ret.get('rnorm', 0.0),
                rtot=ret.get('rtot', 0.0),
                sharpe=sharpe if sharpe is not None else float('-inf'),
                maxdd=dd.max.drawdown / 100,
                sqn=sqn.get('sqn', 0.0),
                ntrades=sqn.get('trades', 0),
            ))

    rows.sort(key=lambda r: r['rnorm'], reverse=True)

    print('=' * 72)
    print('{:>8} {:>5} {:>9} {:>9} {:>7} {:>8} {:>6} {:>5}'.format(
        'momentum', 'topk', '年化', '总收益', '夏普', '最大回撤', 'SQN', '笔数'))
    print('-' * 72)
    for r in rows:
        print('{:>8} {:>5} {:>8.2%} {:>8.2%} {:>7} {:>8.2%} {:>6.2f} {:>5}'.format(
            r['momentum'], r['topk'], r['rnorm'], r['rtot'],
            '{:.2f}'.format(r['sharpe']) if r['sharpe'] != float('-inf') else 'N/A',
            r['maxdd'], r['sqn'], r['ntrades']))
    print('=' * 72)
    print('提示：换一段时间（--fromdate/--todate）重跑，'
          '看排名是否稳定——不稳定说明在过拟合。')


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='multidata-strategy7 - 动量轮动参数优化（optstrategy）')

    parser.add_argument('--symbols', required=False,
                        default='600519,000001,601318,300750,600036',
                        help='候选池 A 股代码，逗号分隔')

    parser.add_argument('--momentum', required=False, default='10,20,40,60',
                        help='动量回看天数候选，逗号分隔')

    parser.add_argument('--topk', required=False, default='1,2,3',
                        help='持仓数候选，逗号分隔')

    parser.add_argument('--maxcpus', required=False, type=int, default=1,
                        help='优化并行进程数（macOS 下多进程可能有兼容问题，'
                             '默认单进程）')

    parser.add_argument('--fromdate', required=False, default='2023-01-01',
                        help='起始日期 YYYY-MM-DD')

    parser.add_argument('--todate', required=False, default='2024-12-31',
                        help='结束日期 YYYY-MM-DD')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=1000000, help='初始资金')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
