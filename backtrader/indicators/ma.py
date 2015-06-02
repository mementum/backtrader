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
            math.fsum(self.data_0.get(size=self.p.period)) / self.p.period

    def once(self, start, end):
        src = self.data_0.array
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

    def nextstart(self):
        super(SmoothingMovingAverage, self).next()

    def next(self):
        prev = self.line[-1]
        self.line[0] = prev * self.smfactor1 + self.data_0[0] * self.smfactor

    def oncestart(self, start, end):
        super(SmoothingMovingAverage, self).once(start, end)

    def once(self, start, end):
        darray = self.data_0.array
        larray = self.line.array
        smfactor = self.smfactor
        smfactor1 = self.smfactor1

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
        data = self.data_0.get(size=self.p.period)
        self.line[0] = self.coef *\
            math.fsum(map(operator.mul, data, self.weights))

    def once(self, start, end):
        darray = self.data_0.array
        larray = self.line.array
        period = self.p.period
        coef = self.coef
        weights = self.weights

        for i in xrange(start, end):
            data = darray[i - period + 1: i + 1]
            larray[i] = coef * math.fsum(map(operator.mul, data, weights))


class WMA(WeightedMovingAverage):
    pass


class MovingAverage(object):
    '''MovingAverage (alias MovAv)

    A placeholder to gather all Moving Average Types in a single place.

    It has the following attributes:

      - Simple
      - Exponential
      - Smoothed
      - Weighted

      - SMA
      - EMA
      - SMMA
      - WMA

    Instantiating a SimpleMovingAverage can be achieved as follows::

      sma = MovingAverage.Simple(self.data, period)

    '''
    Simple = SimpleMovingAverage
    Exponential = ExponentialMovingAverage
    Smoothed = SmoothedMovingAverage
    Weighted = WeightedMovingAverage

    SMA = SMA
    EMA = EMA
    SMMA = SMMA
    WMA = WMA


class MovAv(MovingAverage):
    pass  # alias
