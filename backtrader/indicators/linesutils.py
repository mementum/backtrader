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

import six
from six.moves import xrange
if six.PY3:
    cmp = lambda x, y: (x > y) - (x < y)

from .lineutils import _LineBase


class _LinesBase(_LineBase):
    params = (('line1', _LineBase.Close), ('ago1', 0),)

    def __init__(self):
        if len(self.datas) == 1:
            self.data1 = self.data

        self.d1line = self.data1[self.p.line1]
        self.addminperiod(max(self.p.ago1 - self.p.ago, 0)) # add extra period if needed


class _LinesBasePeriod(_LinesBase):
    params = (('period', 1),)

    def __init__(self):
        self.addminperiod(self.p.period - 1)


class LinesBinder(_LinesBase):
    def next(self):
        self.d0line[self.p.ago] = self.d1line[self.p.ago1] * self.p.factor

    def once(self, start, end):
        darray = self.dline.array
        d1array = self.d1line.array
        factor = self.p.factor
        ago = self.p.ago
        ago1 = self.p.ago1

        for i in xrange(start, end):
            darray[i - ago] = d1array[i - ago1] * factor


class LinesMax(_LinesBase):
    def next(self):
        self.lines[0] = max(self.dline[self.p.ago], self.d1line[self.p.ago1])

    def once(self, start, end):
        larray = self.lines[0].array
        darray = self.dline.array
        d1array = self.d1line.array
        factor = self.p.factor
        ago = self.p.ago
        ago1 = self.p.ago1

        for i in xrange(start, end):
            larray[i] = max(darray[i - ago], d1array[i - ago1]) * factor


class LinesMin(_LinesBase):
    def next(self):
        self.lines[0] = min(self.dline[self.p.ago], self.d1line[self.p.ago1])

    def once(self, start, end):
        larray = self.lines[0].array
        darray = self.dline.array
        d1array = self.d1line.array
        factor = self.p.factor
        ago = self.p.ago
        ago1 = self.p.ago1

        for i in xrange(start, end):
            larray[i] = min(darray[i - ago], d1array[i - ago1]) * factor


class LinesCmp(_LinesBase):
    def next(self):
        self.lines[0] = cmp(self.dline[self.p.ago], self.d1line[self.p.ago1])

    def once(self, start, end):
        larray = self.lines[0].array
        darray = self.dline.array
        d1array = self.d1line.array
        factor = self.p.factor
        ago = self.p.ago
        ago1 = self.p.ago1

        for i in xrange(start, end):
            larray[i] = cmp(darray[i - ago], d1array[i - ago1]) * factor


class LinesSummation(_LinesBase):
    def next(self):
        self.lines[0] = (self.d0line[self.p.ago] + self.d1line[self.p.ago1]) * self.p.factor

    def once(self, start, end):
        larray = self.lines[0].array
        darray = self.dline.array
        d1array = self.d1line.array
        factor = self.p.factor
        ago = self.p.ago
        ago1 = self.p.ago1

        for i in xrange(start, end):
            larray[i] = (darray[i - ago] + d1array[i - ago1]) * factor


class LinesDifference(_LinesBase):
    def next(self):
        self.lines[0] = (self.d0line[self.p.ago] - self.d1line[self.p.ago1]) * self.p.factor

    def once(self, start, end):
        larray = self.lines[0].array
        darray = self.dline.array
        d1array = self.d1line.array
        factor = self.p.factor
        ago = self.p.ago
        ago1 = self.p.ago1

        for i in xrange(start, end):
            larray[i] = (darray[i - ago] - d1array[i - ago1]) * factor


class LinesDiff(LinesDifference):
    pass


class LinesDivision(_LinesBase):
    def next(self):
        self.lines[0] = (self.d0line[self.p.ago] / self.d1line[self.p.ago1]) * self.p.factor

    def once(self, start, end):
        larray = self.lines[0].array
        darray = self.dline.array
        d1array = self.d1line.array
        factor = self.p.factor
        ago = self.p.ago
        ago1 = self.p.ago1

        for i in xrange(start, end):
            larray[i] = (darray[i - ago] / d1array[i - ago1]) * factor
