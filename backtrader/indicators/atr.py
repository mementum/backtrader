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
from .. import DataSeries, Indicator
from ma import MATypes


class TrueRange(Indicator):
    lines = ('tr',)

    def __init__(self):
        self.data_high = self.datas[0].lines[DataSeries.High]
        self.data_low = self.datas[0].lines[DataSeries.Low]
        self.data_close = self.datas[0].lines[DataSeries.Close]

        self.setminperiod(1)

    def next(self):
        th = self.data_high[0]
        tl = self.data_low[0]
        # If only 1 data is available the internally calculated index will be -1
        # which points to the end of the buffer, which is the beginning with only 1 data
        # The calculation makes sense finally and the 1st bar will always be 'th - tl'
        yc = self.data_close[1]

        self.lines[0][0] = max(th - tl, abs(yc - th), abs(yc - tl))


class AverageTrueRange(Indicator):
    lines = ('atr',)
    params = (('period', 14), ('matype', MATypes.Simple))

    def __init__(self):
        tr = TrueRange(self.datas[0])
        self.params.matype(tr, period=self.params.period).bindlines()

ATR = AverageTrueRange
