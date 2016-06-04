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

import datetime
import time as _time

ZERO = datetime.timedelta(0)

STDOFFSET = datetime.timedelta(seconds=-_time.timezone)
if _time.daylight:
    DSTOFFSET = datetime.timedelta(seconds=-_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET


# A UTC class, same as the one in the Python Docs
class _UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


class _LocalTimezone(datetime.tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0


UTC = _UTC()
TZLocal = _LocalTimezone()


HOURS_PER_DAY = 24.0
MINUTES_PER_HOUR = 60.0
SECONDS_PER_MINUTE = 60.0
MUSECONDS_PER_SECOND = 1e6
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY
SECONDS_PER_DAY = SECONDS_PER_MINUTE * MINUTES_PER_DAY
MUSECONDS_PER_DAY = MUSECONDS_PER_SECOND * SECONDS_PER_DAY


def _num2date(x, tz=None):
    # Same as matplotlib except if tz is None a naive datetime object
    # will be returned.
    """
    *x* is a float value which gives the number of days
    (fraction part represents hours, minutes, seconds) since
    0001-01-01 00:00:00 UTC *plus* *one*.
    The addition of one here is a historical artifact.  Also, note
    that the Gregorian calendar is assumed; this is not universal
    practice.  For details, see the module docstring.
    Return value is a :class:`datetime` instance in timezone *tz* (default to
    rcparams TZ value).
    If *x* is a sequence, a sequence of :class:`datetime` objects will
    be returned.
    """

    ix = int(x)
    dt = datetime.datetime.fromordinal(ix)
    remainder = float(x) - ix
    hour, remainder = divmod(HOURS_PER_DAY * remainder, 1)
    minute, remainder = divmod(MINUTES_PER_HOUR * remainder, 1)
    second, remainder = divmod(SECONDS_PER_MINUTE * remainder, 1)
    microsecond = int(MUSECONDS_PER_SECOND * remainder)
    if microsecond < 10:
        microsecond = 0  # compensate for rounding errors

    if tz is not None:
        dt = datetime.datetime(
            dt.year, dt.month, dt.day, int(hour), int(minute), int(second),
            microsecond, tzinfo=UTC).astimezone(tz).replace(tzinfo=None)
    else:
        # If not tz has been passed return a non-timezoned dt
        dt = datetime.datetime(
            dt.year, dt.month, dt.day, int(hour), int(minute), int(second),
            microsecond)

    if microsecond > 999990:  # compensate for rounding errors
        dt += datetime.timedelta(microseconds=1e6 - microsecond)

    return dt


def _num2dt(x, tz=None):
    ix = int(x)
    return datetime.datetime.fromordinal(ix)


def _date2num(dt):
    """
    Convert :mod:`datetime` to the Gregorian date as UTC float days,
    preserving hours, minutes, seconds and microseconds.  Return value
    is a :func:`float`.
    """
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        delta = dt.tzinfo.utcoffset(dt)
        if delta is not None:
            dt -= delta

    base = float(dt.toordinal())
    if hasattr(dt, 'hour'):
        base += (dt.hour / HOURS_PER_DAY +
                 dt.minute / MINUTES_PER_DAY +
                 dt.second / SECONDS_PER_DAY +
                 dt.microsecond / MUSECONDS_PER_DAY
                 )
    return base


def time2num(tm):
    """
    Convert :mod:`time` to the to the preserving hours, minutes, seconds
    and microseconds.  Return value is a :func:`float`.
    """
    num = (tm.hour / HOURS_PER_DAY +
           tm.minute / MINUTES_PER_DAY +
           tm.second / SECONDS_PER_DAY +
           tm.microsecond / MUSECONDS_PER_DAY)

    return num


def num2time(num):
    ix = int(num)
    remainder = float(num) - ix

    hour, remainder = divmod(HOURS_PER_DAY * remainder, 1)
    minute, remainder = divmod(MINUTES_PER_HOUR * remainder, 1)
    second, remainder = divmod(SECONDS_PER_MINUTE * remainder, 1)
    microsecond = int(MUSECONDS_PER_SECOND * remainder)
    if microsecond < 10:
        microsecond = 0  # compensate for rounding errors

    # If not tz has been passed return a non-timezoned dt
    dt = datetime.datetime.min.replace(hour=int(hour),
                                       minute=int(minute),
                                       second=int(second),
                                       microsecond=microsecond)

    if microsecond > 999990:  # compensate for rounding errors
        dt += datetime.timedelta(microseconds=1e6 - microsecond)

    return dt.time()
