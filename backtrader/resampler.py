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

from six.moves import xrange

from . import feed
from . import TimeFrame


class BaseResampler(feed.DataBase):
    def __init__(self, data):
        self.data = data
        self._name = getattr(data, '_name', '')

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

    def _barupdate(self, index=0):
        if math.isnan(self.l.open[0]):
            self._barstart()
            self.lines.open[0] = self.data.l.open[index]

        self.lines.high[0] = max(self.l.high[0], self.data.l.high[index])
        self.lines.low[0] = min(self.l.low[0], self.data.l.low[index])
        self.lines.close[0] = self.data.l.close[index]
        self.lines.volume[0] += self.data.l.volume[index]
        self.lines.openinterest[0] = self.data.l.openinterest[index]
        self.lines.datetime[0] = self.data.l.datetime[index]

    def _baroverlimit(self, index=0):
        if not self._havebar():
            # bar has not been kickstarted - can't be over the limit
            return False

        if self._timeframe > TimeFrame.Minutes:
            return self._barisover_calendar(index)

        return self._barisover_minutes(index)

    def _barisover_calendar(self, index):
        if self._timeframe == TimeFrame.Weeks:
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

        # count next finished bar datetime-wise
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

        cw = int(dt.strftime('%W'))
        barcw = int(bardt.strftime('%W'))

        return barcw > cw

    def _barisover_months(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        return bardt.month > dt.month

    def _barisover_years(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        return bardt.year > dt.year

    def _barisover_minutes(self, index):
        dt = self.lines.datetime.date(index)
        bardt = self.data.datetime.date(index)

        tm = self.lines.datetime.time(index)
        bartm = self.data.datetime.time(index)

        if bardt > dt:
            # TODO: Sessions and not only dates/days should be considered
            return True

        tmpoint = tm.hour * 60 + tm.minute
        tmmul, tmrem = divmod(tmpoint, self.p.compression)
        bartmpoint = bartm.hour * 60 + bartm.minute
        bartmmul, bartmrem = divmod(bartmpoint, self.p.compression)

        if bartmmul > tmmul and bartmrem:
            # bar pt (point) is at next multiple of minute compression
            # and is alreaady inside the range, nor right at the edge
            return True

        elif not tmrem:
            return True

        return False


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
                    break

                self._barupdate()

        else:  # next is calling via load
            distance = len(self.data) - self.lastbar
            if distance:
                # someone has moved the pointer ...
                for i in xrange(-dist, 1):
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

            self._barupdate()

        else:
            self.forward()

        return self._havebar()
