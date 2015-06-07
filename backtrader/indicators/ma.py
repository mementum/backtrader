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

import math
import operator

from six.moves import xrange

from .. import Indicator
from .miscops import SumN


class BaseMovingAverage(Indicator):
    lines = ('ma',)
    params = (('period', 30),)
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.addminperiod(self.p.period)


class SimpleMovingAverage(BaseMovingAverage):
    '''SimpleMovingAverage (alias SMA)

    Non-weighted average of the last n periods

    Formula:
      - movav = Sum(data, period) / period

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Simple_moving_average

    Lines:
      - ma

    Params:
      - period (30): period for the moving average
    '''
    plotinfo = dict(plotname='SMA')

    def next(self):
        self.line[0] = \
            math.fsum(self.data.get(size=self.p.period)) / self.p.period

    def once(self, start, end):
        src = self.data.array
        dst = self.line.array
        period = self.p.period

        for i in xrange(start, end):
            dst[i] = math.fsum(src[i - period + 1:i + 1]) / period


class SMA(SimpleMovingAverage):
    pass


class SmoothingMovingAverage(SimpleMovingAverage):
    '''SmoothingMovingAverage

    Base class for Moving Averages that apply a smoothing factor to the
    previous and incoming input to calculate the new value

    It is a subclass of SimpleMovingAverage and uses the 1st value
    produced by it as the seed for the next values

    Subclasses must override the method ``smoothingfactor`` which calculates
    two values:

      - self.smfactor -> the smoothing factor applied to new input
      - self.smfactor1 -> the smoothing factor applied to the olf value.
        usually `1 - self.smfactor`

    Formula:
      - movav = prev * (1 - smoothfactor) + newdata * smoothfactor

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Simple_moving_average

    Lines:
      - ma

    Params:
      - period (30): period for the moving average
    '''
    def __init__(self):
        super(SmoothingMovingAverage, self).__init__()
        self.smoothingfactor()

    def smoothingfactor(self):
        raise NotImplementedError

    def nextstart(self):
        super(SmoothingMovingAverage, self).next()

    def next(self):
        prev = self.line[-1]
        self.line[0] = prev * self.smfactor1 + self.data[0] * self.smfactor

    def oncestart(self, start, end):
        super(SmoothingMovingAverage, self).once(start, end)

    def once(self, start, end):
        darray = self.data.array
        larray = self.line.array
        smfactor = self.smfactor
        smfactor1 = self.smfactor1

        # Seed value from SMA calculated with the call to oncestart
        prev = larray[start - 1]

        for i in xrange(start, end):
            larray[i] = prev = prev * smfactor1 + darray[i] * smfactor


class ExponentialMovingAverage(SmoothingMovingAverage):
    '''ExponentialMovingAverage (alias EMA)

    A Moving Average that smoothes data exponentially over time.

    It is a subclass of SmoothingMovingAverage.

      - self.smfactor -> 2 / (1 + period)
      - self.smfactor1 -> `1 - self.smfactor`

    Formula:
      - movav = prev * (1.0 - smoothfactor) + newdata * smoothfactor

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

    Lines:
      - ma

    Params:
      - period (30): period for the moving average
    '''
    plotinfo = dict(plotname='EMA')

    def smoothingfactor(self):
        self.smfactor = 2.0 / (1.0 + self.p.period)
        self.smfactor1 = 1.0 - self.smfactor


class EMA(ExponentialMovingAverage):
    pass


class SmoothedMovingAverage(SmoothingMovingAverage):
    '''SmoothedMovingAverage (alias SMMA)

    Smoothing Moving Average used by Wilder in his 1978 book `New Concepts in
    Technical Trading`

    Defined in his book originalyl as:

      - new_value = (old_value * (period - 1) + new_data) / period

    Can be expressed as a SmoothingMovingAverage with the following factors:

      - self.smfactor -> 1.0 / period
      - self.smfactor1 -> `1.0 - self.smfactor`

    Formula:
      - movav = prev * (1.0 - smoothfactor) + newdata * smoothfactor

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average

    Lines:
      - ma

    Params:
      - period (30): period for the moving average
    '''
    plotinfo = dict(plotname='SMMA')

    def smoothingfactor(self):
        self.smfactor = 1.0 / self.p.period
        self.smfactor1 = 1.0 - self.smfactor


class SMMA(SmoothedMovingAverage):
    pass


