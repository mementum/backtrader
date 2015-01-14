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
from .. indicator import Indicator, Parameter
from ma import MovingAverageExponential
from utils import LineDifference


class MACDHisto(Indicator):
    lines = ('macd', 'signal', 'histo',)

    period_me1 = Parameter(12)
    period_me2 = Parameter(26)
    period_signal = Parameter(9)

    def __init__(self, data):
        me1 = MovingAverageExponential(data, period=self.params.period_me1)
        me2 = MovingAverageExponential(data, period=self.params.period_me2)

        macd = LineDifference(me1, me2)
        self.bind2lines(0, macd)

        signal = MovingAverageExponential(macd, period=self.params.period_signal)
        self.bind2lines(1, signal)
        # histo = LineDifference(macd, signal)
        # self.bind2lines(2, histo)

    def next(self):
        self[2][0] = self[0][0] - self[1][0]


class MACD(Indicator):
    lines = ('macd', 'signal',)

    period_me1 = Parameter(12)
    period_me2 = Parameter(26)
    period_signal = Parameter(9)

    def __init__(self, data):
        me1 = MovingAverageExponential(data, period=self.params.period_me1)
        me2 = MovingAverageExponential(data, period=self.params.period_me2)

        macd = LineDifference(me1, me2)
        self.bind2lines(0, macd)

        signal = MovingAverageExponential(macd, period=self.params.period_signal)
        self.bind2lines(1, signal)


if True:
    class MACDHistogram(Indicator):
        extends = (MACD, 'MACD', (0, 0), (1, 1))
        lines = ('histo',) # adds a line

        def __init__(self, data):
            self.bind2lines(2, LineDifference(self.MACD, self.MACD, line0=0, line1=1))

else:
    class MACDHistogram(MACD):
        lines = ('histo',) # adds a line

        def __init__(self, data):
            super(MACDHistogram, self).__init__(data)
            # Use Naked to avoid infinite calculation recursion
            self.bind2lines(2, LineDifference(Naked(self), Naked(self), line0=0, line1=1))

        def next1(self):
            self.lines[2][0] = self.lines[0][0] - self.lines[1][0]
