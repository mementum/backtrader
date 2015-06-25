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
from . import Highest, Lowest


class WilliamsR(Indicator):
    '''
    Developed by Larry Williams to show the relation of closing prices to
    the highest-lowest range of a given period.

    Known as Williams %R (but % is not allowed in Python identifiers)

    Formula:
      - num = highest_period - close
      - den = highestg_period - lowest_period
      - percR = (num / den) * -100.0

    See:
      - http://en.wikipedia.org/wiki/Williams_%25R
    '''
    lines = ('percR',)
    params = (('period', 14),
              ('upperband', -20.0),
              ('lowerband', -80.0),)

    plotinfo = dict(plotname='Williams R%')
    plotlines = dict(percR=dict(_name='R%'))

    def _plotinif(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]

    def __init__(self):
        h = Highest(self.data.high, period=self.p.period)
        l = Lowest(self.data.low, period=self.p.period)
        c = self.data.close

        self.lines.percR = -100.0 * (h - c) / (h - l)

        super(WilliamsR, self).__init__()
