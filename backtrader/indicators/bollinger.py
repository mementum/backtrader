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

from . import Indicator, MovAv, StdDev


class BollingerBands(Indicator):
    '''
    John Bollinger 在 20 世纪 80 年代定义的 Bollinger Bands 指标。

    通过在若干倍 standard deviation 距离上定义上下轨来衡量 volatility。

    Args:
        period: Moving Average 和 Standard Deviation 的周期。
        devfactor: standard deviation 乘数。
        movav: 使用的 Moving Average 类型。

    Returns:
        BollingerBands: 输出 ``mid``、``top``、``bot`` line 的 indicator。

    Formula:
      - midband = SimpleMovingAverage(close, period)
      - topband = midband + devfactor * StandardDeviation(data, period)
      - botband = midband - devfactor * StandardDeviation(data, period)

    See:
      - http://en.wikipedia.org/wiki/Bollinger_Bands

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(BollingerBands, period=20, devfactor=2.0)
    '''
    alias = ('BBands',)

    lines = ('mid', 'top', 'bot',)
    params = (('period', 20), ('devfactor', 2.0), ('movav', MovAv.Simple),)

    plotinfo = dict(subplot=False)
    plotlines = dict(
        mid=dict(ls='--'),
        top=dict(_samecolor=True),
        bot=dict(_samecolor=True),
    )

    def _plotlabel(self):
        plabels = [self.p.period, self.p.devfactor]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def __init__(self):
        self.lines.mid = ma = self.p.movav(self.data, period=self.p.period)
        stddev = self.p.devfactor * StdDev(self.data, ma, period=self.p.period,
                                           movav=self.p.movav)
        self.lines.top = ma + stddev
        self.lines.bot = ma - stddev

        super(BollingerBands, self).__init__()


class BollingerBandsPct(BollingerBands):
    '''
    扩展 ``BollingerBands``，增加 Percentage line。

    Args:
        period: Moving Average 和 Standard Deviation 的周期。
        devfactor: standard deviation 乘数。
        movav: 使用的 Moving Average 类型。

    Returns:
        BollingerBandsPct: 在 Bollinger Bands 基础上额外输出 ``pctb`` line。

    ---
    交互界面使用示范:

    >>> from backtrader import Cerebro
    >>> cerebro = Cerebro()
    >>> cerebro.addindicator(BollingerBandsPct)
    '''
    lines = ('pctb',)
    plotlines = dict(pctb=dict(_name='%B'))  # 图上把该 line 显示为 %B

    def __init__(self):
        super(BollingerBandsPct, self).__init__()
        self.l.pctb = (self.data - self.l.bot) / (self.l.top - self.l.bot)
