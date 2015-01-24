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
from .. indicator import Indicator
from ma import MovingAverageExponential
from utils import LineDifference


class MACDHisto(Indicator):
    lines = ('macd', 'signal', 'histo',)
    params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9))

    def __init__(self):
        me1 = MovingAverageExponential(self.datas[0], period=self.params.period_me1)
        me2 = MovingAverageExponential(self.datas[0], period=self.params.period_me2)

        macd = LineDifference(me1, me2).bindlines() # owner 0 <- own 0
        signal = MovingAverageExponential(macd, period=self.params.period_signal).bindlines(owner=1)
        LineDifference(macd, signal).bindlines(owner=2) # owner 2 <- own 0

    def next1(self):
        self[2][0] = self[0][0] - self[1][0]


class MACD(Indicator):
    lines = ('macd', 'signal',)
    params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9))

    def __init__(self):
        me1 = MovingAverageExponential(self.datas[0], period=self.params.period_me1)
        me2 = MovingAverageExponential(self.datas[0], period=self.params.period_me2)

        macd = LineDifference(me1, me2)
        self.bind2lines(0, macd)

        signal = MovingAverageExponential(macd, period=self.params.period_signal)
        self.bind2lines(1, signal)


macdimp = 4

if macdimp == 1:
    # Slowest implementation
    # 1. Composition via "extend"
    # 2. LineBinding of a LineDifference of the extended indicator
    # 3. By far the most elegant
    class MACDHistogram(Indicator):
        extend = (MACD, (0, 0), (1, 1))
        lines = ('histo',) # adds a line

        def __init__(self):
            LineDifference(self.extend, self.extend, line0=0, line1=1).bindlines(2)
elif macdimp == 2:
    # Slower implementation
    # 1. Composition via "extend"
    # 2. Calculation of the new line based on the values of
    #    the 2 lines of the extended indicator
    class MACDHistogram(Indicator):
        extend = (MACD, (0, 0), (1, 1))
        lines = ('histo',) # adds a line

        def next(self):
            self.lines[2][0] = self.lines[0][0] - self.lines[1][0]

elif macdimp == 3:
    # 2nd fastest implementation
    # 1. Inheritance
    # 2. LineBinding of a LineDifference indicator which operates on "self"
    # 3. By far the most elegant
    class MACDHistogram(MACD):
        lines = ('histo',) # adds a line

        def __init__(self):
            # super(MACDHistogram, self).__init__()
            LineDifference(self, self, line0=0, line1=1).bindlines(2)

elif macdimp == 4:
    # Fastest implementation
    # 1. Inheritance
    # 2. Calculation of the new line based on the values of
    #    the 2 lines of the base class in next
    class MACDHistogram(MACD):
        lines = ('histo',) # adds a line

        if False:
            def __init__(self):
                super(MACDHistogram, self).__init__()

        def next(self):
            self.lines[2][0] = self.lines[0][0] - self.lines[1][0]
