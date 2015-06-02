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

from .. import Indicator
from .ma import MovAv
from .. import Max


class UpDays(Indicator):
    '''UpDays

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"* for the RSI

    Recods days which have been "up", i.e.: the close price has been
    higher than the day before.

    Formula:
      - up = max(close - close_prev, 0)

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    Lines:
      - up

    Params:
      (None)
    '''
    lines = ('up',)

    def __init__(self):
        self.lines.up = Max(self.data - self.data(-1), 0.0)


class DownDays(Indicator):
    '''DownDays

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"* for the RSI

    Recods days which have been "down", i.e.: the close price has been
    lower than the day before.

    Formula:
      - down = max(close_prev - close, 0)

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    Lines:
      - down

    Params:
      (None)
    '''
    lines = ('down',)

    def __init__(self):
        self.lines.down = Max(self.data(-1) - self.data, 0.0)


class RSI(Indicator):
    '''RSI (alias RelativeStrengthIndex and RSI_SMMA)

    Defined by J. Welles Wilder, Jr. in 1978 in his book *"New Concepts in
    Technical Trading Systems"*.

    It measures momentum by calculating the ration of higher closes and
    lower closes after having been smoothed by an average, normalizing
    the result between 0 and 100

    Formula:
      - up = updays(data)
      - down = downdays(data)
      - maup = movingaverage(up, period)
      - madown = movingaverage(down, period)
      - rs = maup / madown
      - rsi = 100 - 100 / (1 + rs)

    The moving average used is the one originally defined by Wilder,
    the SmoothedMovingAverage

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    Note:
      Wikipedia shows a version with an Exponential Moving Average and claims
      the original from Wilder used a SimpleMovingAverage.

      The original described in the book and implemented here used the
      SmoothedMovingAverage like the AverageTrueRange also defined by
      Mr. Wilder.

      Stockcharts has it right.

        - http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:relative_strength_index_rsi

    Lines:
      - rsi

    Params:
      - period (14): period for the indicator
      - movav (Smoothed): moving average to apply
      - overbought (70): indication line of overbought territory
      - oversold (30): indication line of oversold territory
    '''
    lines = ('rsi',)
    params = (('period', 14),
              ('movav', MovAv.Smoothed),
              ('overbought', 70.0),
              ('oversold', 30.0))

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    plotinfo = dict(plotname='RSI')

    def __init__(self):
        self.plotinfo.plothlines = [self.p.overbought, self.p.oversold]
        self.plotinfo.plotyticks = self.plotinfo.plothlines

        updays = UpDays(self.data)
        downdays = DownDays(self.data)
        maup = self.p.movav(updays, period=self.p.period)
        madown = self.p.movav(downdays, period=self.p.period)
        rs = maup / madown
        self.lines.rsi = 100.0 - 100.0 / (1.0 + rs)


class RelativeStrenghIndex(RSI):
    pass  # alias


class RSI_SMMA(RSI):
    pass  # alias


class RSI_Cutler(Indicator):
    '''RSI_Cutler (alias RSI_SMA)

    Uses a SimpleMovingAverage as described in Wikipedia and other soures

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    Lines:
      - rsi

    Params:
      - period (14): period for the indicator
      - movav (Simple): moving average to apply
      - overbought (70): indication line of overbought territory
      - oversold (30): indication line of oversold territory
    '''
    params = (('movav', MovAv.Simple),)


class RSI_SMA(RSI_Cutler):
    pass  # alias


class RSI_EMA(Indicator):
    '''RSI_EMA

    Uses an ExponentialMovingAverage as described in Wikipedia

    See:
      - http://en.wikipedia.org/wiki/Relative_strength_index

    Lines:
      - rsi

    Params:
      - period (14): period for the indicator
      - movav (Exponential): moving average to apply
      - overbought (70): indication line of overbought territory
      - oversold (30): indication line of oversold territory
    '''
    params = (('movav', MovAv.Exponential),)
