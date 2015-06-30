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

import six

from backtrader import Indicator
from . import (SumN, Average, ExpSmoothing, ExpSmoothingDynamic,
               AverageWeighted)


class MovingAverage(object):
    '''MovingAverage (alias MovAv)

    A placeholder to gather all Moving Average Types in a single place.

    Instantiating a SimpleMovingAverage can be achieved as follows::

      sma = MovingAverage.Simple(self.data, period)

    Or using the shorter aliases::

      sma = MovAv.SMA(self.data, period)

    or with the full (forwards and backwards) names:

      sma = MovAv.SimpleMovingAverage(self.data, period)

      sma = MovAv.MovingAverageSimple(self.data, period)

    '''
    _movavs = []

    @classmethod
    def register(cls, regcls):
        cls._movavs.append(regcls)

        clsname = regcls.__name__
        setattr(cls, clsname, regcls)

        clsalias = ''
        if clsname.endswith('MovingAverage'):
            clsalias = clsname.split('MovingAverage')[0]
        elif clsname.startswith('MovingAverage'):
            clsalias = clsname.split('MovingAverage')[1]

        if clsalias:
            setattr(cls, clsalias, regcls)


class MovAv(MovingAverage):
    pass  # alias


class MetaMovAvBase(Indicator.__class__):
    # Register any MovingAverage with the placeholder to allow the automatic
    # creation of envelopes and oscillators

    def __new__(meta, name, bases, dct):
        # Create the class
        cls = super(MetaMovAvBase, meta).__new__(meta, name, bases, dct)

        MovingAverage.register(cls)

        # return the class
        return cls


class MovingAverageBase(six.with_metaclass(MetaMovAvBase, Indicator)):
    params = (('period', 30),)
    plotinfo = dict(subplot=False)


class MovingAverageSimple(MovingAverageBase):
    '''
    Non-weighted average of the last n periods

    Formula:
      - movav = Sum(data, period) / period

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Simple_moving_average
    '''
    alias = ('SMA', 'SimpleMovingAverage',)
    lines = ('sma',)

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        self.lines[0] = Average(self.data, period=self.p.period)
        super(MovingAverageSimple, self).__init__()


class ExponentialMovingAverage(MovingAverageBase):
    '''
    A Moving Average that smoothes data exponentially over time.

    It is a subclass of SmoothingMovingAverage.

      - self.smfactor -> 2 / (1 + period)
      - self.smfactor1 -> `1 - self.smfactor`

    Formula:
      - movav = prev * (1.0 - smoothfactor) + newdata * smoothfactor

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average
    '''
    alias = ('EMA', 'MovingAverageExponential',)
    lines = ('ema',)

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        self.lines[0] = ExpSmoothing(self.data, period=self.p.period,
                                     alpha=2.0 / (1.0 + self.p.period))
        super(ExponentialMovingAverage, self).__init__()


class SmoothedMovingAverage(MovingAverageBase):
    '''
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
    '''
    alias = ('SMMA', 'WilderMA', 'MovingAverageSmoothed',
             'MovingAverageWilder',)
    lines = ('smma',)

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        self.lines[0] = ExpSmoothing(self.data, period=self.p.period,
                                     alpha=1.0 / self.p.period)
        super(SmoothedMovingAverage, self).__init__()


class AdaptiveMovingAverage(MovingAverageBase):
    '''
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
    '''
    alias = ('KAMA', 'MovingAverageAdaptive',)
    lines = ('kama',)
    params = (('fast', 2), ('slow', 30))

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        direction = self.data - self.data(-self.p.period)
        volatility = SumN(abs(self.data - self.data(-1)), period=self.p.period)

        er = abs(direction / volatility)  # efficiency ratio

        fast = 2.0 / (self.p.fast + 1.0)  # fast ema smoothing factor
        slow = 2.0 / (self.p.slow + 1.0)  # slow ema smoothing factor

        sc = pow((er * (fast - slow)) + slow, 2)  # scalable constant

        self.lines[0] = ExpSmoothingDynamic(self.data, period=self.p.period,
                                            alpha=sc)

        super(AdaptiveMovingAverage, self).__init__()


class WeightedMovingAverage(MovingAverageBase):
    '''
    A Moving Average which gives an arithmetic weighting to values with the
    newest having the more weight

    Formula:
      - weights = range(1, period + 1)
      - coef = 2 / (period * (period + 1))
      - movav = coef * Sum(weight[i] * data[period - i] for i in range(period))

    See also:
      - http://en.wikipedia.org/wiki/Moving_average#Weighted_moving_average
    '''
    alias = ('WMA', 'MovingAverageWeighted',)
    lines = ('wma',)

    def __init__(self):
        coef = 2.0 / (self.p.period * (self.p.period + 1.0))
        weights = [float(x) for x in range(1, self.p.period + 1)]

        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        self.lines[0] = AverageWeighted(self.data, period=self.p.period,
                                        coef=coef, weights=weights)
        super(WeightedMovingAverage, self).__init__()
