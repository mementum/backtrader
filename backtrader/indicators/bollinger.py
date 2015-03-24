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

import math

from .. import Indicator
from .ma import MATypes
from .lineutils import SquareRoot, Squared, SumAv
from .linesutils import LinesDifference, LinesSummation


class StdDev(Indicator):
    lines = ('stddev',)

    params = (('period', 20), ('line',0), ('factor', 1.0),)

    def __init__(self):
        sumavsq = SumAv(Squared(self.data, line=self.p.line), period=self.p.period)
        data1 = self.data if len(self.datas) == 1 else self.data1
        sqsumav = Squared(SumAv(data1, period=self.p.period, line=self.p.line))
        SquareRoot(LinesDifference(sumavsq, sqsumav), factor=self.p.factor).bindlines('stddev')


class StandardDeviation(StdDev):
    pass


class BollingerBands(Indicator):
    lines = ('mid', 'top', 'bot',)

    params = (('period', 20), ('stddev', 2.0), ('line', 0), ('matype', MATypes.Simple),)

    plotinfo = dict(subplot=False)
    plotlines = dict(
        mid=dict(ls='-.'),
        top=dict(_samecolor=True),
        bot=dict(_samecolor=True),
    )

    def _plotlabel(self):
        plabels = [self.p.period, self.p.stddev]
        return ','.join(map(str, plabels))

    def __init__(self):
        ma = self.p.matype(self.data, line=self.p.line, period=self.p.period)
        ma.bind2lines('mid')

        stddev = StdDev(self.data, line=self.p.line, period=self.p.period, factor=self.p.stddev)
        LinesSummation(ma, stddev).bind2lines('top')
        LinesDifference(ma, stddev).bind2lines('bot')
