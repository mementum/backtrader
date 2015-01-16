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
from utils import LineDifference, LineDivision, Highest, Lowest


class StochasticFast(Indicator):
    lines = ('k', 'd',)
    params = (('period', 14), ('period_dfast', 3), ('matype', MATypes.Simple),)

    def __init__(self, data):
        highesthigh = Highest(data, period=self.params.period, line=DataSeries.High)
        lowestlow = Lowest(data, period=self.params.period, line=DataSeries.Low)
        knum = LineDifference(data, lowestlow)
        kden = LineDifference(highesthigh, lowestlow)
        kperc = LineDivision(knum, kden, factor=100.0)
        self.bind2lines(0, kperc)
        dfastperc = self.params.matype(kperc, period=self.params.period_dfast)
        self.bind2lines(1, dfastperc)


class StochasticSlow(Indicator):
    extend = (StochasticFast, (0, 1),)
    params = (('period_dslow', 3),)

    def __init__(self, data):
        dslowperc = self.params.matype(self.extend, period=self.params.period_dslow, line=1)
        self.bind2lines(1, dslowperc)


class StochasticFull(Indicator):
    extend = (StochasticFast, (0, 0), (1, 1),)
    lines = ('dslow',)

    params = (('period_dslow', 3),)

    def __init__(self, data):
        dslowperc = self.params.matype(self.extend, period=self.params.period_dslow, line=1)
        self.bind2lines(2, dslowperc)


Stochastic = StochasticSlow
