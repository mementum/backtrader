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

from backtrader import Indicator, Max
from backtrader.indicators import MovAv, MeanDev


class CommodityChannelIndex(Indicator):
    '''CommodityChannelIndex (alias CCI)

    Introduced by Donald Lambert in 1980 to measure variations of the
    "typical price" (see below) from its mean to identify extremes and
    reversals

    Formula:
      - tp = typical_price = (high + low + close) / 3
      - tpmean = MovingAverage(tp, period)
      - deviation = tp - tpmean
      - meandev = MeanDeviation(tp)
      - cci = deviation / (meandeviation * factor)

    See:
      - https://en.wikipedia.org/wiki/Commodity_channel_index

    Lines:
      - cci

    Params:
      - period (20): period for the indicator
      - factor (0.015): scaling factor
      - movav (Simple): moving average type to apply
      - upperband (100.0): upper band to draw for visual inspection
      - lowerband (-100.0): upper band to draw for visual inspection
    '''
    lines = ('cci',)

    params = (('period', 20),
              ('factor', 0.015),
              ('movav', MovAv.Simple),
              ('upperband', 100.0),
              ('lowerband', -100.0),)

    def __init__(self):
        self.plotinfo.plotyhlines = [0.0, self.p.upperband, self.p.lowerband]

        tp = (self.data.high + self.data.low + self.data.close) / 3.0
        tpmean = self.p.movav(tp, period=self.p.period)

        dev = tp - tpmean
        meandev = MeanDev(tp, tpmean, period=self.p.period)

        self.lines.cci = dev / (self.p.factor * meandev)


class CCI(CommodityChannelIndex):
    pass  # alias
