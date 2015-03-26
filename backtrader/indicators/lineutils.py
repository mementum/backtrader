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
import operator

import six
from six.moves import xrange
if six.PY3:
    cmp = lambda x, y: (x > y) - (x < y)

from .. import Indicator

class _SingleLineBase(Indicator):
    lines = ('out',)
    params = (('line', Indicator.Close), ('ago', 0), ('factor', 1.0),)

    def __init__(self, *args):
        self.dline = self.data[self.p.line]
        self.d0line = self.dline # alias
        self.addminperiod(self.p.ago)


class _LineBase(_SingleLineBase):
    params = (('factor', 1.0),)


class _LineBasePeriod(_LineBase):
    params = (('period', 1),)

    def __init__(self):
        self.addminperiod(self.p.period - 1)


class Highest(_LineBasePeriod):
    def next(self):
        self.lines[0] = max(self.dline.get(size=self.p.period, ago=self.p.ago))

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        factor = self.p.factor
        period = self.p.period

        for i in xrange(start, end):
            larray[i] = max(darray[i - ago - period + 1: i - ago + 1]) * self.p.factor


class Max(Highest):
    pass


class Lowest(_LineBasePeriod):
    def next(self):
        self.lines[0] = min(self.dline.get(size=self.p.period, ago=self.p.ago))

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        factor = self.p.factor
        period = self.p.period

        for i in xrange(start, end):
            larray[i] = min(darray[i - ago - period + 1: i - ago + 1]) * factor


class Min(Lowest):
    pass


class Abs(_LineBase):
    def next(self):
        self.lines[0] = abs(self.dline[self.p.ago]) * self.p.factor

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        factor = self.p.factor

        for i in xrange(start, end):
            larray[i] = abs(darray[i - ago]) * factor


class Mult(_LineBase):
    def next(self):
        self.lines[0] = self.dline[self.p.ago] * self.p.factor

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        factor = self.p.factor

        for i in xrange(start, end):
            larray[i] = darray[i - ago] * factor


class Cmp(_LineBase):
    params = (('cmpval', None),)

    def next(self):
        self.lines[0] = cmp(self.dline[self.p.ago], self.p.cmpval)

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        cmpval = self.p.cmpval

        for i in xrange(start, end):
            larray[i] = cmp(darray[i - ago], cmpval)


class Sum(_LineBasePeriod):
    def next(self):
        self.lines[0] = math.fsum(self.dline.get(ago=self.p.ago, size=self.p.period)) * self.p.factor

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        period = self.p.period
        factor = self.p.factor

        for i in xrange(start, end):
            larray[i] = math.fsum(darray[i - ago - period + 1: i - ago + 1]) * factor


class SumAv(Sum):
    def __init__(self):
        self.p.factor = 1.0 / self.p.period


class SumAvWeighted(Sum):
    def __init__(self):
        self.p.factor = 2.0 / (self.p.period * (self.p.period + 1.0))
        self.weights = [float(x) for x in range(1, self.p.period + 1)]

    def next(self):
        data = self.dline.get(ago=self.p.ago, size=self.p.period)
        self.lines[0] = self.p.factor * math.fsum(map(operator.mul, data, self.weights))

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        period = self.p.period
        factor = self.p.factor
        weights = self.weights

        for i in xrange(start, end):
            data = darray[i - ago - period + 1: i - ago + 1]
            larray[i] = factor * math.fsum(map(operator.mul, data, weights))


class SumAvSmoothing(SumAv):
    def __init__(self):
        self.smfactor = self.getsmoothfactor()
        self.sm1factor = 1.0 - self.smfactor

    def nextstart(self):
        super(SumAvSmoothing, self).next()
        self.prev = self.lines[0][0]

    def next(self):
        self.lines[0] = self.prev = self.prev * self.sm1factor + self.dline[0] * self.smfactor

    def oncestart(self, start, end):
        super(SumAvSmoothing, self).once(start, end)

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        smfactor = self.smfactor
        sm1factor = 1.0 - smfactor

        prev = larray[start - 1]

        for i in xrange(start, end):
            larray[i] = prev = sm1factor * prev + smfactor * darray[i - ago]


class Pow(_LineBase):
    params = (('exp', 1.0),)

    def next(self):
        self.lines[0] = math.pow(self.dline[self.p.ago], self.p.exp) * self.p.factor

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        factor = self.p.factor
        exp = self.p.exp

        for i in xrange(start, end):
            larray[i] = math.pow(darray[i - ago], exp) * factor


class Squared(Pow):
    params = (('exp', 2.0),)


class SquareRoot(_LineBase):
    def next(self):
        self.lines[0] = math.sqrt(self.dline[self.p.ago]) * self.p.factor

    def once(self, start, end):
        darray = self.dline.array
        larray = self.lines[0].array
        ago = self.p.ago
        factor = self.p.factor

        for i in xrange(start, end):
            larray[i] = math.sqrt(darray[i - ago]) * factor
