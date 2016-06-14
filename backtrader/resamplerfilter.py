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


from datetime import datetime, date, timedelta

from .dataseries import TimeFrame, _Bar
from .utils.py3 import with_metaclass
from . import metabase
from .utils import num2date, date2num, num2time


class DTFaker(object):

    def __init__(self, sessionend, offset=timedelta()):
        self.datetime = self
        self.sessionend = sessionend
        self._dtime = datetime.now() + offset
        self._dt = date2num(self._dtime)

    def dt(self):
        return int(self._dt)

    def date(self, idx=0):
        return self._dtime.date()

    def __call__(self, idx=0):
        return self._dtime

    def time(self, idx=0):
        return self._dtime.time()

    def __getitem__(self, idx):
        # idx always 0
        return self._dt if idx == 0 else float('-inf')


class _BaseResampler(with_metaclass(metabase.MetaParams, object)):
    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', True),

        ('timeframe', TimeFrame.Days),
        ('compression', 1),

        ('takelate', True),
    )

    def __init__(self, data):
        self.subdays = TimeFrame.Ticks < self.p.timeframe < TimeFrame.Days
        self.componly = (self.subdays and
                         data._timeframe == self.p.timeframe and
                         not (self.p.compression % data._compression)
                         )

        self.bar = _Bar(maxdate=True)  # bar holder
        self.compcount = 0  # count of produced bars to control compression
        self._firstbar = True
        self.componly = self.componly and not self.subdays
        self.doadjusttime = (self.p.bar2edge and self.p.adjbartime and
                             self.subdays)

        # Modify data information according to own parameters
        data.resampling = 1
        data._timeframe = self.p.timeframe
        data._compression = self.p.compression

        self.data = data

    def _latedata(self, data):
        # new data at position 0, still untouched from stream
        if not self.subdays:
            return False

        # Time already delivered
        return len(data) > 1 and data.datetime[0] <= data.datetime[-1]

    def _checkbarover(self, data, fromcheck=False):
        if fromcheck:
            chkdata = DTFaker(sessionend=data.sessionend,
                              offset=data._timeoffset())
        else:
            chkdata = data

        isover = False
        if not self._barover(chkdata):
            return isover

        if self.subdays and self.p.bar2edge:
            isover = True
        elif not fromcheck:  # fromcheck doesn't increase compcount
            # over time/date limit - increase number of bars completed
            self.compcount += 1
            if not (self.compcount % self.p.compression):
                # boundary crossed and enough bars for compression ... proceed
                isover = True

        return isover

    def _barover(self, data):
        tframe = self.p.timeframe

        if tframe == TimeFrame.Ticks:
            # Ticks is already the lowest level
            return self.bar.isopen()

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
        '''Returns the point of time intraday for a given time according to the
        timeframe

          - Ex 1: 00:05:00 in minutes -> point = 5
          - Ex 2: 00:05:20 in seconds -> point = 5 * 60 + 20 = 320
        '''
        point = tm.hour * 60 + tm.minute
        restpoint = 0

        if self.p.timeframe < TimeFrame.Minutes:
            point = point * 60 + tm.second

            if self.p.timeframe < TimeFrame.Seconds:
                point = point * 1e6 + tm.microsecond
            else:
                restpoint = tm.microsecond
        else:
            restpoint = tm.second + tm.microsecond

        return point, restpoint

    def _barover_subdays(self, data):
        # Put session end in context of last bar datetime
        sessend = int(self.bar.datetime) + data.sessionend

        if data.datetime[0] > sessend:
            # Next session is on (defaults to next day)
            return True

        if data.datetime.datetime() <= num2date(self.bar.datetime):
            return False

        # Get time objects for the comparisons
        tm = num2time(self.bar.datetime)
        bartm = data.datetime.time()

        point, _ = self._gettmpoint(tm)
        barpoint, _ = self._gettmpoint(bartm)

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

    def check(self, data):
        '''Called to check if the current stored bar has to be delivered in
        spite of the data not having moved forward. If no ticks from a live
        feed come in, a 5 second resampled bar could be delivered 20 seconds
        later. When this method is called the wall clock (incl data time
        offset) is called to check if the time has gone so far as to have to
        deliver the already stored data
        '''
        if not self.bar.isopen():
            return

        return self(data, fromcheck=True)

    def _dataonedge(self, data):
        if not self.subdays:  # only for subdays
            return False

        point, prest = self._gettmpoint(data.datetime.time())
        if prest:
            return False  # cannot be on boundary, subunits presetn

        # Pass through compression to get boundary and rest over boundary
        bound, brest = divmod(point, self.p.compression)

        # if no extra and decomp bound is point
        return brest == 0 and point == (bound * self.p.compression)

    def _adjusttime(self, greater=False):
        '''
        Adjusts the time of calculated bar (from underlying data source) by
        using the timeframe to the appropriate boundary, with compression taken
        into account

        Depending on param ``rightedge`` uses the starting boundary or the
        ending one
        '''
        # Get current time
        tm = num2time(self.bar.datetime)
        # Get the point of the day in the time frame unit (ex: minute 200)
        point, _ = self._gettmpoint(tm)

        # Apply compression to update the point position (comp 5 -> 200 // 5)
        # point = (point // self.p.compression)
        point = point // self.p.compression

        # If rightedge (end of boundary is activated) add it unless recursing
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

        if ph > 23:  # went over midnight:
            self.bar.datetime += ph // 24
            ph %= 24

        # Get current datetime value which was taken from data
        dt = num2date(self.bar.datetime)
        # Replace intraday parts with the calculated ones and update it
        dt = dt.replace(hour=ph, minute=pm, second=ps, microsecond=pus)

        dtnum = date2num(dt)

        if greater:  # request only replace if greater
            if dtnum > self.bar.datetime:
                self.bar.datetime = dtnum
                return True

            return False

        self.bar.datetime = dtnum
        return True


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

      - rightedge (default: True)

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
        ('rightedge', True),
    )

    replaying = False

    def last(self, data):
        '''Called when the data is no longer producing bars

        Can be called multiple times. It has the chance to (for example)
        produce extra bars which may still be accumulated and have to be
        delivered
        '''
        if self.bar.isopen():
            if self.doadjusttime:
                self._adjusttime()

            data._add2stack(self.bar.lvalues())
            self.bar.bstart(maxdate=True)  # close the bar to avoid dups
            return True

        return False

    def __call__(self, data, fromcheck=False):
        '''Called for each set of values produced by the data source'''
        consumed = False
        onedge = False
        if not fromcheck:
            if self._latedata(data):
                if not self.p.takelate:
                    data.backwards()
                    return True  # get a new bar

                self.bar.bupdate(data)  # update new or existing bar
                # push time beyond reference
                self.bar.datetime = data.datetime[-1] + 0.000001
                data.backwards()  # remove used bar
                return True

            if self.componly:  # only if not subdays
                consumed = True

            elif self._dataonedge(data):  # for subdays
                consumed = True
                onedge = True

        if consumed:
            self.bar.bupdate(data)  # update new or existing bar
            data.backwards()  # remove used bar

        if onedge or self._checkbarover(data, fromcheck=fromcheck):
            if not onedge and self.doadjusttime:
                self._adjusttime(greater=True)

            data._add2stack(self.bar.lvalues())
            self.bar.bstart(maxdate=True)  # bar delivered -> restart

        if not fromcheck:
            if not consumed:
                self.bar.bupdate(data)  # update new or existing bar
                data.backwards()  # remove used bar

        # return True  # tell the system to fetch a new bar (stack or source)
        return True


