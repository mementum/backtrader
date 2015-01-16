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
from ma import MATypes
from utils import LineDifference, LineDivision


class LineNormalize(Indicator):
    lines = ('linenorm',)
    params = (('norm', 100.0), ('line', 0))

    def __init__(self, data):
        self.dataline = data[self.params.line]

    def next(self):
        norm = self.params.norm
        self.lines[0][0] = norm - norm / (1.0 + self.dataline[0])


class UpDays(Indicator):
    lines = ('up',)
    params = (('line', 0),)

    def __init__(self, data):
        self.dataline = data.lines[self.params.line]

    def next(self):
        linediff = self.dataline[0] - self.dataline[1]
        self.lines[0][0] = linediff if linediff > 0.0 else 0.0


class DownDays(Indicator):
    lines = ('down',)
    params = (('line', 0),)

    def __init__(self, data):
        self.dataline = data.lines[self.params.line]

    def next(self):
        linediff = self.dataline[1] - self.dataline[0]
        self.lines[0][0] = linediff if linediff > 0.0 else 0.0


class RSI(Indicator):
    lines = ('rsi',)
    params = (('period', 14), ('matype', MATypes.Smoothed))

    def __init__(self, data):
        updays = UpDays(data)
        downdays = DownDays(data)
        if False:
            maup = self.params.matype(updays, period=self.params.period)
            madown = self.params.matype(downdays, period=self.params.period)
            rs = LineDivision(maup, madown)
            rsi = LineNormalize(rs)
            self.bind2lines(0, rsi)
        else:
            self.maup = self.params.matype(updays, period=self.params.period)
            self.madown = self.params.matype(downdays, period=self.params.period)

    def next(self):
        # Explanation:
        # Next is much faster (40%) than having a LineDivision and LineNormalize objects
        # because values are being stored and the only needed thing is a division
        # The code in __init__ with the objects is much more elegant but really ineffective

        rs = self.maup[0][0] / self.madown[0][0]
        rsi = 100.0 - 100.0 / (1.0 + rs)
        self.lines[0][0] = rsi

__all__ = ['RSI',]
