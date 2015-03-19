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

from .. import DataSeries, Indicator
from .ma import MATypes
from .utils import LineBinder, LineDifference, LineDivision, Highest, Lowest


class StochasticFast(Indicator):
    lines = ('k', 'd',)
    params = (('period', 14), ('period_dfast', 3), ('matype', MATypes.Simple),
              ('overbought', 80.0), ('oversold', 20.0),)

    plotlines = dict(d=dict(ls='-.'))

    def _plotlabel(self):
        plabels = [self.params.period, self.params.period_dfast, self.params.matype.__name__]
        return ','.join(map(str, plabels))

    def __init__(self):
        self.plotinfo.hlines = self.plotinfo.yticks = [self.params.overbought, self.params.oversold]

        highesthigh = Highest(self.datas[0], period=self.params.period, line=DataSeries.High)
        lowestlow = Lowest(self.datas[0], period=self.params.period, line=DataSeries.Low)
        knum = LineDifference(self.datas[0], lowestlow)
        kden = LineDifference(highesthigh, lowestlow)
        kperc = LineDivision(knum, kden, factor=100.0).bindlines('k')
        self.params.matype(kperc, period=self.params.period_dfast).bindlines('d')


class _StochasticInt(StochasticFast):
    params = (('period_dslow', 3),)

    def _plotlabel(self):
        plabels = [self.params.period, self.params.period_dfast, self.params.period_dslow,
                   self.params.matype.__name__]
        return ','.join(map(str, plabels))


class Stochastic(_StochasticInt):
    def __init__(self):
        super(Stochastic, self).__init__()
        LineBinder(self, line0=0, line1=1)
        self.params.matype(self, period=self.params.period_dslow, line=1).bindlines('d')

StochasticSlow = Stochastic


class StochasticFull(_StochasticInt):
    lines = ('dd',)
    plotlines = dict(dd=dict(ls=':'))

    def __init__(self):
        super(StochasticFull, self).__init__()
        self.params.matype(self, period=self.params.period_dslow, line=1).bindlines('dd')
