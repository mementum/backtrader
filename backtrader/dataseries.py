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

from .lineseries import LineSeries


class TimeFrame(object):
    Minutes, Days, Weeks, Months, Years = range(5)
    names = ['Minutes', 'Days', 'Weeks', 'Months', 'Years']

    @classmethod
    def getname(cls, tframe, compression):
        if compression == 1:
            # return singular if compression is 1
            return cls.names[tframe][:-1]
        return cls.names[tframe]


class DataSeries(LineSeries):
    _name = ''
    _compression = 1
    _timeframe = TimeFrame.Days

    Close, Low, High, Open, Volume, OpenInterest, DateTime = range(7)


class OHLC(DataSeries):
    lines = ('close', 'low', 'high', 'open', 'volume', 'openinterest',)


class OHLCDateTime(OHLC):
    lines = (('datetime', 'ls'),)
