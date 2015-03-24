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
from .lineutils import Highest, Lowest
from .linesutils import LinesBinder, LinesDifference, LinesDivision


class StochasticFast(Indicator):
    lines = ('k', 'd',)
    params = (('period', 14), ('period_dfast', 3), ('matype', MATypes.Simple),
              ('overbought', 80.0), ('oversold', 20.0),)

    plotlines = dict(d=dict(ls='-.'))

    def _plotlabel(self):
        plabels = [self.p.period, self.p.period_dfast,]
        if self.p.matype != MATypes.Simple:
            plabels += [self.params.matype.__name__]
        return ','.join(map(str, plabels))

    def __init__(self):
        self.plotinfo.hlines = self.plotinfo.yticks = [self.p.overbought, self.p.oversold]

        highesthigh = Highest(self.data, period=self.p.period, line=self.High)
        lowestlow = Lowest(self.data, period=self.p.period, line=self.Low)
        knum = LinesDifference(self.data, lowestlow)
        kden = LinesDifference(highesthigh, lowestlow)
        kperc = LinesDivision(knum, kden, factor=100.0).bind2lines('k')
        self.p.matype(kperc, period=self.p.period_dfast).bind2lines('d')


class _StochasticInt(StochasticFast):
    params = (('period_dslow', 3),)

    def _plotlabel(self):
        plabels = [self.p.period, self.p.period_dfast, self.p.period_dslow,]
        if self.p.matype != MATypes.Simple:
            plabels += [self.params.matype.__name__]
        return ','.join(map(str, plabels))


class Stochastic(_StochasticInt):
    def __init__(self):
        LinesBinder(self, line=0, line1=1)
        self.p.matype(self, period=self.p.period_dslow, line=1).bind2lines('d')


class StochasticSlow(Stochastic):
    pass


class StochasticFull(_StochasticInt):
    lines = ('dd',)
    plotlines = dict(dd=dict(ls=':'))

    def __init__(self):
        self.p.matype(self, period=self.p.period_dslow, line=1).bind2lines('dd')
