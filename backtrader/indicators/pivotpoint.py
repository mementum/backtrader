#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator, CmpEx


class PivotPoint(Indicator):
    '''
    通过更大 timeframe 的上一周期价格 bar 组件均值定义关键价位。例如以日线交易时，
    可使用已经过去的月线固定价格计算 pivot。

    使用示例:

      data = btfeeds.ADataFeed(dataname=x, timeframe=bt.TimeFrame.Days)
      cerebro.adddata(data)
      cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    In the ``__init__`` method of the strategy:

      pivotindicator = btind.PivotPoiont(self.data1)  # the resampled data

    indicator 会尝试自动绘制到非 resampled data 上。若要关闭该行为，构造时使用：

      - _autoplot=False

    Note:

      示例使用 *days* 与 *months*，但可使用任意 timeframe 组合；推荐组合见相关资料。

    Args:
        open: 是否将 open 加入 pivot point 计算。
        close: 是否在计算中重复使用 close。
        _autoplot: 是否尝试绘制到真实目标 data 上。

    Returns:
        PivotPoint: 输出 ``p``、``s1``、``s2``、``r1`` 与 ``r2`` line 的
        indicator。

    Formula:
      - pivot = (h + l + c) / 3  # variants duplicate close or add open
      - support1 = 2.0 * pivot - high
      - support2 = pivot - (high - low)
      - resistance1 = 2.0 * pivot - low
      - resistance2 = pivot + (high - low)

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:pivot_points
      - https://en.wikipedia.org/wiki/Pivot_point_(technical_analysis)

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(PivotPoint, _autoplot=False)
    '''
    lines = ('p', 's1', 's2', 'r1', 'r2',)
    plotinfo = dict(subplot=False)

    params = (
        ('open', False),  # 将开盘价加入 pivot point
        ('close', False),  # 在计算中重复使用 close
        ('_autoplot', True),  # 尝试绘制到真实目标 data 上
    )

    def _plotinit(self):
        # 尝试绘制到实际 timeframe master
        if self.p._autoplot:
            if hasattr(self.data, 'data'):
                self.plotinfo.plotmaster = self.data.data

    def __init__(self):
        o = self.data.open
        h = self.data.high  # 当前 high
        l = self.data.low  # 当前 low
        c = self.data.close  # 当前 close

        if self.p.close:
            self.lines.p = p = (h + l + 2.0 * c) / 4.0
        elif self.p.open:
            self.lines.p = p = (h + l + c + o) / 4.0
        else:
            self.lines.p = p = (h + l + c) / 3.0

        self.lines.s1 = 2.0 * p - h
        self.lines.r1 = 2.0 * p - l

        self.lines.s2 = p - (h - l)
        self.lines.r2 = p + (h - l)

        super(PivotPoint, self).__init__()  # 启用协作式继承

        if self.p._autoplot:
            self.plotinfo.plot = False  # 禁用自身绘图
            self()  # Coupler 跟随真实对象


