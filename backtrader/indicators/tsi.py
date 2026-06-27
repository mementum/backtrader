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
from . import EMA


class TrueStrengthIndicator(bt.Indicator):
    '''
    William Blau 在 *Stocks & Commodities* 杂志中提出的 True Strength Indicator。
    它默认通过价格的 double exponential 平滑来衡量 momentum。

    当极值继续扩张而收盘价没有同步扩张时，它可用于观察 divergence。

    Args:
        period1: 第一次平滑周期。
        period2: 第二次平滑周期。
        pchange: 计算价格变化的回看周期。
        _movav: 用于平滑的 Moving Average 类型。

    Returns:
        TrueStrengthIndicator: 输出 ``tsi`` line 的 indicator。

    Formula:
      - price_change = close - close(pchange periods ago)
      - sm1_simple = EMA(price_close_change, period1)
      - sm1_double = EMA(sm1_simple, period2)
      - sm2_simple = EMA(abs(price_close_change), period1)
      - sm2_double = EMA(sm2_simple, period2)
      - tsi = 100.0 * sm1_double / sm2_double

    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:true_strength_index

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(TrueStrengthIndicator, period1=25, period2=13)
    '''
    alias = ('TSI',)
    params = (
        ('period1', 25),
        ('period2', 13),
        ('pchange', 1),
        ('_movav', EMA),
    )
    lines = ('tsi',)

    def __init__(self):
        pc = self.data - self.data(-self.p.pchange)

        sm1 = self.p._movav(pc, period=self.p.period1)
        sm12 = self.p._movav(sm1, period=self.p.period2)

        sm2 = self.p._movav(abs(pc), period=self.p.period1)
        sm22 = self.p._movav(sm2, period=self.p.period2)

        self.lines.tsi = 100.0 * (sm12 / sm22)
