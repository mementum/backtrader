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

from .. import Indicator
from .ma import MATypes
from .lineoperations import MaxVal, ValDiv, ValMinus, PlusVal
from .lineutils import _LineBase
from .linesutils import LinesDiff, LinesDivision


class LineNormalize(_LineBase):
    params = (('factor', 100.0),)

    def __init__(self):
        den = PlusVal(self.data, 1.0, line=self.p.line, ago=self.p.ago)
        minus = ValDiv(self.p.factor, den)
        ValMinus(self.p.factor, minus).bind2lines()


class UpDays(_LineBase):
    params = (('line', Indicator.Close),)
    def __init__(self):
        ld = LinesDiff(self.data, line=self.p.line, ago=self.p.ago, line1=self.p.line, ago1=self.p.ago + 1)
        MaxVal(ld, 0.0).bind2lines()


class DownDays(_LineBase):
    params = (('line', Indicator.Close),)
    def __init__(self):
        ld = LinesDiff(self.data, line=self.p.line, ago=self.p.ago + 1, line1=self.p.line, ago1=self.p.ago)
        MaxVal(ld, 0.0).bind2lines()


class RSI(Indicator):
    lines = ('rsi',)
    params = (('period', 14), ('matype', MATypes.Smoothed), ('overbought', 70.0), ('oversold', 30.0),)

    def _plotlabel(self):
        plabels = [self.p.period,]
        if self.p.matype != MATypes.Simple:
            plabels += [self.params.matype.__name__,]
        return ','.join(map(str, plabels))

    plotinfo = dict(plotname='RSI')

    def __init__(self):
        self.plotinfo.hlines = self.plotinfo.yticks = [self.p.overbought, self.p.oversold]

        maup = self.p.matype(UpDays(self.data), period=self.p.period)
        madown = self.p.matype(DownDays(self.data), period=self.p.period)
        rs = LinesDivision(maup, madown)
        rsi = LineNormalize(rs).bindlines()


__all__ = ['RSI',]
