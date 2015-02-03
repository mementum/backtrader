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
from .. import Indicator

class LineCmpTo(Indicator):
    lines = ('cmp',)

    params = (('line', 0), ('ago', 0), ('cmpval', None),)

    def __init__(self):
        self.dline = self.datas[0].lines[self.params.line]

    def next(self):
        self[0][0] = cmp(self.dline[self.params.ago], self.params.cmpval)


class _LineBase(Indicator):
    lines = ('line',)
    params = (('line0', 0), ('line1', 0), ('ago0', 0), ('ago1', 0), ('factor', 1.0),)

    def __init__(self):
        self.lined0 = self.datas[0][self.params.line0]
        self.lined1 = self.datas[len(self.datas) > 1][self.params.line1]

        self.setminperiod(max([self.params.ago0, self.params.ago1]) + 1)


class LinesCmp(_LineBase):
    def next(self):
        self[0][0] = cmp(self.lined0[self.params.ago0], self.lined1[self.params.ago1])


class LineBinder(_LineBase):
    def next(self):
        self.lined0[self.params.ago0] = self.lined1[self.params.ago1] * self.params.factor


class LineDifference(_LineBase):
    def next(self):
        self[0][0] = (self.lined0[self.params.ago0] - self.lined1[self.params.ago1]) * self.params.factor


class LineDivision(_LineBase):
    def next(self):
        self[0][0] = (self.lined0[self.params.ago0] / self.lined1[self.params.ago1]) * self.params.factor


class Highest(Indicator):
    lines = ('highest',)
    params = (('period', 14), ('line', 0))

    def __init__(self):
        self.dataline = self.datas[0][self.params.line]
        self.setminperiod(self.params.period)

    def next(self):
        self[0][0] = max(self.dataline.get(size=self.params.period))


class Lowest(Indicator):
    lines = ('lowest',)
    params = (('period', 14), ('line', 0))

    def __init__(self):
        self.dataline = self.datas[0][self.params.line]
        self.setminperiod(self.params.period)

    def next(self):
        self[0][0] = min(self.dataline.get(size=self.params.period))
