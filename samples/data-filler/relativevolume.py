#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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
import backtrader.indicators as btind


class RelativeVolume(bt.Indicator):
    csv = True  # show up in csv output (default for indicators is False)

    lines = ('relvol',)
    params = (
        ('period', 20),
        ('volisnan', True),
    )

    def __init__(self):
        if self.p.volisnan:
            # if missing volume will be NaN, do a simple division
            # the end result for missing volumes will also be NaN
            relvol = self.data.volume(-self.p.period) / self.data.volume
        else:
            # Else do a controlled Div with a built-in function
            relvol = bt.DivByZero(
                self.data.volume(-self.p.period),
                self.data.volume,
                zero=0.0)

        self.lines.relvol = relvol
