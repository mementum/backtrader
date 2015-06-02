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


class StandardDeviation(Indicator):
    '''StandardDeviation (alias StdDev)

    Calculates the standard deviation of the passed data for a given period

    Formula:
      - meansquared = SimpleMovingAverage(pow(data, 2), period)
      - squaredmean = pow(SimpleMovingAverage(data, period), 2)
      - stddev = pow(meansquared - squaredmean, 0.5)  # square root

    See:
      - http://en.wikipedia.org/wiki/Standard_deviation

    Lines:
      - stddev

    Params:
      - period (20): period for the moving average
      - movav (SimpleMovingAverage): moving average type to apply
    '''
    lines = ('stddev',)
    params = (('period', 20), ('movav', MovAv.Simple),)

    def __init__(self):
        # mean could already be passed as a parameter to avoid recalculation
        # dmean = self.data1 if len(self.datas) > 1 else \
        # self.p.movav(self.data, period=self.p.period)
        # sqmean = pow(dmean, 2)

        meansq = self.p.movav(pow(self.data, 2), period=self.p.period)
        sqmean = pow(self.p.movav(self.data, period=self.p.period), 2)
        self.lines.stddev = pow(meansq - sqmean, 0.5)


class StdDev(StandardDeviation):
    pass


class BollingerBands(Indicator):
    '''BollingerBands (alias BBands)

    Defined by John Bollinger in the 80s. It measures volatility by defining
    upper and lower bands at distance x standard deviations

    Formula:
      - midband = SimpleMovingAverage(close, period)
      - topband = midband + devfactor * StandardDeviation(data, period)
      - botband = midband - devfactor * StandardDeviation(data, period)

    See:
      - http://en.wikipedia.org/wiki/Bollinger_Bands

    Lines:
      - mid, top, bot

    Params:
      - period (20): period for the moving average
      - devfactor (2.0): distance of the bottom, top bands to the middle
      - movav (SimpleMovingAverage): moving average type to apply
    '''
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
        stddev = self.p.devfactor * StdDev(self.data, period=self.p.period)
        self.lines.top = ma + stddev
        self.lines.bot = ma - stddev


class BBands(BollingerBands):
    pass
