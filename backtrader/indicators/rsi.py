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

    def __init__(self):
        self.dataline = self.datas[0][self.params.line]

    def next(self):
        norm = self.params.norm
        self.lines[0][0] = norm - norm / (1.0 + self.dataline[0])

    def once(self, start, end):
        darray = self.dataline.array
        larray = self.lines[0].array
        norm = self.params.norm
        for i in xrange(start, end):
            larray[i] = norm - norm / (1.0 + darray[i])


class UpDays(Indicator):
    lines = ('up',)
    params = (('line', 0),)

    def __init__(self):
        self.dataline = self.datas[0].lines[self.params.line]

    def next(self):
        linediff = self.dataline[0] - self.dataline[-1]
        self.lines[0][0] = linediff if linediff > 0.0 else 0.0

    def once(self, start, end):
        darray = self.dataline.array
        larray = self.lines[0].array
        for i in xrange(start, end):
            linediff = darray[i] - darray[i - 1]
            larray[i] = linediff if linediff > 0.0 else 0.0


class DownDays(Indicator):
    lines = ('down',)
    params = (('line', 0),)

    def __init__(self):
        self.dataline = self.datas[0].lines[self.params.line]

    def next(self):
        linediff = self.dataline[-1] - self.dataline[0]
        self.lines[0][0] = linediff if linediff > 0.0 else 0.0

    def once(self, start, end):
        darray = self.dataline.array
        larray = self.lines[0].array
        for i in xrange(start, end):
            linediff = darray[i - 1] - darray[i]
            larray[i] = linediff if linediff > 0.0 else 0.0


class RSI(Indicator):
    lines = ('rsi',)
    params = (('period', 14), ('matype', MATypes.Smoothed), ('overbought', 70.0), ('oversold', 30.0),)

    def _plotlabel(self):
        return ','.join(map(str, [self.params.period, self.params.matype.__name__]))

    plotname = 'RSI'
    plothlines = plotticks = [70.0, 30.0]

    def __init__(self):
        self.plothlines = [self.params.overbought, self.params.oversold]
        self.plotticks = [self.params.overbought, self.params.oversold]

        updays = UpDays(self.datas[0])
        downdays = DownDays(self.datas[0])
        self.maup = self.params.matype(updays, period=self.params.period)
        self.madown = self.params.matype(downdays, period=self.params.period)
        if False:
            rs = LineDivision(maup, madown)
            rsi = LineNormalize(rs).bindlines()

    def next(self):
        # Explanation:
        # Next is much faster (40%) than having a LineDivision and LineNormalize objects
        # because values are being stored and the only needed thing is a division
        # The code in __init__ with the objects is much more elegant but really ineffective
        rs = self.maup[0][0] / self.madown[0][0]
        rsi = 100.0 - 100.0 / (1.0 + rs)
        self.lines[0][0] = rsi

    def once(self, start, end):
        larray = self.lines[0].array
        muarray = self.maup[0].array
        mdarray = self.madown[0].array

        for i in xrange(start, end):
            rs = muarray[i] / mdarray[i]
            rsi = 100.0 - 100. / (1.0 + rs)
            larray[i] = rsi


__all__ = ['RSI',]
