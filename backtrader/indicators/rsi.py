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

from .. import Indicator
from .ma import MATypes
from .lineoperations import Max


class UpDays(Indicator):
    lines = ('up',)

    def __init__(self):
        self.lines.up = Max(self.data - self.data(-1), 0.0)


class DownDays(Indicator):
    lines = ('down',)

    def __init__(self):
        self.lines.down = Max(self.data(-1) - self.data, 0.0)


class RSI(Indicator):
    lines = ('rsi',)
    params = (('period', 14),
              ('matype', MATypes.Smoothed),
              ('overbought', 70.0),
              ('oversold', 30.0))

    def _plotlabel(self):
        plabels = [self.p.period]
        plabels += [self.p.matype] * self.p.notdefault('matype')
        return plabels

    plotinfo = dict(plotname='RSI')

    def __init__(self):
        self.plotinfo.plothlines = [self.p.overbought, self.p.oversold]
        self.plotinfo.plotyticks = self.plotinfo.plothlines

        updays = UpDays(self.data)
        downdays = DownDays(self.data)
        maup = self.p.matype(updays, period=self.p.period)
        madown = self.p.matype(downdays, period=self.p.period)
        rs = maup / madown
        self.lines.rsi = 100.0 - 100.0 / (1.0 + rs)
