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

from .dataseries import TimeFrame, _Bar
from .utils.py3 import with_metaclass
from . import metabase
from .utils import num2date, date2num, num2time


class _BaseResampler(with_metaclass(metabase.MetaParams, object)):
    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', False),

        ('timeframe', TimeFrame.Days),
        ('compression', 1),
    )

    def __init__(self, data):
        # Modify data information according to own parameters
        data._timeframe = self.p.timeframe
        data._compression = self.p.compression

        self.bar = _Bar(maxdate=True)  # bar holder
        self.compcount = 0  # count of produced bars to control compression
        self._firstbar = True

    def _checkbarover(self, data):
        if not self._barover(data):
            return False

        ret = False
        if (self.p.bar2edge and
            self.p.timeframe in [TimeFrame.MicroSeconds,
                                 TimeFrame.Seconds,
                                 TimeFrame.Minutes]):

            ret = True
        else:
            # over time/date limit - increase number of bars completed
            self.compcount += 1
            if not (self.compcount % self.p.compression):
                # boundary crossed and enough bars for compression ... proceed
                ret = True

        if ret:
            self._baroverdeliver(data)

        return ret

    def _baroverdeliver(self, data):
        if not self.replaying:
            if TimeFrame.Ticks < self.p.timeframe < TimeFrame.Days:
                # Adjust resampled to time limit for micro/seconds/minutes
                if self.p.bar2edge and self.p.adjbartime:
                    self._adjusttime()
            # deliver bar
            data._add2stack(list(self.bar.values()))

        # re-init bar
        self.bar.bstart()

    def last(self, data):
        '''Called when the data is no longer producing bars

        Can be called multiple times. It has the chance to (for example)
        produce extra bars which may still be accumulated and have to be
        delivered
        '''
        if not self.replaying and self.bar.isopen():
            self._baroverdeliver(data)
            return True

        return False

    def _barover(self, data):
        tframe = self.p.timeframe

        if tframe == TimeFrame.Ticks:
            # Ticks is already the lowest level
            return True

        elif tframe < TimeFrame.Days:
            return self._barover_subdays(data)

        elif tframe == TimeFrame.Days:
            return self._barover_days(data)

        elif tframe == TimeFrame.Weeks:
            return self._barover_weeks(data)

        elif tframe == TimeFrame.Months:
            return self._barover_months(data)

        elif tframe == TimeFrame.Years:
            return self._barover_years(data)

    def _barover_days(self, data):
        return data.datetime.dt() > int(self.bar.datetime)

    def _barover_weeks(self, data):
        year, week, _ = num2date(self.bar.datetime).isocalendar()
        yearweek = year * 100 + week

        baryear, barweek, _ = data.datetime.date().isocalendar()
        bar_yearweek = baryear * 100 + barweek

        return bar_yearweek > yearweek

    def _barover_months(self, data):
        dt = num2date(self.bar.datetime)
        yearmonth = dt.year * 100 + dt.month

        bardt = data.datetime.datetime()
        bar_yearmonth = bardt.year * 100 + bardt.month

        return bar_yearmonth > yearmonth

    def _barover_years(self, data):
        return data.datetime.date().year > num2date(self.bar.datetime).year

    def _gettmpoint(self, tm):
        '''
        Returns the point of time intraday for a given time according to the
        timeframe

          - Ex 1: 00:05:00 in minutes -> point = 5
          - Ex 2: 00:05:20 in seconds -> point = 5 * 60 + 20 = 320
        '''
        point = tm.hour * 60 + tm.minute

        if self.p.timeframe < TimeFrame.Minutes:
            point = point * 60 + tm.second

        if self.p.timeframe < TimeFrame.Seconds:
            point = point * 1e6 + tm.microsecond

        return point

    def _barover_subdays(self, data):
        # Put session end in context of current datetime
        sessend = data.datetime.tm2dtime(data.sessionend)

        if data.datetime[0] > sessend:
            # Next session is on (defaults to next day)
            return True

        if data.datetime[0] <= self.bar.datetime:
            return False

        # Get time objects for the comparisons
        tm = num2time(self.bar.datetime)
        bartm = data.datetime.time()

        point = self._gettmpoint(tm)
        barpoint = self._gettmpoint(bartm)

        ret = False
        if barpoint > point:
            # The data bar has surpassed the internal bar
            if not self.p.bar2edge:
                # Compression done on simple bar basis (like days)
                ret = True
            elif self.p.compression == 1:
                # no bar compression requested -> internal bar done
                ret = True
            else:
                point_comp = point // self.p.compression
                barpoint_comp = barpoint // self.p.compression

                # Went over boundary including compression
                if barpoint_comp > point_comp:
                    ret = True

        return ret

    def _adjusttime(self):
        '''
        Adjusts the time of calculated bar (from underlying data source) by
        using the timeframe to the appropriate boundary taken int account
        compression

        Depending on param ``rightedge`` uses the starting boundary or the
        ending one
        '''
        # Get current time
        tm = num2time(self.bar.datetime)
        # Get the point of the day in the time frame unit (ex: minute 200)
        point = self._gettmpoint(tm)

        # Apply compression to update the point position (comp 5 -> 200 // 5)
        # point = (point // self.p.compression)
        point = point // self.p.compression

        # If rightedge (end of boundary is activated) add it
        point += self.p.rightedge

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

        # Get current datetime value which was taken from data
        dt = num2date(self.bar.datetime)
        # Replace intraday parts with the calculated ones and update it
        dt = dt.replace(hour=ph, minute=pm, second=ps, microsecond=pus)
        self.bar.datetime = date2num(dt)


