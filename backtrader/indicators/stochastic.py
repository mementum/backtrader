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

from .. import Indicator
from .ma import MATypes
from .lineoperations import Highest, Lowest


class _StochasticBase(Indicator):
    lines = ('k', 'd',)
    params = (('period', 14), ('period_dfast', 3), ('matype', MATypes.Simple),
              ('overbought', 80.0), ('oversold', 20.0),)

    plotlines = dict(d=dict(ls='--'))

    def _plotlabel(self):
        plabels = [self.p.period, self.p.period_dfast,]
        plabels += [self.p.matype,] * self.p.notdefault('matype')
        return plabels

    def __init__(self):
        self.plotinfo.hlines = self.plotinfo.yticks = [self.p.overbought, self.p.oversold,]

        highesthigh = Highest(self.data[self.PriceHigh], period=self.p.period)
        lowestlow = Lowest(self.data[self.PriceLow], period=self.p.period)
        knum = self.data[self.PriceClose] - lowestlow
        kden = highesthigh - lowestlow
        self.kperc = 100.0 * (knum / kden)
        self.dperc = self.p.matype(self.kperc, period=self.p.period_dfast)


class StochasticFast(_StochasticBase):
    def __init__(self):
        super(StochasticFast, self).__init__()
        self.lines.k = self.kperc
        self.lines.d = self.dperc


class Stochastic(_StochasticBase):
    params = (('period_dslow', 3),)

    def _plotlabel(self):
        plabels = [self.p.period, self.p.period_dfast, self.p.period_dslow,]
        plabels += [self.p.matype,] * self.p.notdefault('matype')
        return plabels

    def __init__(self):
        super(Stochastic, self).__init__()
        self.lines.k = self.dperc
        self.lines.d = self.p.matype(self.lines.k, period=self.p.period_dslow)


class StochasticSlow(Stochastic):
    pass


class StochasticAll(StochasticSlow):
    lines = ('dd',)
    plotlines = dict(dd=dict(ls=':'))

    def __init__(self):
        super(StochasticAll, self).__init__()
        self.lines.dd = self.p.matype(self.lines.d, period=self.p.period_dslow)
