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

from . import Indicator, Max, MovAv, MeanDev


class CommodityChannelIndex(Indicator):
    '''
    Donald Lambert 于 1980 年提出的 Commodity Channel Index，用于衡量
    "typical price" 相对均值的偏离，以识别极端状态和反转。

    Args:
        period: 计算 typical price 均值与平均偏差的周期。
        factor: 标准化偏离值的缩放因子。
        movav: 用于 typical price 均值的 Moving Average 类型。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        CommodityChannelIndex: 输出 ``cci`` line 的 indicator。

    Formula:
      - tp = typical_price = (high + low + close) / 3
      - tpmean = MovingAverage(tp, period)
      - deviation = tp - tpmean
      - meandev = MeanDeviation(tp)
      - cci = deviation / (meandeviation * factor)

    See:
      - https://en.wikipedia.org/wiki/Commodity_channel_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(CommodityChannelIndex, period=20)
    '''
    alias = ('CCI',)

    lines = ('cci',)

    params = (('period', 20),
              ('factor', 0.015),
              ('movav', MovAv.Simple),
              ('upperband', 100.0),
              ('lowerband', -100.0),)

    def _plotlabel(self):
        plabels = [self.p.period, self.p.factor]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines = [0.0, self.p.upperband, self.p.lowerband]

    def __init__(self):
        tp = (self.data.high + self.data.low + self.data.close) / 3.0
        tpmean = self.p.movav(tp, period=self.p.period)

        dev = tp - tpmean
        meandev = MeanDev(tp, tpmean, period=self.p.period)

        self.lines.cci = dev / (self.p.factor * meandev)

        super(CommodityChannelIndex, self).__init__()
