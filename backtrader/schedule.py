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

from .feed import AbstractDataBase
from .utils import date2num, num2date
from .utils.py3 import integer_types, range
from .utils import TIME_MAX


__all__ = ['SESSION_TIME', 'SESSION_START', 'SESSION_END', 'Schedule']

SESSION_TIME, SESSION_START, SESSION_END = 0, 1, 2


class Schedule(object):

    SESSION_TIME, SESSION_START, SESSION_END = (SESSION_TIME, SESSION_START,
                                                SESSION_END)

    def __init__(self, tid,
                 cerebro, runstrats,
                 when, offset, repeat, weekdays, tzdata,
                 cb, *args, **kwargs):

        fields = [
            'cerebro', 'runstrats', 'tid',
            'when', 'offset', 'repeat', 'weekdays', 'tzdata',
        ]
        l = locals()
        for f in fields:
            setattr(self, f, l[f])

        self.cbargs = args, kwargs

        if isinstance(cb, collections.Callable):
            self.cb = cb
        else:  # assume cb is iterable with indices to strategies
            self.cb = None
            self.cbs = [runstrats[i] for i in cb or range(len(runstrats))]

        if not isinstance(when, integer_types):  # must be time/datetime
            self.stype = SESSION_TIME
        else:
            self.stype = when
            if self.tzdata is None:
                self.tzdata = cerebro.datas[0]

        self._isdata = isinstance(self.tzdata, AbstractDataBase)
        self._reset_when()

    def _reset_when(self, ddate=datetime.min):
        if self.stype == SESSION_TIME:
            self._when = self.when
        elif self.stype == SESSION_START:
            self._when = self.tzdata.p.sessionstart
        elif self.stype == SESSION_END:
            self._when = self.tzdata.p.sessionend

        self._lastcall = ddate
        self.dtwhen = self.dwhen = None

    def schedcheck(self, dt):
        d = num2date(dt)
        ddate = d.date()

        if self._lastcall == ddate:  # not repeating, awaiting date change
            return

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

        if dt >= dtwhen:
            cbargs, cbkwargs = self.cbargs
            if self.cb is not None:
                self.cb(self.tid, dwhen, *cbargs, **cbkwargs)
            else:
                for cb in self.cbs:
                    cb.notify_timer(self.tid, dwhen, *cbargs, **cbkwargs)

            if not self.repeat:  # cannot repeat
                self._reset_when(ddate)  # reset and mark as called on ddate
                return

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
                    self.dtwhen = date2num(dwhen)  # float timestamp
                    # Get the localized expected next time
                    if self._isdata:
                        self.dwhen = self.tzdata.num2date(dtwhen)
                    else:  # assume pytz compatible or None
                        self.dwhen = num2date(dtwhen, tz=tzdata)

                    break
