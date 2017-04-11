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


from datetime import timedelta, time

from .metabase import MetaParams
from backtrader.utils.py3 import string_types, with_metaclass

__all__ = ['TradingCalendarBase', 'TradingCalendar', 'PandasMarketCalendar']

# Imprecission in the full time conversion to float would wrap over to next day
# if microseconds is 999999 as defined in time.max
_time_max = time(hour=23, minute=59, second=59, microsecond=999990)


MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)
(ISONODAY, ISOMONDAY, ISOTUESDAY, ISOWEDNESDAY, ISOTHURSDAY, ISOFRIDAY,
 ISOSATURDAY, ISOSUNDAY) = range(8)

WEEKEND = [SATURDAY, SUNDAY]
ISOWEEKEND = [ISOSATURDAY, ISOSUNDAY]
ONEDAY = timedelta(days=1)


class TradingCalendarBase(with_metaclass(MetaParams, object)):
    def _nextday(self, day):
        '''
        Returns the next trading day (datetime/date instance) after ``day``
        (datetime/date instance) and the isocalendar components

        The return value is a tuple with 2 components: (nextday, (y, w, d))
        '''
        raise NotImplementedError

    def schedule(self, day):
        '''
        Returns a tuple with the opening and closing times (``datetime.time``)
        for the given ``date`` (``datetime/date`` instance)
        '''
        raise NotImplementedError


class TradingCalendar(TradingCalendarBase):
    params = (
        ('open', time.min),
        ('close', _time_max),
        ('holidays', []),  # list of non trading days (date)
        ('earlydays', []),  # list of tuples (date, opentime, closetime)
        ('offdays', ISOWEEKEND),  # list of non trading (isoweekdays)
    )

    def schedule(self, day):
        '''
        Returns a tuple with the opening and closing times (``datetime.time``)
        for the given ``date`` (``datetime/date`` instance)
        '''
        pass

    def _nextday(self, day):
        '''
        Returns the next trading day (datetime/date instance) after ``day``
        (datetime/date instance) and the isocalendar components

        The return value is a tuple with 2 components: (nextday, (y, w, d))
        '''
        while True:
            day += ONEDAY
            isocal = day.isocalendar()
            if isocal[2] in self.p.offdays or day in self.p.holidays():
                continue

            return day, isocal

    def nextday(self, day):
        '''
        Returns the next trading day (datetime/date instance) after ``day``
        (datetime/date instance)
        '''
        return self._next_day(day)[0]  # 1st ret elem is next day

    def nextday_week(self, day):
        '''
        Returns the iso week number of the next trading day, given a ``day``
        (datetime/date) instance
        '''
        self._nextday(day)[1][1]  # 2 elem is isocal / 0 - y, 1 - wk, 2 - day

    def last_weekday(self, day):
        '''
        Returns ``True`` if the given ``day`` (datetime/date) instance is the
        last trading day of this week
        '''
        # Next day must be greater than day. If the week changes is enough for
        # a week change even if the number is smaller (year change)
        return day.isocalendar()[1] != self._nextday(day)[1][1]


class PandasMarketCalendar(TradingCalendarBase):
    params = (
        ('calendar', None),  # A pandas_market_calendar instance or exch name
    )

    def __init__(self):
        self._calendar = self.p.calendar

        if isinstance(self._calendar, string_types):  # use passed mkt name
            import pandas_market_calendar as mcal
            self._calendar = mcal.get_calendar(self._calendar)

    def _nextday(self, day):
        '''
        Returns the next trading day (datetime/date instance) after ``day``
        (datetime/date instance) and the isocalendar components

        The return value is a tuple with 2 components: (nextday, (y, w, d))
        '''
        while True:
            day += ONEDAY
            valid = self._calendar.valid_days(day, day)
            if valid:  # has something
                return valid.to_pydatetime()[0]
