#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Ssoftware Foundation, either version 3 of the License, or
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

from . import Indicator, Max, MovAv
from . import DivZeroByZero

class RelativeMomentumIndex(Indicator):
    '''
    Description:
    The Relative Momentum Index was developed by Roger Altman and was introduced
    in his article in the February, 1993 issue of Technical Analysis of
    Stocks & Commodities magazine.

    While your typical RSI counts up and down days from close to close, the
    Relative Momentum Index counts up and down days from the close relative to
    a close x number of days ago. The result is an RSI that is a bit smoother.

    Usage:
    Use in the same way you would any other RSI . There are overbought and
    oversold zones, and can also be used for divergence and trend analysis.


    Formula:
     - RMI = 100 * H / (H + B) where

    H is the sum of positive changes over specified period (bar period)
    B is the sum of negative changes over specified period (bar period)

    See:
      - https://www.marketvolume.com/technicalanalysis/relativemomentumindex.asp
      - https://www.tradingview.com/script/UCm7fIvk-FREE-INDICATOR-Relative-Momentum-Index-RMI/
      - https://www.prorealcode.com/prorealtime-indicators/relative-momentum-index-rmi/


    Notes:
      - ``safediv`` (default: False) If this parameter is True the division
        rs = maup / madown will be checked for the special cases in which a
        ``0 / 0`` or ``x / 0`` division will happen
      - ``safehigh`` (default: 100.0) will be used as RMI value for the
        ``x / 0`` case

      - ``safelow``  (default: 50.0) will be used as RMI value for the
        ``0 / 0`` case

    '''
    alias = ('RMI', )
    lines = ('rmi', )

    params = (('period', 9),
              ('movav', MovAv.Smoothed),
              ('loopback', 5),
              ('upperband', 70.0),
              ('lowerband', 30.0),
              ('safediv', False),
              ('safehigh', 100.0),
              ('safelow', 50.0),)

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.loopback]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]

    def __init__(self):

        momup = Max(self.data.close-self.data.close(-self.p.loopback), 0)
        momdown = Max(self.data.close(-self.p.loopback)-self.data.close, 0)

        up = self.p.movav(momup, period=self.p.period)
        dn = self.p.movav(momdown, period=self.p.period)

        if not self.p.safediv:
            rm = up / dn
        else:
            highrs = self._rscalc(self.p.safehigh)
            lowrs = self._rscalc(self.p.safelow)
            rm = DivZeroByZero(up, dn, highrs, lowrs)

        self.l.rmi = 100 * rm / (1 + rm)

    def _rscalc(self, rmi):
        try:
            rm = (-100.0 / (rmi - 100.0)) - 1.0
        except ZeroDivisionError:
            return float('inf')

        return rm
