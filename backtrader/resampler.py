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

from .utils.py3 import range

from . import feed
from . import TimeFrame
from backtrader import date2num


class BaseResampler(feed.AbstractDataBase):
    params = (
        ('timelimits', True),
        ('adjtimelimits', True),
        ('limitpast', False),
    )

    def __init__(self):
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

    def _baroverlimit(self, index=0):
        if not self._havebar():
            # bar has not been kickstarted - can't be over the limit
            return False

        if self._timeframe == TimeFrame.Ticks:
            # Ticks is already the lowest level
            ret = True

        elif self._timeframe == TimeFrame.MicroSeconds:
            ret = self._barisover_minutes_sub(index, TimeFrame.MicroSeconds)

        elif self._timeframe == TimeFrame.Seconds:
            ret = self._barisover_minutes_sub(index, TimeFrame.Seconds)

        elif self._timeframe == TimeFrame.Minutes:
            ret = self._barisover_minutes_sub(index, TimeFrame.Minutes)

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

        if self.p.timelimits and \
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
        iy, barweek, iwd = bardt.isocalendar()

        return barweek > dtweek

    def _barisover_months(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        return bardt.month > dt.month

    def _barisover_years(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        return bardt.year > dt.year

    def _barisover_minutes_sub(self, index, tframe):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        tm = self.lines.datetime.time(index)
        bartm = self.data.datetime.time(index)

        if bardt > dt:
            # TODO: Sessions and not only dates/days should be considered
            return True

        if tframe == TimeFrame.Minutes:
            point = tm.hour * 60 + tm.minute
            barpoint = bartm.hour * 60 + bartm.minute
        elif tframe == TimeFrame.Seconds:
            point = tm.hour * 3600 + tm.minute * 60 + tm.second
            barpoint = bartm.hour * 3600 + bartm.minute * 60 + bartm.second
        elif tframe == TimeFrame.MicroSeconds:
            point = tm.microsecond + \
                (tm.hour * 3600 + tm.minute * 60 + tm.second) * 1000000
            barpoint = bartm.microsecond + \
                (bartm.hour * 3600 + bartm.minute * 60 + bartm.second) * 1000000

        ret = False
        if barpoint > point:
            # The data bar has surpassed the internal bar
            if not self.p.timelimits:
                # Compression to be checked outside
                ret = True

            if self.p.compression == 1:
                # no bar compression requested -> internal bar done
                ret = True

            p_major, p_minor = divmod(point, self.p.compression)
            bp_major, bp_minor = divmod(barpoint, self.p.compression)

            if bp_major > p_major:
                ret = True

            if ret and self.p.adjtimelimits:
                p_major = ((point // self.p.compression) + self.p.limitpast)
                p_major *= self.p.compression

                if tframe == TimeFrame.Minutes:
                    ph, pm = divmod(p_major, 60)
                    ps = 0
                    pus = 0
                elif tframe == TimeFrame.Seconds:
                    ph, pmin = divmod(p_major, 3600)
                    pm, ps = divmod(pmin, 60)
                    pus = 0
                elif tframe == TimeFrame.MicroSeconds:
                    ph, pmin = divmod(p_major, 36000 * 1000000)
                    pm, psec = divmod(pmin, 60 * 1000000)
                    ps, pus = divmod(psec, 1000000)

                dt = self.lines.datetime.datetime(index)
                dt = dt.replace(hour=ph, minute=pm, second=ps, microsecond=pus)
                self.lines.datetime[0] = date2num(dt)

        return ret


class DataResampler(BaseResampler):
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
        # if data.buflen() > len(data):
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
