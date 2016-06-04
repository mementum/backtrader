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

import calendar
from collections import OrderedDict
import datetime

from backtrader import Analyzer, TimeFrame


class TimeReturn(Analyzer):
    '''
    This analyzer calculates the Returns by looking at the beginning
    and end of the year

    Params:

      - timeframe (default TimeFrame.Years)

      - compression (default: 1)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('timeframe', TimeFrame.Years),
        ('compression', 1),
    )

    def get_analysis(self):
        return self.rets

    def start(self):
        self.data = self.strategy.data
        self.rets = OrderedDict()
        self.dtcmp, self.dtkey = self._get_dt_cmpkey(datetime.datetime.min)
        self.lastvalue = self.strategy.broker.getvalue()

    def notify_cashvalue(self, cash, value):
        dt = self.data.datetime.datetime()
        dtcmp, dtkey = self._get_dt_cmpkey(dt)

        if dtcmp > self.dtcmp:
            self.dtkey = dtkey
            self.dtcmp = dtcmp
            self.value_start = self.lastvalue  # last value before cycle change

        self.rets[self.dtkey] = (value / self.value_start) - 1.0
        self.lastvalue = value

    def _get_dt_cmpkey(self, dt):
        if self.p.timeframe == TimeFrame.Years:
            dtcmp = dt.year
            dtkey = datetime.datetime(dt.year, 12, 31)

        elif self.p.timeframe == TimeFrame.Months:
            dtcmp = dt.year * 100 + dt.month
            _, lastday = calendar.monthrange(dt.year, dt.month)
            dtkey = datetime.datetime(dt.year, dt.month, lastday)

        elif self.p.timeframe == TimeFrame.Weeks:
            isoyear, isoweek, isoweekday = dt.isocalendar()
            dtcmp = isoyear * 100 + isoweek
            sunday = dt + datetime.timedelta(days=7 - isoweekday)
            dtkey = datetime.datetime(sunday.year, sunday.month, sunday.day)

        elif self.p.timeframe == TimeFrame.Days:
            dtkey = dt.year * 10000 + dt.month * 100 + dt.day
            dtcmp = datetime.datetime(dt.year, dt.month, dt.day)

        else:
            dtcmp, dtkey = self._getsubday_cmpkey(dt)

        return dtcmp, dtkey

    def _get_subday_cmpkey(self, dt):
        # Calculate intraday position
        point = dt.hour * 60 + dt.minute

        if self.p.timeframe < TimeFrame.Minutes:
            point = point * 60 + dt.second

        if self.p.timeframe < TimeFrame.Seconds:
            point = point * 1e6 + dt.microsecond

        # Apply compression to update point position (comp 5 -> 200 // 5)
        point = point // self.p.compression

        # Move to next boundary
        point += 1

        # Restore point to the timeframe units by de-applying compression
        point *= self.p.compression

        # Get hours, minutes, seconds and microseconds
        if self.p.timeframe == TimeFrame.Minutes:
            ph, pm = divmod(point, 60)
            ps = 0
            pus = 0
        elif self.p.timeframe == TimeFrame.Seconds:
            ph, pm = divmod(point, 60 * 60)
            pm, ps = divmod(pm, 60)
            pus = 0
        elif self.p.timeframe == TimeFrame.MicroSeconds:
            ph, pm = divmod(point, 60 * 60 * 1e6)
            pm, psec = divmod(pm, 60 * 1e6)
            ps, pus = divmod(psec, 1e6)

        # moving 1 minor unit to the left to be in the boundary
        pm -= self.p.timeframe == TimeFrame.Minutes
        ps -= self.p.timeframe == TimeFrame.Seconds
        pus -= self.p.timeframe == TimeFrame.MicroSeconds

        # Replace intraday parts with the calculated ones and update it
        dtcmp = dt.replace(hour=ph, minute=pm, second=ps, microsecond=pus)
        dtkey = dtcmp

        return dtcmp, dtkey
