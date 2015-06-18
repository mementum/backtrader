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

from six.moves import xrange

from backtrader import Indicator
from backtrader.indicators import MovAv, OperationN


class FindLastHigh(OperationN):
    lines = ('ago',)

    def func(self, it):
        m = max(it)
        return next(i for i, v in enumerate(reversed(it)) if v == m)


class FindLastLow(OperationN):
    lines = ('ago',)

    def func(self, it):
        m = min(it)
        return next(i for i, v in enumerate(reversed(it)) if v == m)


class AroonUp(Indicator):
    lines = ('aroonup',)
    params = (('period', 25),)

    def __init__(self):
        hidist = FindLastHigh(self.data, period=self.p.period)
        self.l.aroonup = 100.0 * (self.p.period - hidist) / self.p.period


class AroonDown(Indicator):
    lines = ('aroondown',)
    params = (('period', 25),)

    def __init__(self):
        lodist = FindLastLow(self.data, period=self.p.period)
        self.l.aroondown = 100.0 * (self.p.period - lodist) / self.p.period


class AroonUpDown(Indicator):
    lines = ('aroonup', 'aroondown',)
    params = (('period', 25),)

    def __init__(self):
        self.lines.aroonup = AroonUp(self.data, period=self.p.period)
        self.lines.aroondown = AroonDown(self.data, period=self.p.period)


class AroonOscillator(Indicator):
    lines = ('aroonosc',)
    params = (('period', 25),)

    def __init__(self):
        aroonup = AroonUp(self.data, period=self.p.period)
        aroondown = AroonDown(self.data, period=self.p.period)

        self.lines.aroonosc = aroonup - aroondown
