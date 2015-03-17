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
from .ma import MATypes, MovingAverageSimple
from .utils import LineDivision, LineDifference, LineSummation

class SquaredSum(Indicator):
    lines = ('sum',)

    params = (('line', 0), ('ago', 0), ('period', 10),)

    def __init__(self):
        self.dline = self.datas[0].lines[self.params.line]

    def next(self):
        s = math.pow(math.fsum(self.dline.get(ago=self.params.ago, size=self.params.period)), 2.0)
        self.lines.sum = s

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines.sum.array
        ago = self.params.ago
        period = self.params.period

        for i in xrange(start, end):
            larray[i] = math.pow(math.fsum(darray[i + ago - period + 1: i + ago + 1]), 2.0)


class NSumSquared(Indicator):
    lines = ('sqsum',)

    params = (('line', 0), ('ago', 0), ('period', 10),)

    def __init__(self):
        self.dline = self.datas[0].lines[self.params.line]
        self.fperiod = float(self.params.period)

    def next(self):
        squared = [math.pow(x, 2.0) for x in self.dline.get(ago=self.params.ago, size=self.params.period)]
        sqsum = math.fsum(squared)
        self.lines.sqsum = self.fperiod * sqsum

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines.sqsum.array
        ago = self.params.ago
        period = self.params.period
        fperiod = self.fperiod

        for i in xrange(start, end):
            sqsum = math.fsum([math.pow(x, 2.0) for x in darray[i + ago - period + 1: i + ago + 1]])
            larray[i] = fperiod * sqsum


class SquareRoot(Indicator):
    lines = ('sqroot',)

    params = (('line', 0), ('ago', 0), ('factor', 1.0),)

    def __init__(self):
        self.dline = self.datas[0].lines[self.params.line]

    def next(self):
        self.lines.sqsum = self.params.factor * math.sqrt(self.dline[self.params.ago])

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines.sqsum.array
        ago = self.params.ago
        factor = self.params.factor

        for i in xrange(start, end):
            larray[i] = factor * math.sqrt(darray[i + ago])


class StdDev(Indicator):
    lines = ('stddev',)

    params = (('period', 10), ('line',0), ('factor', 1.0),)

    def __init__(self):
        self.data = self.datas[0]

        sum_n_squared = NSumSquared(self.data, line=self.params.line, period=self.params.period)
        squared_sum = SquaredSum(self.data, line=self.params.line, period=self.params.period)

        sum_minus_squared = LineDifference(
            sum_n_squared, squared_sum, factor=1.0/float(pow(self.params.period, 2)))

        stddev = SquareRoot(sum_minus_squared, factor=self.params.factor).bindlines(0)

    def once(self, start, end):
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
        plabels = [self.params.period, self.params.stddev]
        return ','.join(map(str, plabels))

    def __init__(self):
        self.data = self.datas[0]

        ma = self.params.matype(self.data, line=self.params.line, period=self.params.period)
        ma.bindlines(0)

        stddev = StdDev(self.data, line=self.params.line, period=self.params.period,
                        factor=self.params.stddev)

        LineSummation(ma, stddev).bindlines(1)
        LineDifference(ma, stddev).bindlines(2)

    def once(self, start, end):
        pass
