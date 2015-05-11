#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
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
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math
import operator

from six.moves import xrange

from .. import Indicator


class ExecOnces(Indicator):
    extralines = 1

    def prenext(self):
        pass  # to avoid preonce be optimized away in metaclass

    def next(self):
        pass  # to avoid once be optimized away in metaclass

    def preonce(self, start, end):
        self.data.preonce(start, end)
        self.data.preonce = self.data.once_empty

    def oncestart(self, start, end):
        self.data.oncestart(start, end)
        self.data.oncestart = self.data.once_empty

    def once(self, start, end):
        self.data.once = self.data.once_empty


# See Stochastic for example of how to bind lines by assigning
class LinesBinder(Indicator):
    extralines = 1

    def next(self):
        self.data[0] = self.data1[0]

    def once(self, start, end):
        dst = self.data.lines[0].array
        src = self.data1.lines[0].array

        for i in xrange(start, end):
            dst[i] = src[i]


class OperationN(Indicator):
    params = (('period', 1),)

    def __init__(self):
        self.addminperiod(self.p.period)

    def next(self):
        self.line[0] = self.func(self.data_0.get(size=self.p.period))

    def once(self, start, end):
        dst = self.line.array
        src = self.data_0.array
        period = self.p.period
        func = self.func

        for i in xrange(start, end):
            dst[i] = func(src[i - period + 1: i + 1])


class MaxN(OperationN):
    lines = ('maxn',)
    func = max


class Highest(OperationN):
    lines = ('highest',)
    func = max


class MinN(OperationN):
    lines = ('minn',)
    func = min


class Lowest(OperationN):
    lines = ('lowest',)
    func = min


class SumN(OperationN):
    lines = ('sumn',)
    func = math.fsum


class Operation1(Indicator):
    def __init__(self, *args):
        self.dlines = [x.lines[0] for x in self.datas]
        self.getitem0 = operator.itemgetter(0)

        if args:
            self.args = list(args)
            self.next = self.next_args
            self.once = self.once_args

    def next(self):
        self.line[0] = self.func(map(self.getitem0, self.dlines))

    def once(self, start, end):
        dst = self.line.array
        func = self.func
        darrays = [dline.array for dline in self.dlines]

        for i in xrange(start, end):
            dst[i] = func([darray[i] for darray in darrays])

    def next_args(self):
        func = self.func
        self.line[0] = func(func(map(self.getitem0, self.dlines), self.args))

    def once_args(self, start, end):
        dst = self.line.array
        func = self.func
        darrays = [dline.array for dline in self.dlines]
        args = self.args

        for i in xrange(start, end):
            dst[i] = func(func([darray[i] for darray in darrays], args))


class Max(Operation1):
    lines = ('max',)
    func = max


class High(Operation1):
    lines = ('high',)
    func = max


class Min(Operation1):
    lines = ('min',)
    func = min


class Low(Operation1):
    lines = ('low',)
    func = min


class Sum(Operation1):
    lines = ('sum',)
    func = math.fsum
