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
from .. import DataSeries, Indicator
from ma import MATypes
from utils import LineBinder, LineDifference, LineDivision, Highest, Lowest


class StochasticFast(Indicator):
    lines = ('k', 'd',)
    params = (('period', 14), ('period_dfast', 3), ('matype', MATypes.Simple),)

    def __init__(self):
        highesthigh = Highest(self.datas[0], period=self.params.period, line=DataSeries.High)
        lowestlow = Lowest(self.datas[0], period=self.params.period, line=DataSeries.Low)
        knum = LineDifference(self.datas[0], lowestlow)
        kden = LineDifference(highesthigh, lowestlow)
        kperc = LineDivision(knum, kden, factor=100.0).bindlines()
        self.params.matype(kperc, period=self.params.period_dfast).bindlines(1)


if True:
    class StochasticInt(StochasticFast):
        params = (('period_dslow', 3),)

        def __init__(self):
            if self.slow:
                LineBinder(self, line0=0, line1=1)

            self.params.matype(self, period=self.params.period_dslow, line=1).bindlines(2 - self.slow)


    class StochasticFull(StochasticInt):
        lines = ('dd',)
        slow = False


    class StochasticSlow(StochasticInt):
        slow = True


else:
    class StochasticSlow(Indicator):
        extend = (StochasticFast, (0, 1),)
        params = (('period_dslow', 3),)

        def __init__(self):
            self.params.matype(self.extend, period=self.params.period_dslow, line=1).bindlines(1)


    class StochasticFull(Indicator):
        extend = (StochasticFast, (0, 0), (1, 1),)
        lines = ('dd',)

        params = (('period_dslow', 3),)

        def __init__(self):
            self.params.matype(self.extend, period=self.params.period_dslow, line=1).bindlines(2)


Stochastic = StochasticSlow
