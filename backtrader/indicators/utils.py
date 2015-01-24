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


class LineBinder(Indicator):
    # lines = ('linebinder',)
    extralines = 1
    params = (('line0', 0), ('line1', 1),)

    def __init__(self):
        self.data0line = self.datas[0][self.params.line0]
        self.data1line = self.datas[len(self.datas) > 1][self.params.line1]

    def next(self):
        self.data0line[0] = self.data1line[0]


class LineDifference(Indicator):
    lines = ('linedif',)
    params = (('line0', 0), ('line1', 0), ('ago0', 0), ('ago1', 0))

    def __init__(self):
        self.data0line = self.datas[0][self.params.line0]
        self.data1line = self.datas[1][self.params.line1]

        self.setminperiod(max([self.params.ago0, self.params.ago1]) + 1)

    def next(self):
        self.lines[0][0] = self.data0line[self.params.ago0] - self.data1line[self.params.ago1]


class LineDivision(Indicator):
    lines = ('linediv',)
    params = (('line0', 0), ('line1', 0), ('ago0', 0), ('ago1', 0), ('factor', 1.0))


    def __init__(self):
        self.data0line = self.datas[0][self.params.line0]
        self.data1line = self.datas[1][self.params.line1]

        self.setminperiod(max([self.params.ago0, self.params.ago1]) + 1)

    def next(self):
        self.lines[0][0] = self.params.factor * \
                           (self.data0line[self.params.ago0] / self.data1line[self.params.ago1])


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
