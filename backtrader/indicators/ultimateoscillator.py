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


import backtrader as bt
from backtrader.indicators import SumN, TrueLow, TrueRange


class UltimateOscillator(bt.Indicator):
    '''
    Ultimate Oscillator 用多个周期的 Buying Pressure 与 TrueRange 比值衡量
    momentum。

    Args:
        p1: 短周期求和窗口。
        p2: 中周期求和窗口。
        p3: 长周期求和窗口。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        UltimateOscillator: 输出 ``uo`` line 的 indicator。

    Formula:
      # Buying Pressure = Close - TrueLow
      BP = Close - Minimum(Low or Prior Close)

      # TrueRange = TrueHigh - TrueLow
      TR = Maximum(High or Prior Close)  -  Minimum(Low or Prior Close)

      Average7 = (7-period BP Sum) / (7-period TR Sum)
      Average14 = (14-period BP Sum) / (14-period TR Sum)
      Average28 = (28-period BP Sum) / (28-period TR Sum)

      UO = 100 x [(4 x Average7)+(2 x Average14)+Average28]/(4+2+1)

    See:

      - https://en.wikipedia.org/wiki/Ultimate_oscillator
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:ultimate_oscillator

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(UltimateOscillator)
    '''
    lines = ('uo',)

    params = (
        ('p1', 7),
        ('p2', 14),
        ('p3', 28),
        ('upperband', 70.0),
        ('lowerband', 30.0),
    )

    def _plotinit(self):
        baseticks = [10.0, 50.0, 90.0]
        hlines = [self.p.upperband, self.p.lowerband]

        # 绘制上下轨参考线
        self.plotinfo.plotyhlines = hlines
        # 绘制基础刻度与用户指定的上下轨刻度
        self.plotinfo.plotyticks = baseticks + hlines

    def __init__(self):
        bp = self.data.close - TrueLow(self.data)
        tr = TrueRange(self.data)

        av7 = SumN(bp, period=self.p.p1) / SumN(tr, period=self.p.p1)
        av14 = SumN(bp, period=self.p.p2) / SumN(tr, period=self.p.p2)
        av28 = SumN(bp, period=self.p.p3) / SumN(tr, period=self.p.p3)

        # 将浮点乘除移到公式外，减少 line 对象数量
        factor = 100.0 / (4.0 + 2.0 + 1.0)
        uo = (4.0 * factor) * av7 + (2.0 * factor) * av14 + factor * av28
        self.lines.uo = uo

        super(UltimateOscillator, self).__init__()
