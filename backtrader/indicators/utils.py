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
from .. import Indicator, Parameter


class LineDifference(Indicator):
    lines = ('linedif',)

    line0 = Parameter(0)
    line1 = Parameter(0)
    ago0 = Parameter(0)
    ago1 = Parameter(0)

    def __init__(self, data0, data1):
        self.data0line = data0[self.params.line0]
        self.data1line = data1[self.params.line1]

        self.setminperiod(max([self.params.ago0, self.params.ago1]) + 1)

    def next(self):
        self.lines[0][0] = self.data0line[self.params.ago0] - self.data1line[self.params.ago1]


class LineDivision(Indicator):
    lines = ('linediv',)

    line0 = Parameter(0)
    line1 = Parameter(0)
    ago0 = Parameter(0)
    ago1 = Parameter(0)
    factor = Parameter(1.0)

    def __init__(self, data0, data1):
        self.data0line = data0.lines[self.params.line0]
        self.data1line = data1.lines[self.params.line1]

        self.setminperiod(max([self.params.ago0, self.params.ago1]) + 1)

    def next(self):
        self.lines[0][0] = self.params.factor * \
                           (self.data0line[self.params.ago0] / self.data1line[self.params.ago1])


class Highest(Indicator):
    lines = ('highest',)

    period = Parameter(14)
    line = Parameter(0)

    def __init__(self, data):
        self.dataline = data[self.params.line]
        self.setminperiod(self.params.period)

    def next(self):
        self[0][0] = max(self.dataline.get(ago=0, size=self.params.period))


class Lowest(Indicator):
    lines = ('lowest',)

    period = Parameter(14)
    line = Parameter(0)

    def __init__(self, data):
        self.dataline = data.lines[self.params.line]
        self.setminperiod(self.params.period)

    def next(self):
        self[0][0] = min(self.dataline.get(size=self.params.period))
