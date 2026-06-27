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

from . import Indicator, MovAv


class StandardDeviation(Indicator):
    '''
    计算传入 data 在指定周期内的 standard deviation。

    Args:
        period: 计算周期。
        movav: 用于均值计算的 Moving Average 类型。
        safepow: 是否对平方根入参取绝对值，以规避浮点表示导致的负值。

    Returns:
        StandardDeviation: 输出 ``stddev`` line 的 indicator。

    Note:
      - 如果传入 2 个 data，第 2 个会被视为第 1 个 data 的均值。

      - ``safepow`` 为 True 时，standard deviation 会以
        ``pow(abs(meansq - sqmean), 0.5)`` 计算，以防浮点表示使
        ``meansq - sqmean`` 出现微小负值。

    Formula:
      - meansquared = SimpleMovingAverage(pow(data, 2), period)
      - squaredmean = pow(SimpleMovingAverage(data, period), 2)
      - stddev = pow(meansquared - squaredmean, 0.5)  # square root

    See:
      - http://en.wikipedia.org/wiki/Standard_deviation

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(StandardDeviation, period=20)
    '''
    alias = ('StdDev',)

    lines = ('stddev',)
    params = (('period', 20), ('movav', MovAv.Simple), ('safepow', True),)

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        if len(self.datas) > 1:
            mean = self.data1
        else:
            mean = self.p.movav(self.data, period=self.p.period)

        meansq = self.p.movav(pow(self.data, 2), period=self.p.period)
        sqmean = pow(mean, 2)

        if self.p.safepow:
            self.lines.stddev = pow(abs(meansq - sqmean), 0.5)
        else:
            self.lines.stddev = pow(meansq - sqmean, 0.5)


class MeanDeviation(Indicator):
    '''MeanDeviation（别名 MeanDev）。

    计算传入 data 在指定周期内的 Mean Deviation。

    Args:
        period: 计算周期。
        movav: 用于均值与平均偏差计算的 Moving Average 类型。

    Returns:
        MeanDeviation: 输出 ``meandev`` line 的 indicator。

    Note:
      - 如果传入 2 个 data，第 2 个会被视为第 1 个 data 的均值。

    Formula:
      - mean = MovingAverage(data, period) (or provided mean)
      - absdeviation = abs(data - mean)
      - meandev = MovingAverage(absdeviation, period)

    See:
      - https://en.wikipedia.org/wiki/Average_absolute_deviation

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(MeanDeviation, period=20)
    '''
    alias = ('MeanDev',)

    lines = ('meandev',)
    params = (('period', 20), ('movav', MovAv.Simple),)

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        if len(self.datas) > 1:
            mean = self.data1
        else:
            mean = self.p.movav(self.data, period=self.p.period)

        absdev = abs(self.data - mean)
        self.lines.meandev = self.p.movav(absdev, period=self.p.period)