class Resampler(_BaseResampler):
    '''This class resamples data of a given timeframe to a larger timeframe.

    Params

      - bar2edge (default: True)

        resamples using time boundaries as the target. For example with a
        "ticks -> 5 seconds" the resulting 5 seconds bars will be aligned to
        xx:00, xx:05, xx:10 ...

      - adjbartime (default: True)

        Use the time at the boundary to adjust the time of the delivered
        resampled bar instead of the last seen timestamp. If resampling to "5
        seconds" the time of the bar will be adjusted for example to hh:mm:05
        even if the last seen timestamp was hh:mm:04.33

        .. note::

           Time will only be adjusted if "bar2edge" is True. It wouldn't make
           sense to adjust the time if the bar has not been aligned to a
           boundary

      - rightedge (default: False)

        Use the right edge of the time boundaries to set the time.

        If False and compressing to 5 seconds the time of a resampled bar for
        seconds between hh:mm:00 and hh:mm:04 will be hh:mm:00 (the starting
        boundary

        If True the used boundary for the time will be hh:mm:05 (the ending
        boundary)
    '''
    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', False),
    )

    replaying = False

    def __call__(self, data):
        '''Called for each set of values produced by the data source'''
        self._checkbarover(data)
        self.bar.bupdate(data)
        data.backwards()  # remove bar consumed here

        # return True to indicate the bar can no longer be used by the data
        return True


class Replayer(_BaseResampler):
    '''This class replays data of a given timeframe to a larger timeframe.

    It simulates the action of the market by slowly building up (for ex.) a
    daily bar from tick/seconds/minutes data

    Only when the bar is complete will the "length" of the data be changed
    effectively delivering a closed bar

    Params

      - bar2edge (default: False)

        replays using time boundaries as the target of the closed bar. For
        example with a "ticks -> 5 seconds" the resulting 5 seconds bars will
        be aligned to xx:00, xx:05, xx:10 ...

      - adjbartime (default: False)

        Use the time at the boundary to adjust the time of the delivered
        resampled bar instead of the last seen timestamp. If resampling to "5
        seconds" the time of the bar will be adjusted for example to hh:mm:05
        even if the last seen timestamp was hh:mm:04.33

        .. note::

           Time will only be adjusted if "bar2edge" is True. It wouldn't make
           sense to adjust the time if the bar has not been aligned to a
           boundary

      - rightedge (default: False)

        Use the right edge of the time boundaries to set the time.

        If False and compressing to 5 seconds the time of a resampled bar for
        seconds between hh:mm:00 and hh:mm:04 will be hh:mm:00 (the starting
        boundary

        If True the used boundary for the time will be hh:mm:05 (the ending
        boundary)

    '''
    params = (
        ('bar2edge', False),  # changed from base
        ('adjbartime', False),  # changed from base
        ('rightedge', False),
    )

    replaying = True

    def __call__(self, data):
        if self._checkbarover(data):
            self._firstbar = True

        # Update the tick values
        data._tick_fill(force=True)  # before we erase the data below

        # Update internal bar - before removing the data bar
        self.bar.bupdate(data)
        data.backwards()
        # deliver current bar too
        data._updatebar(list(self.bar.values()), forward=self._firstbar)
        self._firstbar = False

        return False  # nothing removed from the system


class ResamplerTicks(Resampler):
    params = (('timeframe', TimeFrame.Ticks),)


class ResamplerSeconds(Resampler):
    params = (('timeframe', TimeFrame.Seconds),)


class ResamplerMinutes(Resampler):
    params = (('timeframe', TimeFrame.Minutes),)


class ResamplerDaily(Resampler):
    params = (('timeframe', TimeFrame.Days),)


class ResamplerWeekly(Resampler):
    params = (('timeframe', TimeFrame.Weeks),)


class ResamplerMonthly(Resampler):
    params = (('timeframe', TimeFrame.Months),)


class ResamplerYearly(Resampler):
    params = (('timeframe', TimeFrame.Years),)


class ReplayerTicks(Replayer):
    params = (('timeframe', TimeFrame.Ticks),)


class ReplayerSeconds(Replayer):
    params = (('timeframe', TimeFrame.Seconds),)


class ReplayerMinutes(Replayer):
    params = (('timeframe', TimeFrame.Minutes),)


class ReplayerDaily(Replayer):
    params = (('timeframe', TimeFrame.Days),)


class ReplayerWeekly(Replayer):
    params = (('timeframe', TimeFrame.Weeks),)


class ReplayerMonthly(Replayer):
    params = (('timeframe', TimeFrame.Months),)
