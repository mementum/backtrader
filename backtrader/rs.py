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


import datetime

from .dataseries import TimeFrame
from .utils import AutoOrderedDict
from .utils.py3 import with_metaclass
from . import metabase
from .feed import DataBase
from .utils import num2date, date2num


class _Bar(AutoOrderedDict):
    '''
    This class is a placeholder for the values of the standard lines of a
    DataBase class (from OHLCDateTime)

    It inherits from AutoOrderedDict to be able to easily return the values as
    an iterable and address the keys as attributes

    Order of definition is important and must match that of the lines
    definition in DataBase (which directly inherits from OHLCDateTime)
    '''
    def __init__(self, maxdate=False):
        super(_Bar, self).__init__()
        self.bstart(maxdate=maxdate)

    def bstart(self, maxdate=False):
        '''Initializes a bar to the default not-updated vaues'''
        # Order is important: defined in DataSeries/OHLC/OHLCDateTime
        self.open = float('NaN')
        self.high = float('-inf')
        self.close = float('NaN')
        self.low = float('inf')
        self.volume = 0.0
        self.openinterest = 0.0
        if maxdate:
            # Without - 1 ... fromordinal (inside num2date) will not work
            self.datetime = date2num(datetime.datetime.max) - 1
        else:
            self.datetime = None

    def isopen(self):
        '''Returns if a bar has already been updated

        Uses the fact that NaN is the value which is not equal to itself
        and ``open`` is initialized to NaN
        '''
        o = self.open
        return o == o  # False if NaN, True in other cases

    def bupdate(self, data):
        '''Updates a bar with the values from data

        Returns True if the update was the 1st on a bar (just opened)

        Returns False otherwise
        '''
        self.datetime = data.datetime[0]

        self.high = max(self.high, data.high[0])
        self.low = min(self.low, data.low[0])
        self.close = data.close[0]

        self.volume += data.volume[0]
        self.openinterest = data.openinterest[0]

        if not self.isopen():
            self.open = data.open[0]
            return True  # just opened the bar

        return False


class _Resampler(with_metaclass(metabase.MetaParams, object)):
    params = (('compression', 1),)

    def __init__(self, data):
        # Modify data information according to own parameters
        data._timeframe = self.p.timeframe
        data._compression = self.p.compression

        self.bar = _Bar(maxdate=True)  # bar holder
        self.compcount = 0  # count of produced bars to control compression

    def __call__(self, data):
        '''Called for each set of values produced by the data source'''
        self._checkbarover(data)
        self.bar.bupdate(data)
        data.backwards()  # remove bar consumed here
        # return True to indicate the bar can no longer be used by the data
        return True

    def _checkbarover(self, data):
        if not self.barover(data):
            return

        # over time/date limit - increase number of bars completed
        self.compcount += 1

        if not (self.compcount % self.p.compression):
            # boundary crossed and enough bars for compression ... proceed
            # print('output bar', num2date(self.bar.datetime))
            data._add2stack(list(self.bar.values()))
            self.bar.bstart()

    def last(self, data):
        '''Called when the data is no longer producing bars

        Can be called multiple times. It has the chance to (for example)
        produce extra bars which may still be accumulated and have to be
        delivered
        '''
        if self.bar.isopen():
            data._add2stack(list(self.bar.values()))
            self.bar.bstart()  # invalidate bar to avoid re-entering


class ResamplerDaily(_Resampler):
    params = (('timeframe', TimeFrame.Days),)

    def barover(self, data):
        return data.datetime.dt() > int(self.bar.datetime)


class ResamplerWeekly(_Resampler):
    params = (('timeframe', TimeFrame.Weeks),)

    def barover(self, data):
        year, week, _ = num2date(self.bar.datetime).isocalendar()
        yearweek = year * 100 + week

        baryear, barweek, _ = data.datetime.date().isocalendar()
        bar_yearweek = baryear * 100 + barweek

        return bar_yearweek > yearweek


class ResamplerMonthly(_Resampler):
    params = (('timeframe', TimeFrame.Months),)

    def barover(self, data):
        dt = num2date(self.bar.datetime)
        yearmonth = dt.year * 100 + dt.month

        bardt = data.datetime.datetime()
        bar_yearmonth = bardt.year * 100 + bardt.month

        return bar_yearmonth > yearmonth


class ResamplerYearly(_Resampler):
    params = (('timeframe', TimeFrame.Years),)

    def barover(self, data):
        return data.datetime.date().year > num2date(self.bar.datetime).year
