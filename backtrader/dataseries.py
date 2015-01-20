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
from lineseries import LineSeries


class DataSeries(LineSeries):
    Close, Low, High, Open, Volume, OpenInterest, DateTime = range(7)

    # To simply branch away from indicators/systems/strategies/studies
    pass


class OHLC(DataSeries):
    lines = ('close', 'low', 'high', 'open', 'volume', 'openinterest',)


class OHLCDateTime(OHLC):
    lines = (('datetime', 'dq'),)


class OHLCDateTimeTestExt(OHLC):
    lines = ('hlavg', 'hlcavg',)

    def docalc(self):
        self.lines.hlavg = (self.lines.high[0] + self.lines.low[0]) / 2.0
        self.lines.hlcavg = (self.lines.high[0] + self.lines.low[0] + self.lines.close[0]) / 3.0
