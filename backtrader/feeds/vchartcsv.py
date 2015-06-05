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
import itertools

from .. import feed
from .. import TimeFrame
from ..utils import date2num


class VChartCSVData(feed.CSVDataBase):
    vctframes = dict(
        I=TimeFrame.Minutes,
        D=TimeFrame.Days,
        W=TimeFrame.Weeks,
        M=TimeFrame.Months)

    def _loadline(self, linetokens):
        i = itertools.count(0)
        ticker = linetokens[next(i)]  # skip ticker name
        if not self._name:
            self._name = ticker

        # day/intraday indication
        timeframe = linetokens[next(i)]

        self._timeframe = self.vctframes[timeframe]

        dttxt = linetokens[next(i)]
        y, m, d = int(dttxt[0:4]), int(dttxt[4:6]), int(dttxt[6:8])

        tmtxt = linetokens[next(i)]
        if timeframe == 'I':
            # use the provided time
            hh, mmss = divmod(int(tmtxt), 10000)
            mm, ss = divmod(mmss, 100)
            tm = datetime.time(hh, mm, ss)
        else:
            # put it at the end of the session parameter
            hh = self.p.sessionend.hour
            mm = self.p.sessionend.minute
            ss = self.p.sessionend.second

        dtnum = date2num(datetime.datetime(y, m, d, hh, mm, ss))

        self.lines.datetime[0] = dtnum
        self.lines.open[0] = float(linetokens[next(i)])
        self.lines.high[0] = float(linetokens[next(i)])
        self.lines.low[0] = float(linetokens[next(i)])
        self.lines.close[0] = float(linetokens[next(i)])
        self.lines.volume[0] = float(linetokens[next(i)])
        self.lines.openinterest[0] = float(linetokens[next(i)])

        return True


class VChartCSV(feed.CSVFeedBase):
    DataCls = VChartCSVData