class WeightedMovingAverage(BaseMovingAverage):
    '''WeightedMovingAverage (alias WMA)

    A Moving Average which gives an arithmetic weighting to values with the
    newest having the more weight

    Formula:
      - weights = range(1, period + 1)
      - coef = 2 / (period * (period + 1))
      - movav = coef * Sum(weight[i] * data[period - i] for i in range(period))

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Weighted_moving_average

    Lines:
      - ma

    Params:
      - period (30): period for the moving average
    '''
    plotinfo = dict(plotname='WMA')

    def __init__(self):
        super(WeightedMovingAverage, self).__init__()
        self.coef = 2.0 / (self.p.period * (self.p.period + 1.0))
        self.weights = [float(x) for x in range(1, self.p.period + 1)]

    def next(self):
        data = self.data.get(size=self.p.period)
        self.line[0] = self.coef *\
            math.fsum(map(operator.mul, data, self.weights))

    def once(self, start, end):
        darray = self.data.array
        larray = self.line.array
        period = self.p.period
        coef = self.coef
        weights = self.weights

        for i in xrange(start, end):
            data = darray[i - period + 1: i + 1]
            larray[i] = coef * math.fsum(map(operator.mul, data, weights))


class WMA(WeightedMovingAverage):
    pass  # alias


class AdaptiveMovingAverage(SmoothingMovingAverage):
    '''AdaptiveMovingAverage (alias KAMA)

    Defined by Perry Kaufman in his book `"Smarter Trading"`.

    It is A Moving Average with a continuosly scaled smoothing factor by taking
    into account market direction and volatility. The smoothing factor is
    calculated from 2 ExponetialMovingAverages smoothing factors, a fast one
    and slow one.

    If the market trends the value will tend to the fast ema smoothing
    period. If the market doesn't trend it will move towards the slow EMA
    smoothing period.

    It is a subclass of SmoothingMovingAverage, overriding once to account for
    the live nature of the smoothing factor

      - self.smfactor -> 2 / (1 + period)
      - self.smfactor1 -> `1 - self.smfactor`

    Formula:
      - direction = close - close_period
      - volatility = sumN(abs(close - close_n), period)
      - effiency_ratio = abs(direction / volatility)
      - fast = 2 / (fast_period + 1)
      - slow = 2 / (slow_period + 1)

      - smfactor = squared(efficienty_ratio * (fast - slow) + slow)
      - smfactor1 = 1.0  - smfactor

      - The initial seed value is a SimpleMovingAverage

    See also:
      - http://fxcodebase.com/wiki/index.php/Kaufman's_Adaptive_Moving_Average_(KAMA)
      - http://www.metatrader5.com/en/terminal/help/analytics/indicators/trend_indicators/ama
      - http://help.cqg.com/cqgic/default.htm#!Documents/adaptivemovingaverag2.htm

    Lines:
      - ma

    Params:
      - period (30): period for the moving average
      - fast (2): fast EMA period
      - slow (30): slow EMA period
    '''

    params = (('fast', 2), ('slow', 30))

    def __init__(self):
        super(AdaptiveMovingAverage, self).__init__()

        direction = self.data - self.data(-self.p.period)
        volatility = SumN(abs(self.data - self.data(-1)), period=self.p.period)

        er = abs(direction / volatility)  # efficiency ratio

        fast = 2.0 / (self.p.fast + 1.0)  # fast ema smoothing factor
        slow = 2.0 / (self.p.slow + 1.0)  # slow ema smoothing factor

        self.sc = pow((er * (fast - slow)) + slow, 2)  # scalable constant
        self.sc1 = 1.0 - self.sc

        # No assigment to line (due to the recursive nature of smoothing) and
        # therefore the min period has to be adjusted manually to account for
        # the extra bar needed inside SumN - there the minperiod is 2
        self.addminperiod(2)

    def smoothingfactor(self):
        # Smoothingfactors are dynamic and calculated during init as lines
        pass

    def next(self):
        # Need to override next to apply [] to sc and sc1
        prev = self.line[-1]
        self.line[0] = prev * self.sc1[0] + self.data[0] * self.sc[0]

    def once(self, start, end):
        # Need to override once to apply [] to sc and sc1
        darray = self.data.array
        larray = self.line.array
        sc = self.sc.array
        sc1 = self.sc1.array

        # Seed value from SMA calculated with the call to oncestart
        prev = larray[start - 1]

        for i in xrange(start, end):
            larray[i] = prev = prev * sc1[i] + darray[i] * sc[i]


class KAMA(AdaptiveMovingAverage):
    pass  # alias


class MovingAverage(object):
    '''MovingAverage (alias MovAv)

    A placeholder to gather all Moving Average Types in a single place.

    It has the following attributes to access MovingAverages

      - Simple or SMA
      - Exponential or EMA
      - Smoothed or SMMA
      - Weighted or WMA
      - Adaptive or AMA

    Instantiating a SimpleMovingAverage can be achieved as follows::

      sma = MovingAverage.Simple(self.data, period)

    Or using the shorter aliases::

      ema = MovAv.EMA(self.data, period)

    '''
    Simple = SimpleMovingAverage
    Exponential = ExponentialMovingAverage
    Smoothed = SmoothedMovingAverage
    Weighted = WeightedMovingAverage
    Adaptive = AdaptiveMovingAverage

    SMA = SMA
    EMA = EMA
    SMMA = SMMA
    WMA = WMA
    KAMA = KAMA


class MovAv(MovingAverage):
    pass  # alias