class FibonacciPivotPoint(Indicator):
    '''
    通过更大 timeframe 的上一周期价格 bar 组件均值定义关键价位。

    使用可配置的 Fibonacci level 定义 support/resistance level。

    使用示例:

      data = btfeeds.ADataFeed(dataname=x, timeframe=bt.TimeFrame.Days)
      cerebro.adddata(data)
      cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    In the ``__init__`` method of the strategy:

      pivotindicator = btind.FibonacciPivotPoiont(self.data1)  # the resampled data

    indicator 会尝试自动绘制到非 resampled data 上。若要关闭该行为，构造时使用：

      - _autoplot=False

    Note:

      示例使用 *days* 与 *months*，但可使用任意 timeframe 组合；推荐组合见相关资料。

    Args:
        open: 是否将 open 加入 pivot point 计算。
        close: 是否在计算中重复使用 close。
        _autoplot: 是否尝试绘制到真实目标 data 上。
        level1: 第 1 个 Fibonacci level。
        level2: 第 2 个 Fibonacci level。
        level3: 第 3 个 Fibonacci level。

    Returns:
        FibonacciPivotPoint: 输出 ``p``、``s1``、``s2``、``s3``、``r1``、
        ``r2`` 与 ``r3`` line 的 indicator。

    Formula:
      - pivot = (h + l + c) / 3  # variants duplicate close or add open
      - support1 = p - level1 * (high - low)  # level1 0.382
      - support2 = p - level2 * (high - low)  # level2 0.618
      - support3 = p - level3 * (high - low)  # level3 1.000
      - resistance1 = p + level1 * (high - low)  # level1 0.382
      - resistance2 = p + level2 * (high - low)  # level2 0.618
      - resistance3 = p + level3 * (high - low)  # level3 1.000

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:pivot_points

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(FibonacciPivotPoint, _autoplot=False)
    '''
    lines = ('p', 's1', 's2', 's3', 'r1', 'r2', 'r3')
    plotinfo = dict(subplot=False)
    params = (
        ('open', False),  # 将开盘价加入 pivot point
        ('close', False),  # 在计算中重复使用 close
        ('_autoplot', True),  # 尝试绘制到真实目标 data 上
        ('level1', 0.382),
        ('level2', 0.618),
        ('level3', 1.0),
    )

    def _plotinit(self):
        # 尝试绘制到实际 timeframe master
        if self.p._autoplot:
            if hasattr(self.data, 'data'):
                self.plotinfo.plotmaster = self.data.data

    def __init__(self):
        o = self.data.open
        h = self.data.high  # 当前 high
        l = self.data.low  # 当前 low
        c = self.data.close  # 当前 close

        if self.p.close:
            self.lines.p = p = (h + l + 2.0 * c) / 4.0
        elif self.p.open:
            self.lines.p = p = (h + l + c + o) / 4.0
        else:
            self.lines.p = p = (h + l + c) / 3.0

        self.lines.s1 = p - self.p.level1 * (h - l)
        self.lines.s2 = p - self.p.level2 * (h - l)
        self.lines.s3 = p - self.p.level3 * (h - l)

        self.lines.r1 = p + self.p.level1 * (h - l)
        self.lines.r2 = p + self.p.level2 * (h - l)
        self.lines.r3 = p + self.p.level3 * (h - l)

        super(FibonacciPivotPoint, self).__init__()

        if self.p._autoplot:
            self.plotinfo.plot = False  # 禁用自身绘图
            self()  # Coupler 跟随真实对象


class DemarkPivotPoint(Indicator):
    '''
    通过更大 timeframe 的上一周期价格 bar 组件均值定义 DeMark pivot 关键价位。

    使用示例:

      data = btfeeds.ADataFeed(dataname=x, timeframe=bt.TimeFrame.Days)
      cerebro.adddata(data)
      cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    In the ``__init__`` method of the strategy:

      pivotindicator = btind.DemarkPivotPoiont(self.data1)  # the resampled data

    indicator 会尝试自动绘制到非 resampled data 上。若要关闭该行为，构造时使用：

      - _autoplot=False

    Note:

      示例使用 *days* 与 *months*，但可使用任意 timeframe 组合；推荐组合见相关资料。

    Args:
        open: 是否将 open 加入 pivot point 计算。
        close: 是否在计算中重复使用 close。
        _autoplot: 是否尝试绘制到真实目标 data 上。

    Returns:
        DemarkPivotPoint: 输出 ``p``、``s1`` 与 ``r1`` line 的 indicator。

    Formula:
      - if close < open x = high + (2 x low) + close

      - if close > open x = (2 x high) + low + close

      - if Close == open x = high + low + (2 x close)

      - p = x / 4

      - support1 = x / 2 - high
      - resistance1 = x / 2 - low

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:pivot_points

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(DemarkPivotPoint, _autoplot=False)
    '''
    lines = ('p', 's1', 'r1',)
    plotinfo = dict(subplot=False)
    params = (
        ('open', False),  # 将开盘价加入 pivot point
        ('close', False),  # 在计算中重复使用 close
        ('_autoplot', True),  # 尝试绘制到真实目标 data 上
        ('level1', 0.382),
        ('level2', 0.618),
        ('level3', 1.0),
    )

    def _plotinit(self):
        # 尝试绘制到实际 timeframe master
        if self.p._autoplot:
            if hasattr(self.data, 'data'):
                self.plotinfo.plotmaster = self.data.data

    def __init__(self):
        x1 = self.data.high + 2.0 * self.data.low + self.data.close
        x2 = 2.0 * self.data.high + self.data.low + self.data.close
        x3 = self.data.high + self.data.low + 2.0 * self.data.close

        x = CmpEx(self.data.close, self.data.open, x1, x2, x3)
        self.lines.p = x / 4.0

        self.lines.s1 = x / 2.0 - self.data.high
        self.lines.r1 = x / 2.0 - self.data.low

        super(DemarkPivotPoint, self).__init__()

        if self.p._autoplot:
            self.plotinfo.plot = False  # 禁用自身绘图
            self()  # Coupler 跟随真实对象
