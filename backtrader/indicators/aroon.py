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

from . import Indicator, FindFirstIndexHighest, FindFirstIndexLowest


class _AroonBase(Indicator):
    '''
    Aroon 的基类，用于计算 AroonUp/AroonDown 值并定义公共参数。

    它使用类属性 ``_up`` 与 ``_down``（布尔标志）决定要计算哪个值。

    计算值不会直接赋给 line，而是存入实例变量 ``up`` 与 ``down``，供子类赋值或继续计算。
    '''
    _up = False
    _down = False

    params = (('period', 14), ('upperband', 70), ('lowerband', 30),)
    plotinfo = dict(plotymargin=0.05, plotyhlines=[0, 100])

    def _plotlabel(self):
        plabels = [self.p.period]
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines += [self.p.lowerband, self.p.upperband]

    def __init__(self):
        # 当前 data 向后看 period + 1。公式需要产出 0 到 100 之间的值，
        # 只有 hhidx/llidx 能覆盖 0 到 period 时才成立，因此需要 period + 1 个值。
        idxperiod = self.p.period + 1

        if self._up:
            hhidx = FindFirstIndexHighest(self.data.high, period=idxperiod)
            self.up = (100.0 / self.p.period) * (self.p.period - hhidx)

        if self._down:
            llidx = FindFirstIndexLowest(self.data.low, period=idxperiod)
            self.down = (100.0 / self.p.period) * (self.p.period - llidx)

        super(_AroonBase, self).__init__()


class AroonUp(_AroonBase):
    '''
    Tushar Chande 于 1995 年开发的 AroonUpDown indicator 中的 AroonUp。

    Args:
        period: 回看周期。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        AroonUp: 输出 ``aroonup`` line 的 indicator。

    Formula:
      - up = 100 * (period - distance to highest high) / period

    Note:
      line 在 0 到 100 之间 oscillate。这意味着距离最近 highest 或 lowest 的
      "distance" 必须从 0 到 period，公式才能产出 0 与 100。

      因此 lookback period 是 period + 1，因为当前 bar 也参与计算。

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AroonUp, period=14)
    '''
    _up = True

    lines = ('aroonup',)

    def __init__(self):
        super(AroonUp, self).__init__()

        self.lines.aroonup = self.up


class AroonDown(_AroonBase):
    '''
    Tushar Chande 于 1995 年开发的 AroonUpDown indicator 中的 AroonDown。

    Args:
        period: 回看周期。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        AroonDown: 输出 ``aroondown`` line 的 indicator。

    Formula:
      - down = 100 * (period - distance to lowest low) / period

    Note:
      line 在 0 到 100 之间 oscillate。这意味着距离最近 highest 或 lowest 的
      "distance" 必须从 0 到 period，公式才能产出 0 与 100。

      因此 lookback period 是 period + 1，因为当前 bar 也参与计算。

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AroonDown, period=14)
    '''
    _down = True

    lines = ('aroondown',)

    def __init__(self):
        super(AroonDown, self).__init__()

        self.lines.aroondown = self.down


class AroonUpDown(AroonUp, AroonDown):
    '''
    Tushar Chande 于 1995 年开发的 AroonUpDown。

    它通过计算给定周期内最近 high/low 的距离（AroonUp/AroonDown），尝试判断趋势是否存在。

    Args:
        period: 回看周期。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        AroonUpDown: 输出 ``aroonup`` 与 ``aroondown`` line 的 indicator。

    Formula:
      - up = 100 * (period - distance to highest high) / period
      - down = 100 * (period - distance to lowest low) / period

    Note:
      line 在 0 到 100 之间 oscillate。这意味着距离最近 highest 或 lowest 的
      "distance" 必须从 0 到 period，公式才能产出 0 与 100。

      因此 lookback period 是 period + 1，因为当前 bar 也参与计算。

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AroonUpDown, period=14)
    '''
    alias = ('AroonIndicator',)


class AroonOscillator(_AroonBase):
    '''
    AroonUpDown 的变体，显示 AroonUp 与 AroonDown 当前差值，用于直观看出哪一侧更强
    （大于 0 表示 AroonUp 更强，小于 0 表示 AroonDown 更强）。

    Args:
        period: 回看周期。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        AroonOscillator: 输出 ``aroonosc`` line 的 indicator。

    Formula:
      - aroonosc = aroonup - aroondown

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AroonOscillator, period=14)
    '''
    _up = True
    _down = True

    alias = ('AroonOsc',)

    lines = ('aroonosc',)

    def _plotinit(self):
        super(AroonOscillator, self)._plotinit()

        for yhline in self.plotinfo.plotyhlines[:]:
            self.plotinfo.plotyhlines.append(-yhline)

    def __init__(self):
        super(AroonOscillator, self).__init__()

        self.lines.aroonosc = self.up - self.down


class AroonUpDownOscillator(AroonUpDown, AroonOscillator):
    '''
    同时呈现 AroonUpDown 与 AroonOsc 的 indicator。

    Args:
        period: 回看周期。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        AroonUpDownOscillator: 输出 AroonUpDown 与 AroonOsc 相关 line 的
        indicator。

    Formula:
      (None, uses the aforementioned indicators)

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:aroon

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(AroonUpDownOscillator, period=14)
    '''
    alias = ('AroonUpDownOsc',)
