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

from . import (Indicator, Highest, Lowest, If, UpDay, DownDay, Accum, TrueLow,
               TrueHigh)


class WilliamsR(Indicator):
    '''
    Larry Williams 开发的 Williams %R，用于显示 close 与指定周期最高-最低区间的关系。

    该指标通常称为 Williams %R，但 Python 标识符中不能使用 ``%``。

    Args:
        period: 最高价与最低价的回看周期。
        upperband: 绘图时的上轨参考线。
        lowerband: 绘图时的下轨参考线。

    Returns:
        WilliamsR: 输出 ``percR`` line 的 indicator。

    Formula:
      - num = highest_period - close
      - den = highestg_period - lowest_period
      - percR = (num / den) * -100.0

    See:
      - http://en.wikipedia.org/wiki/Williams_%25R

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(WilliamsR, period=14)
    '''
    lines = ('percR',)
    params = (('period', 14),
              ('upperband', -20.0),
              ('lowerband', -80.0),)

    plotinfo = dict(plotname='Williams R%')
    plotlines = dict(percR=dict(_name='R%'))

    def _plotinif(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]

    def __init__(self):
        h = Highest(self.data.high, period=self.p.period)
        l = Lowest(self.data.low, period=self.p.period)
        c = self.data.close

        self.lines.percR = -100.0 * (h - c) / (h - l)

        super(WilliamsR, self).__init__()


class WilliamsAD(Indicator):
    '''
    Larry Williams 提出的 Williams Accumulation/Distribution。它使用 UpDays 与
    DownDays 的概念，累计衡量价格是在 accumulation（向上）还是
    distribution（向下）。

    价格可能继续上涨，但若 upday 与 downday 相互抵消，accumulation 不再同步增强，
    就可能形成 divergence。

    Args:
        data: 含有 close/high/low line 的数据源。

    Returns:
        WilliamsAD: 输出 ``ad`` line 的 indicator。

    See:
    - http://www.metastock.com/Customer/Resources/TAAZ/?p=125
    - http://ta.mql4.com/indicators/trends/williams_accumulation_distribution

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(WilliamsAD)
    '''
    lines = ('ad',)

    def __init__(self):
        upday = UpDay(self.data.close)
        downday = DownDay(self.data.close)

        adup = If(upday, self.data.close - TrueLow(self.data), 0.0)
        addown = If(downday, self.data.close - TrueHigh(self.data), 0.0)

        self.lines.ad = Accum(adup + addown)

        super(WilliamsAD, self).__init__()
