#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2017 Christoph Giese <cgi1>. Based on backtrader by Daniel Rodriguez
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
import math


class Choppy(Indicator):
    '''
    The Choppiness Index (CHOP) was developed by E.W. Dreiss to detect choppy (ranging) markets.
    Article: http://www.edwards-magee.com/ggu/dreisscaos.pdf
    '''
    lines = ('choppy',)
    params = (('period', 14), ('upperband', 61.8), ('lowerband', 38.2),
              ('safediv', False), ('safezero', 0.0))

    plotlines = dict(choppy=dict(_name='%Choppy', ls='--'), )

    def _plotlabel(self):
        plabels = [self.p.period, self.p.upperband, self.p.lowerband]
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]

    def __init__(self):
        pass  # Nothing to do yet.

    def next(self):

        if len(self.data) < self.p.period + 1:  # One additional for first yesterdays close
            return  # Not enough data yet.

        atr_sum = 0
        for i in range(0, -1 * self.p.period, -1):
            atr_sum += max(self.data.close[i - 1], self.data.open[i], self.data.high[i], self.data.low[i]) - min(
                self.data.close[i - 1], self.data.open[i], self.data.high[i], self.data.low[i])

        hh = max(self.data.high.get(size=self.p.period))
        ll = min(self.data.low.get(size=self.p.period))
        periodbox = hh - ll
        self.lines.choppy[0] = 100 * (math.log(atr_sum / periodbox, 10) / math.log(self.p.period, 10))
