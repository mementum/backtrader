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


class StdDev(Indicator):
    lines = ('stddev',)
    params = (('period', 20),)

    def __init__(self):
        # mean could already be passed as a parameter to avoid recalculation
        # dmean = self.data1 if len(self.datas) > 1 else MaTypes.Simple(self.data, period=self.p.period)
        # sqmean = pow(dmean, 2)

        meansq = MATypes.Simple(pow(self.data, 2), period=self.p.period)
        sqmean = pow(MATypes.Simple(self.data, period=self.p.period), 2)
        self.lines.stddev = pow(meansq - sqmean, 0.5)


class StandardDeviation(StdDev):
    pass


class BollingerBands(Indicator):
    lines = ('mid', 'top', 'bot',)
    params = (('period', 20), ('devfactor', 2.0), ('matype', MATypes.Simple),)

    plotinfo = dict(subplot=False)
    plotlines = dict(
        mid=dict(ls='-.'),
        top=dict(_samecolor=True),
        bot=dict(_samecolor=True),
    )

    def _plotlabel(self):
        plabels = [self.p.period, self.p.devfactor,]
        plabels += [self.p.matype,] * self.p.notdefault('matype')
        return plabels

    def __init__(self):
        self.lines.mid = ma = self.p.matype(self.data, period=self.p.period)
        stddev = self.p.devfactor * StdDev(self.data, period=self.p.period)
        self.lines.top = ma + stddev
        self.lines.bot = ma - stddev

class BBands(BollingerBands):
    pass
