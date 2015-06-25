#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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


from backtrader import Indicator
from . import MovAv


class DoubleExponentialMovingAverage(Indicator):
    '''
    DEMA was first time introduced in 1994, in the article "Smoothing Data with
    Faster Moving Averages" by Patrick G. Mulloy in "Technical Analysis of
    Stocks & Commodities" magazine.

    It attempts to reduce the inherent lag associated to Moving Averages

    Formula:
      - dema = (2.0 - ema(data, period) - ema(ema(data, period), period)

    See:
      (None)
    '''
    alias = ('DEMA',)

    lines = ('dema',)
    params = (('period', 30), ('_movav', MovAv.EMA),)
    plotinfo = dict(subplot=False)

    def __init__(self):
        ema = self.p._movav(self.data, period=self.p.period)
        ema2 = self.p._movav(ema, period=self.p.period)
        self.lines.dema = 2.0 * ema - ema2

        super(DoubleExponentialMovingAverage, self).__init__()


class TripleExponentialMovingAverage(Indicator):
    '''
    TEMA was first time introduced in 1994, in the article "Smoothing Data with
    Faster Moving Averages" by Patrick G. Mulloy in "Technical Analysis of
    Stocks & Commodities" magazine.

    It attempts to reduce the inherent lag associated to Moving Averages

    Formula:
      - ema1 = ema(data, period)
      - ema2 = ema(ema1, period)
      - ema3 = ema(ema2, period)
      - tema = 3 * ema1 - 3 * ema2 + ema3

    See:
      (None)
    '''
    alias = ('TEMA',)

    lines = ('tema',)
    params = (('period', 30), ('_movav', MovAv.EMA),)
    plotinfo = dict(subplot=False)

    def __init__(self):
        ema = self.p._movav(self.data, period=self.p.period)
        ema2 = self.p._movav(ema, period=self.p.period)
        ema3 = self.p._movav(ema2, period=self.p.period)

        self.lines.tema = 3.0 * ema - 3.0 * ema2 + ema3
        super(TripleExponentialMovingAverage, self).__init__()


MovAv.DoubleExponential = DoubleExponentialMovingAverage
MovAv.TripleExponential = TripleExponentialMovingAverage
MovAv.DEMA = DEMA
MovAv.TEMA = TEMA
