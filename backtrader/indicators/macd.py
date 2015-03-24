#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
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
################################################################################

from __future__ import absolute_import, division, print_function, unicode_literals

from .. indicator import Indicator
from .ma import MovingAverageExponential
from .linesutils import LinesDifference


class MACD(Indicator):
    lines = ('macd', 'signal',)
    params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9))

    plotinfo = dict(hlines=[0.0])
    plotlines = dict(signal=dict(ls='--'))

    def __init__(self):
        me1 = MovingAverageExponential(self.data, period=self.p.period_me1)
        me2 = MovingAverageExponential(self.data, period=self.p.period_me2)
        macd = LinesDifference(me1, me2).bind2lines('macd')
        MovingAverageExponential(macd, period=self.p.period_signal).bind2lines('signal')


class MACDHistogram(MACD):
    lines = ('histo',)
    plotlines = dict(histo=dict(_method='bar', alpha=0.33))

    def __init__(self):
        LinesDifference(self, self, line=0, line1=1).bind2lines('histo')
