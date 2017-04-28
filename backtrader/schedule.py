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


import collections
from datetime import date, datetime, timedelta
import itertools

from .feed import AbstractDataBase
from .utils import date2num, num2date
from .utils.py3 import integer_types, range
from .utils import TIME_MAX


__all__ = ['SESSION_TIME', 'SESSION_START', 'SESSION_END', 'Schedule']

SESSION_TIME, SESSION_START, SESSION_END = 0, 1, 2


class Schedule(object):

    SESSION_TIME, SESSION_START, SESSION_END = (SESSION_TIME, SESSION_START,
                                                SESSION_END)

    def __init__(self, tid, owner, strats,
                 when, offset, repeat, weekdays, tzdata,
                 *args, **kwargs):

        self.tid = tid  # identifier

        self.owner = owner  # for external reference purposes only
        self.strats = strats  # boolean for external reference

        self.when = when
        self.offset = offset
        self.repeat = repeat
        self.weekdays = weekdays
        self.tzdata = tzdata
        self.args = args
        self.kwargs = kwargs

        # write down the 'reset when' value
        if not isinstance(when, integer_types):  # expect time/datetime
            self._rwhen = self.when
        elif when == SESSION_START:
            self._rwhen = self.tzdata.p.sessionstart
        elif when == SESSION_END:
            self._rwhen = self.tzdata.p.sessionend

        self._isdata = isinstance(self.tzdata, AbstractDataBase)
        self._reset_when()

    def _reset_when(self, ddate=datetime.min):
        self._when = self._rwhen

        self._lastcall = ddate
        self.dtwhen = self.dwhen = None

    def schedcheck(self, dt):
        d = num2date(dt)
        ddate = d.date()

        if self._lastcall == ddate:  # not repeating, awaiting date change
            return False

        dwhen = self.dwhen
        dtwhen = self.dtwhen
        if dtwhen is None:
            dwhen = datetime.combine(ddate, self._when)
            if self.offset:
                dwhen += self.offset

            self.dwhen = dwhen

            if self._isdata:
                dtwhen = self.tzdata.date2num(dwhen)
            elif self.tzdata is not None:  # assume pytz compatible
                dtwhen = date2num(dwhen, tz=self.tzdata)

            self.dtwhen = dtwhen

        if dt < dtwhen:
            return False  # timer target not met

        self.lastwhen = dwhen

        if not self.repeat:  # cannot repeat
            self._reset_when(ddate)  # reset and mark as called on ddate
        else:
            if self._isdata:  # eos provided by data
                nexteos, _ = self.tzdata._getnexteos()
            else:  # generic eos
                nexteos = datetime.combine(ddate, TIME_MAX)

            while True:
                dwhen += self.repeat
                if dwhen > nexteos:  # new schedule is beyone session
                    self._reset_when(ddate)  # reset to original point
                    break

                if dwhen > d:  # gone over current date
                    self.dtwhen = dtwhen = date2num(dwhen)  # float timestamp
                    # Get the localized expected next time
                    if self._isdata:
                        self.dwhen = self.tzdata.num2date(dtwhen)
                    else:  # assume pytz compatible or None
                        self.dwhen = num2date(dtwhen, tz=tzdata)

                    break

        return True  # timer target was met
