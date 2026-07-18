#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# 自定义 Indicator 教学示例
#
# 两个指标覆盖自定义指标的两种写法：
#
#   1. Bias（乖离率）—— 纯声明式：__init__ 里用 lines 运算符搭好计算图，
#      一行搞定，连 next() 都不用写（stage1 运算符重载的实际应用）
#   2. Streak（连涨/连跌天数）—— 递归指标：当前值依赖自己上一格的值，
#      声明式表达不了，必须写 next()；同时给出 once() 向量化实现，
#      演示直接操作 LineBuffer 底层数组
#
# 顺带演示 plotinfo / plotlines 控制画图效果。
#
# 数据用仓库自带 CSV，无需网络：
#
#   python3 samples/custom-indicator/custom-indicator.py
#   python3 samples/custom-indicator/custom-indicator.py --plot
#   python3 samples/custom-indicator/custom-indicator.py --runnext   # 强制逐 bar 模式（走 next 而非 once）
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import os.path
import sys

# 未 pip 安装 backtrader 时，直接使用仓库根目录下的源码
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import backtrader as bt

DEFAULT_DATA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'datas', '2005-2006-day-001.txt')


class Bias(bt.Indicator):
    '''乖离率：收盘价偏离 N 日均线的百分比

    纯声明式指标——__init__ 里的算式都是 lines 对象间的运算（stage1），
    返回的是"计算图"，引擎每根 bar 自动求值。不需要 next()/once()，
    向量化(runonce)模式下自动享受批量计算。
    '''

    lines = ('bias',)            # 元类读走它，生成 self.lines.bias
    params = dict(period=20)     # 元类读走它，生成 self.p.period

    # 画图控制：subplot=True 画在独立子图（振荡器类指标都该这样）
    plotinfo = dict(subplot=True)
    plotlines = dict(bias=dict(color='blue'))

    def __init__(self):
        sma = bt.ind.SMA(self.data, period=self.p.period)
        # 整行都是 line 运算：除法、减法、乘法全部返回新的 line 对象
        self.lines.bias = (self.data.close / sma - 1.0) * 100.0
        # minperiod 无需手动声明：SMA(period) 的 minperiod 沿计算图自动传播


class Streak(bt.Indicator):
    '''连涨/连跌天数：+3 表示连涨 3 天，-2 表示连跌 2 天

    递归指标——今天的值依赖自己昨天的值，无法用声明式算式表达，
    必须写 next() 逐 bar 计算。
    '''

    lines = ('streak',)

    plotinfo = dict(subplot=True)
    plotlines = dict(streak=dict(_method='bar'))   # 画成柱状

    def __init__(self):
        # 需要比较今昨两天收盘价：告诉引擎第 2 根 bar 起才有值。
        # 声明式指标由计算图自动推导 minperiod，手写 next 的要自己声明
        self.addminperiod(2)

    def next(self):
        '''逐 bar 模式：[0] 是当前格，[-1] 是上一格（含自己的线）

        注意 NaN 陷阱：第一次调用时自己线的 [-1] 是缓冲区初始值 NaN，
        不处理的话 max(NaN,0)+1 == NaN 会污染整条线。递归指标必须
        给初值兜底。
        '''
        prev = self.lines.streak[-1]
        if prev != prev:   # NaN != NaN 为真：还没有前值
            prev = 0.0

        if self.data.close[0] > self.data.close[-1]:
            self.lines.streak[0] = max(prev, 0) + 1
        elif self.data.close[0] < self.data.close[-1]:
            self.lines.streak[0] = min(prev, 0) - 1
        else:
            self.lines.streak[0] = 0

    def once(self, start, end):
        '''向量化模式（可选，纯为提速）：直接操作 LineBuffer 底层数组。

        此时游标机制不参与，用绝对下标读写 array——这正是 lines 课
        讲的 linebuffer 结构：line.array 就是那个完整数组。
        不实现 once() 也能跑，引擎会退化为逐 bar 调 next()。
        '''
        carray = self.data.close.array
        larray = self.lines.streak.array

        prev = 0.0
        for i in range(start, end):
            if carray[i] > carray[i - 1]:
                prev = larray[i] = max(prev, 0) + 1
            elif carray[i] < carray[i - 1]:
                prev = larray[i] = min(prev, 0) - 1
            else:
                prev = larray[i] = 0.0


class DemoStrategy(bt.Strategy):
    '''演示用策略：均值回归——超跌（乖离率深负 + 连跌多日）买入，
    回归（乖离率转正）卖出。重点在展示自定义指标像内置指标一样使用。
    '''

    params = dict(
        bias_buy=-2.5,    # 乖离率低于 -2.5% 视为超跌
        streak_buy=-3,    # 且连跌 3 天以上
        printout=True,
    )

    def __init__(self):
        self.bias = Bias(self.data)        # 自定义指标的用法和内置的没有区别
        self.streak = Streak(self.data)

    def log(self, txt):
        if self.p.printout:
            print('{} {}'.format(self.data.datetime.date(0), txt))

    def next(self):
        if not self.position:
            if (self.bias[0] < self.p.bias_buy and
                    self.streak[0] <= self.p.streak_buy):
                self.log('超跌买入: bias={:.2f}% streak={:.0f}'.format(
                    self.bias[0], self.streak[0]))
                self.buy(size=1)   # 该数据价格 ~3700，1 万本金只买得起 1 份
        elif self.bias[0] > 0:
            self.log('回归卖出: bias={:.2f}%'.format(self.bias[0]))
            self.close()

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log('平仓 净利 {:.2f}'.format(trade.pnlcomm))

    def stop(self):
        print('=' * 50)
        print('期末资产: {:.2f}'.format(self.broker.getvalue()))


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro(runonce=not args.runnext)
    cerebro.broker.set_cash(10000)

    data = bt.feeds.BacktraderCSVData(dataname=args.data)
    cerebro.adddata(data)

    cerebro.addstrategy(DemoStrategy)

    cerebro.run()

    if args.plot:
        cerebro.plot(style='candle')


def parse_args(pargs=None):

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='custom-indicator - 自定义指标教学示例')

    parser.add_argument('--data', required=False, default=DEFAULT_DATA,
                        help='数据文件（backtrader CSV 格式）')

    parser.add_argument('--runnext', action='store_true',
                        help='禁用向量化(runonce)，强制逐 bar 走 next()')

    parser.add_argument('--plot', '-p', action='store_true',
                        help='绘图（价格主图 + 两个指标子图）')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
