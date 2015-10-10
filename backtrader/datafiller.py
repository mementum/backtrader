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

import collections
import datetime

from backtrader import AbstractDataBase, TimeFrame, date2num, num2date


class DataFiller(AbstractDataBase):
    '''This class will fill gaps in the source data using the following
    information bits from the underlying data source

      - timeframe and compression to dimension the output bars

      - sessionstart and sessionend
    '''

    params = (
        ('fill_vol', 0.0),
        ('fill_oi', 0.0),
        )

    def start(self):
        super(DataFiller, self).start()
        self._fillbars = collections.deque()
        self._dbar = False

    def preload(self):
        if len(self.p.dataname) == self.p.dataname.buflen():
            # if data is not preloaded .... do it
            self.p.dataname.start()
            self.p.dataname.preload()
            self.p.dataname.home()

        # Copy timeframe from data after start (some sources do autodetection)
        self.p.timeframe = self._timeframe = self.p.dataname._timeframe
        self.p.compression = self._compression = self.p.dataname._compression

        super(DataFiller, self).preload()

    def _copyfromdata(self):
        # Data is allowed - Copy size which is "number of lines"
        for i in range(self.p.dataname.size()):
            self.lines[i][0] = self.p.dataname.lines[i][0]

        self._dbar = False  # invalidate flag for read bar

        return True

    def _frombars(self):
        dtime, price = self._fillbars.popleft()

        self.lines.datetime[0] = date2num(dtime)
        self.lines.open[0] = price
        self.lines.high[0] = price
        self.lines.low[0] = price
        self.lines.close[0] = price
        self.lines.volume[0] = self.p.fill_vol
        self.lines.openinterest[0] = self.p.fill_oi

        return True

    # Minimum delta unit in between bars
    _tdeltas = {
        TimeFrame.Minutes: datetime.timedelta(seconds=60),
        TimeFrame.Seconds: datetime.timedelta(seconds=1),
        TimeFrame.MicroSeconds: datetime.timedelta(microseconds=1),
    }

    def _load(self):
        if not len(self.p.dataname):
            self.p.dataname.start()  # start data if not done somewhere else

            # Copy from underlying data
            self._timeframe = self.p.dataname._timeframe
            self._compression = self.p.dataname._compression

            self.p.timeframe = self._timeframe
            self.p.compression = self._compression

            # Calculate and save timedelta for timeframe
            self._tdunit = self._tdeltas[self._timeframe]
            self._tdunit *= self._compression

        if self._fillbars:
            return self._frombars()

        # use existing bar or fetch a bar
        self._dbar = self._dbar or self.p.dataname.next()
        if not self._dbar:
            return False  # no more data

        if len(self) == 1:
            # Cannot yet look backwards - deliver data as is
            return self._copyfromdata()

        # previous (delivered) close
        pclose = self.lines.close[-1]
        # Get time of previous (already delivered) bar
        dtime_prev = self.lines.datetime.datetime(-1)
        # Get time of current (from data source) bar
        dtime_cur = self.p.dataname.datetime.datetime(0)

        # Calculate session end for previous bar
        dtnum_prev = self.lines.datetime.dt(-1)
        send_num = dtnum_prev + self.sessionend
        send = num2date(send_num)

        if dtime_cur > send:  # if jumped boundary
            # 1. check for missing bars until boundary (end)
            dtime_prev += self._tdunit
            while dtime_prev < send:
                self._fillbars.append((dtime_prev, pclose))
                dtime_prev += self._tdunit

            # Calculate session start for new bar
            dtnum_cur = self.p.dataname.datetime.dt(0)
            sstart_num = dtnum_cur + self.sessionstart
            sstart = num2date(sstart_num)

            # 2. check for missing bars from new boundary (start)
            # check gap from new sessionstart
            while sstart < dtime_cur:
                self._fillbars.append((sstart, pclose))
                sstart += self._tdunit
        else:
            # no boundary jumped - check gap until current time
            dtime_prev += self._tdunit
            while dtime_prev < dtime_cur:
                self._fillbars.append((dtime_prev, pclose))
                dtime_prev += self._tdunit

        if self._fillbars:
            self._dbar = True  # flag a pending data bar is available

            # return an accumulated bar in current cycle
            return self._frombars()

        return self._copyfromdata()
