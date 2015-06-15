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
from .ma import MovAv
from .. import Max
from . import SumN


class CommodityChannelIndex(Indicator):
    lines = ('cci',)

    params = (('period', 20),
              ('factor', 0.015),
              ('movav', MovAv.SMA))

    def __init__(self):
        tp = (self.data.high + self.data.low + self.data.close) / 3.0
        tpma = self.p.movav(tp, period=self.periodP)

        tp_minus_ma = tp - tpma

        meandev = SumN(abs(tp_minus_ma)) / self.p.period

        self.lines.cci = tp_minus_ma / (self.p.factor * meandev)