class Replayer(_BaseResampler):
    '''This class replays data of a given timeframe to a larger timeframe.

    It simulates the action of the market by slowly building up (for ex.) a
    daily bar from tick/seconds/minutes data

    Only when the bar is complete will the "length" of the data be changed
    effectively delivering a closed bar

    Params

      - bar2edge (default: True)

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

        .. note:: if this parameter is True an extra tick with the *adjusted*
                  time will be introduced at the end of the *replayed* bar

      - rightedge (default: True)

        Use the right edge of the time boundaries to set the time.

        If False and compressing to 5 seconds the time of a resampled bar for
        seconds between hh:mm:00 and hh:mm:04 will be hh:mm:00 (the starting
        boundary

        If True the used boundary for the time will be hh:mm:05 (the ending
        boundary)
    '''
    params = (
        ('bar2edge', True),
        ('adjbartime', False),
        ('rightedge', True),
    )

    replaying = True

    def __call__(self, data, fromcheck=False):
        consumed = False
        onedge = False
        takinglate = False

        if not fromcheck:
            if self._latedata(data):
                if not self.p.takelate:
                    data.backwards(force=True)
                    return True  # get a new bar

                consumed = True
                takinglate = True

            elif self.componly:  # only if not subdays
                consumed = True

            elif self._dataonedge(data):  # for subdays
                consumed = True
                onedge = True

            data._tick_fill(force=True)  # update

        if consumed:
            self.bar.bupdate(data)
            if takinglate:
                self.bar.datetime = data.datetime[-1] + 0.000001

        if onedge or self._checkbarover(data, fromcheck=fromcheck):
            if not onedge and self.doadjusttime:  # insert tick with adjtime
                adjusted = self._adjusttime(greater=True)
                if adjusted:
                    ago = 0 if (consumed or fromcheck) else -1
                    # Update to the point right before the new data
                    data._updatebar(self.bar.lvalues(), forward=False, ago=ago)

                if not fromcheck:
                    if not consumed:
                        # Reopen bar with real new data and save data to queue
                        self.bar.bupdate(data, reopen=True)
                        # erase is True, but the tick will not be seen below
                        # and therefore no need to mark as 1st
                        data._save2stack(erase=True, force=True)
                    else:
                        self.bar.bstart(maxdate=True)
                        self._firstbar = True  # next is first
                else:  # from check
                    # fromcheck or consumed have  forced delivery, reopen
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  # next is first
                    if adjusted:
                        # after adjusting need to redeliver if this was a check
                        data._save2stack(erase=True, force=True)

            elif not fromcheck:
                if not consumed:
                    # Data already "forwarded" and we replay to new bar
                    # No need to go backwards. simply reopen internal cache
                    self.bar.bupdate(data, reopen=True)
                else:
                    # compression only, used data to update bar, hence remove
                    # from stream, update existing data, reopen bar
                    if not self._firstbar:  # only discard data if not firstbar
                        data.backwards(force=True)
                    data._updatebar(self.bar.lvalues(), forward=False, ago=0)
                    self.bar.bstart(maxdate=True)
                    self._firstbar = True  # make sure next tick moves forward

        elif not fromcheck:
            # not over, update, remove new entry, deliver
            if not consumed:
                self.bar.bupdate(data)

            if not self._firstbar:  # only discard data if not firstbar
                data.backwards(force=True)

            data._updatebar(self.bar.lvalues(), forward=False, ago=0)
            self._firstbar = False

        return False  # the existing bar can be processed by the system


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
