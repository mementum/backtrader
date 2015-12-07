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

import math

from backtrader import date2num, AbstractDataBase, TimeFrame
from backtrader.utils.py3 import with_metaclass


class MetaBaseResampler(AbstractDataBase.__class__):
    '''
    Inserted as metaclass for BaseResampler to make the 1.1.12.88 parameter
    names compatible with later releases
    '''
    def donew(cls, *args, **kwargs):
        # Translate parameter names from 1.1.12.88 to names given after
        _translate = dict(timelimits='bar2edge',
                          adjtimelimits='adjbartime', limitpast='rightedge')

        for name, newname in _translate.items():
            if name in kwargs:
                kwargs[newname] = kwargs.pop(name)

        # Create the object and set the params in place
        _obj, args, kwargs = \
            super(MetaBaseResampler, cls).donew(*args, **kwargs)

        # Parameter values have now been set before __init__
        return _obj, args, kwargs


class BaseResampler(with_metaclass(MetaBaseResampler, AbstractDataBase)):
    params = (
        ('bar2edge', True),
        ('adjbartime', True),
        ('rightedge', False),
    )

    def __init__(self):
        super(BaseResampler, self).__init__()
        self.data = self.p.dataname
        self._name = getattr(self.data, '_name', '')

    def ringbuffer(self, maxlen=-1):
        super(BaseResampler, self).ringbuffer(maxlen=maxlen)

        # Activate it for the data under control. Becasue it could
        # be controlled by the strategy itself, pass the default -1
        # to let it autochoose (already set or 1)
        self.data.ringbuffer(maxlen=-1)

    def start(self):
        super(BaseResampler, self).start()
        self._samplecount = 0

    def _havebar(self):
        return not math.isnan(self.lines.open[0])

    def _barstart(self):
        # self.lines.open[0] = 0.0
        self.lines.high[0] = float('-inf')
        self.lines.low[0] = float('inf')
        # self.lines.close[0] = 0.0
        self.lines.volume[0] = 0.0
        # self.lines.openinterest[0] = 0.0
        # self.lines.datetime[0] = 0.0

    def _barupdate(self, index=0, replaying=False):
        sstart = self.data.datetime.tm2dtime(self.sessionstart)
        send = self.data.datetime.tm2dtime(self.sessionend)
        if sstart > self.data.datetime[index] > sessend:
            # Not within session limits - skip the bar
            return

        if math.isnan(self.l.open[0]):
            self._barstart()
            self.lines.open[0] = self.data.l.open[index]

        self.lines.high[0] = max(self.l.high[0], self.data.l.high[index])
        self.lines.low[0] = min(self.l.low[0], self.data.l.low[index])
        self.lines.close[0] = self.data.l.close[index]
        self.lines.volume[0] += self.data.l.volume[index]
        self.lines.openinterest[0] = self.data.l.openinterest[index]
        self.lines.datetime[0] = self.data.l.datetime[index]

        if replaying:
            self.tick_open = self.data.lines.open[index]
            self.tick_high = self.data.lines.high[index]
            self.tick_low = self.data.lines.low[index]
            self.tick_close = self.tick_last = self.data.lines.close[index]
            self.tick_volume = self.data.lines.volume[index]
            self.tick_openinterest = self.data.lines.openinterest[index]

        if TimeFrame.Ticks < self._timeframe < TimeFrame.Days:
            # Adjust resampled to the time limit for micro/seconds/minutes
            if self.p.bar2edge and self.p.adjbartime:
                self._adjusttime(index)

    def _baroverlimit(self, index=0):
        if not self._havebar():
            # bar has not been kickstarted - can't be over the limit
            return False

        if self._timeframe == TimeFrame.Ticks:
            # Ticks is already the lowest level
            ret = True

        elif self._timeframe < TimeFrame.Days:
            ret = self._barisover_minutes_sub(index)

        elif self._timeframe == TimeFrame.Weeks:
            ret = self._barisover_weeks(index)

        elif self._timeframe == TimeFrame.Months:
            ret = self._barisover_months(index)

        elif self._timeframe == TimeFrame.Years:
            ret = self._barisover_years(index)

        else:  # self._timeframe == TimeFrame.Days
            ret = self._barisover_days(index)

        if not ret:
            # if not over say so to have the chance to accum more
            return False

        if self.p.bar2edge and \
           self._timeframe in [TimeFrame.MicroSeconds,
                               TimeFrame.Seconds,
                               TimeFrame.Minutes]:

            # Compression limit already calculated by the methods
            pass
        else:
            # count next number of bars
            self._samplecount += 1

            if self._samplecount % self.p.compression:
                # compression level not reached yet, not over limit
                return False

        # datewise over and compression reached ... over the limit
        return True

    def _barisover_days(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        return bardt > dt

    def _barisover_weeks(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        iy, dtweek, iwd = dt.isocalendar()
        biy, barweek, biwd = bardt.isocalendar()

        return (biy * 100 + barweek) > (iy * 100 + dtweek)

    def _barisover_months(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        return (bardt.year * 100 + bardt.month) > (dt.year * 100 + dt.month)

    def _barisover_years(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        return bardt.year > dt.year

    def _barisover_minutes_sub(self, index):
        # Put session end of cached internal bar in context of current time
        sessend = self.lines.datetime.tm2dtime(self.sessionend)

        if self.data.datetime[index] > sessend:
            return True

        tm = self.lines.datetime.time(index)
        bartm = self.data.datetime.time(index)

        point = self._gettmpoint(tm)
        barpoint = self._gettmpoint(bartm)

        ret = False
        if barpoint > point:
            # The data bar has surpassed the internal bar
            if not self.p.bar2edge:
                # Compression to be ochecked outside
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

    def _gettmpoint(self, tm):
        '''
        Returns the point of time intraday for a given time according to the
        timeframe

          - Ex 1: 00:05:00 in minutes -> point = 5
          - Ex 2: 00:05:20 in seconds -> point = 5 * 60 + 20 = 320
        '''
        point = tm.hour * 60 + tm.minute

        if self._timeframe < TimeFrame.Minutes:
            point = point * 60 + tm.second

        if self._timeframe < TimeFrame.Seconds:
            point = point * 1e6 + tm.microsecond

        return point

    def _adjusttime(self, index=0):
        '''
        Adjusts the time of calculated bar (from underlying data source) by
        using the timeframe to the appropriate boundary taken int account
        compression

        Depending on param ``rightedge`` uses the starting boundary or the
        ending one
        '''
        # Get current time
        tm = self.lines.datetime.time(0)
        # Get the point of the day in the time frame unit (ex: minute 200)
        point = self._gettmpoint(tm)

        # Apply compression to update the point position (comp 5 -> 200 // 5)
        point = (point // self.p.compression)
        # If rightedge (end of boundary is activated) add it
        if point % self.p.compression:
            point += self.p.rightedge

        # Restore point to the timeframe units by de-applying compression
        point *= self.p.compression

        # Get hours, minutes, seconds and microseconds
        if self._timeframe == TimeFrame.Minutes:
            ph, pm = divmod(point, 60)
            ps = 0
            pus = 0
        elif self._timeframe == TimeFrame.Seconds:
            ph, pm = divmod(point, 60 * 60)
            pm, ps = divmod(pm, 60)
            pus = 0
        elif self._timeframe == TimeFrame.MicroSeconds:
            ph, pm = divmod(point, 60 * 60 * 1e6)
            pm, psec = divmod(pm, 60 * 1e6)
            ps, pus = divmod(psec, 1e6)

        # Get current datetime value which was taken from data
        dt = self.lines.datetime.datetime(index)
        # Replace intraday parts with the calculated ones and update it
        dt = dt.replace(hour=ph, minute=pm, second=ps, microsecond=pus)
        self.lines.datetime[0] = date2num(dt)


class DataResampler(BaseResampler):
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

    def start(self):
        super(DataResampler, self).start()
        self._preloading = False
        self.lastbar = 0

    def preload(self):
        if len(self.data) == self.data.buflen():
            # if data is not preloaded .... do it
            self.data.start()
            self.data.preload()
            self.data.home()

        self._preloading = True
        super(DataResampler, self).preload()
        self.data.home()
        self._preloading = False

    def _load(self):
        if self._preloading:
            # data is preloaded, we are preloading too, can move
            # forward until have full bar or data source is exhausted
            while True:
                self.data.advance()
                if len(self.data) > self.data.buflen():
                    break

                if self._baroverlimit():
                    self.data.rewind()
                    break

                self._barupdate()

        else:  # next is calling via load
            distance = len(self.data) - self.lastbar
            if distance:
                # someone has moved the pointer ...
                for i in range(-distance, 1):
                    if self._baroverlimit(i):
                        return self._havebar()

                    self.lastbar += 1
                    self._barupdate(i)

            else:
                # data is under control of this resampler
                if not len(self.data):
                    self.data.start()

                while self.data.next():
                    if self._baroverlimit():
                        self.data.rewind()
                        break

                    self.lastbar += 1
                    self._barupdate()

        return self._havebar()


class DataReplayer(BaseResampler):
    params = (
        ('bar2edge', False),  # changed
        ('adjbartime', False),  # changed
        ('rightedge', False),
    )

    def start(self):
        super(DataReplayer, self).start()
        self._firstbar = True

    def preload(self):
        raise NotImplementedError('Replay does not support preloading')

    def _load(self):
        # data MUST BE under control of this resampler
        if not len(self.data):
            self.data.start()

        if not self._firstbar:
            self.backwards()  # still in same bar
        else:
            self._firstbar = False

        if self.data.next():
            if self._baroverlimit():
                self.forward()

            self._barupdate(replaying=True)

        else:
            self.forward()

        return self._havebar()
