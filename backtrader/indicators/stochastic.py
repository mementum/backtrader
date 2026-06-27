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

from . import Indicator, Max, MovAv, Highest, Lowest, DivByZero


class _StochasticBase(Indicator):
    '''Stochastic 的基类，用于统一 %K/%D 计算、参数和绘图参考线。'''
    lines = ('percK', 'percD',)
    params = (('period', 14), ('period_dfast', 3), ('movav', MovAv.Simple),
              ('upperband', 80.0), ('lowerband', 20.0),
              ('safediv', False), ('safezero', 0.0))

    plotlines = dict(percD=dict(_name='%D', ls='--'),
                     percK=dict(_name='%K'))

    def _plotlabel(self):
        plabels = [self.p.period, self.p.period_dfast]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]

    def __init__(self):
        highesthigh = Highest(self.data.high, period=self.p.period)
        lowestlow = Lowest(self.data.low, period=self.p.period)
        knum = self.data.close - lowestlow
        kden = highesthigh - lowestlow
        if self.p.safediv:
            self.k = 100.0 * DivByZero(knum, kden, zero=self.p.safezero)
        else:
            self.k = 100.0 * (knum / kden)
        self.d = self.p.movav(self.k, period=self.p.period_dfast)

        super(_StochasticBase, self).__init__()


class StochasticFast(_StochasticBase):
    '''
    Dr. George Lane 在 20 世纪 50 年代提出的 StochasticFast。它比较 close
    与价格区间的位置，当 close 靠近极值时尝试显示 convergence。

      - close 接近 high 时通常上升
      - close 接近 low 时通常下降

    当极值继续扩张而 close 未同步接近极值时，可用于观察 divergence。

    Args:
        period: high/low 回看周期。
        period_dfast: %D 快线平滑周期。
        movav: 用于平滑的 Moving Average 类型。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。
        safediv: 是否保护除零。
        safezero: 除零时使用的默认值。

    Returns:
        StochasticFast: 输出 ``percK`` 与 ``percD`` line 的 indicator。

    Formula:
      - hh = highest(data.high, period)
      - ll = lowest(data.low, period)
      - knum = data.close - ll
      - kden = hh - ll
      - k = 100 * (knum / kden)
      - d = MovingAverage(k, period_dfast)

    See:
      - http://en.wikipedia.org/wiki/Stochastic_oscillator

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(StochasticFast)
    '''
    def __init__(self):
        super(StochasticFast, self).__init__()
        self.lines.percK = self.k
        self.lines.percD = self.d


class Stochastic(_StochasticBase):
    '''
    常规版（或 slow version）额外添加一层 Moving Average，因此：

      - StochasticFast 的 percD line 会成为 percK line
      - percD 会成为原始 percD 上 ``period_dslow`` 周期的 Moving Average

    Args:
        period: high/low 回看周期。
        period_dfast: 快速 %D 平滑周期。
        period_dslow: 慢速 %D 平滑周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        Stochastic: 输出 ``percK`` 与 ``percD`` line 的 indicator。

    Formula:
      - k = k
      - d = d
      - d = MovingAverage(d, period_dslow)

    See:
      - http://en.wikipedia.org/wiki/Stochastic_oscillator

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(Stochastic)
    '''
    alias = ('StochasticSlow',)
    params = (('period_dslow', 3),)

    def _plotlabel(self):
        plabels = [self.p.period, self.p.period_dfast, self.p.period_dslow]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        super(Stochastic, self).__init__()
        self.lines.percK = self.d
        self.l.percD = self.p.movav(self.l.percK, period=self.p.period_dslow)


class StochasticFull(_StochasticBase):
    '''
    该版本显示 3 条可用 line：

      - percK
      - percD
      - percSlow

    Args:
        period: high/low 回看周期。
        period_dfast: 快速 %D 平滑周期。
        period_dslow: 慢速 %D 平滑周期。
        movav: 用于平滑的 Moving Average 类型。

    Returns:
        StochasticFull: 输出 ``percK``、``percD`` 与 ``percDSlow`` line 的
        indicator。

    Formula:
      - k = d
      - d = MovingAverage(k, period_dslow)
      - dslow =

    See:
      - http://en.wikipedia.org/wiki/Stochastic_oscillator

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(StochasticFull)
    '''
    lines = ('percDSlow',)
    params = (('period_dslow', 3),)

    plotlines = dict(percDSlow=dict(_name='%DSlow'))

    def _plotlabel(self):
        plabels = [self.p.period, self.p.period_dfast, self.p.period_dslow]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        super(StochasticFull, self).__init__()
        self.lines.percK = self.k
        self.lines.percD = self.d
        self.l.percDSlow = self.p.movav(
            self.l.percD, period=self.p.period_dslow)
