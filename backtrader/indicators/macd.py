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
from .utils import LineDifference


class MACD(Indicator):
    lines = ('macd', 'signal',)
    params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9))

    plotinfo = dict(hlines=[0.0])
    plotlines = dict(signal=dict(ls='--'))

    def __init__(self):
        me1 = MovingAverageExponential(self.datas[0], period=self.params.period_me1)
        me2 = MovingAverageExponential(self.datas[0], period=self.params.period_me2)
        macd = LineDifference(me1, me2).bindlines(0) # owner 0 <- own 0
        signal = MovingAverageExponential(macd, period=self.params.period_signal).bindlines(1)

    def once(self, start, end):
        pass #

class MACDHistogram(MACD):
    lines = ('histo',)
    plotlines = dict(histo=dict(_method='bar', alpha=0.33))

    def __init__(self):
        super(MACDHistogram, self).__init__()
        LineDifference(self, self, line0=0, line1=1).bindlines(owner=2) # owner 2 <- own 0
