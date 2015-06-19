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


class Momentum(Indicator):
    '''Momentum

    Measures the change in price by calculating the difference between the
    current price and the price from a given period ago


    Formula:
      - momentum = data - data_period

    See:
      - http://en.wikipedia.org/wiki/Momentum_(technical_analysis)

    Lines:
      - momentum

    Params:
      - period (12): period to consider
    '''
    lines = ('momentum',)
    params = (('period', 12),)
    plotinfo = dict(plothlines=[0.0])

    def __init__(self):
        self.l.momentum = self.data - self.data(-self.p.period)


class MomentumOscillator(Indicator):
    '''MomentumOscillator

    Measures the ratio of change in prices over a period

    Formula:
      - mosc = 100 * (data / data_period)

    See:
      - http://ta.mql4.com/indicators/oscillators/momentum

    Lines:
      - momosc

    Params:
      - period (12): period to consider
      - band (100.0): line to be plotted
    '''

    # Named output lines
    lines = ('momosc',)

    # Accepted parameters (and defaults) -
    # MovAvg also parameter to allow experimentation
    params = (('period', 12),
              ('band', 100.0))

    def _plotlabel(self):
        plabels = [self.p.period]
        return plabels

    def _plotinit(self):
        self.plotinfo.plothlines = [self.p.band]

    def __init__(self):

        self.l.momosc = 100.0 * (self.data / self.data(-self.p.period))


class RateOfChange(Indicator):
    '''RateOfChange (alias ROC)

    Measures the ratio of change in prices over a period

    Formula:
      - roc = (data - data_period) / data_period

    See:
      - http://en.wikipedia.org/wiki/Momentum_(technical_analysis)

    Lines:
      - roc

    Params:
      - period (12): period to consider
    '''

    # Named output lines
    lines = ('roc',)

    # Accepted parameters (and defaults) -
    # MovAvg also parameter to allow experimentation
    params = (('period', 12),)

    def __init__(self):
        dperiod = self.data(-self.p.period)
        self.l.roc = (self.data - dperiod) / dperiod


class ROC(RateOfChange):
    pass  # alias
