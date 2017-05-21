#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
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


import backtrader as bt
from . import EMA


class TrueStrengthIndicator(bt.Indicator):
    alias = ('TSI',)
    params = (
        ('period1', 25),
        ('period2', 13),
    )
    lines = ('tsi',)

    def __init__(self):
        pc = self.data - self.data(-1)

        sm1 = bt.ind.EMA(pc, period=self.p.period1)
        sm12 = bt.ind.EMA(sm1, period=self.p.period2)

        sm2 = bt.ind.EMA(abs(pc), period=self.p.period1)
        sm22 = bt.ind.EMA(sm2, period=self.p.period2)

        self.lines.tsi = 100.0 * (sm12 / sm22)
