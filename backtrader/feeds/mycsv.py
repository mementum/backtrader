#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
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
################################################################################
import datetime
import itertools

from .. import dataseries
from .. import feed
from .. import linebuffer


class MyCSVData(feed.CSVDataFeedBase):
    def _load(self, linetokens):
        i = itertools.count(0)
        i.next() # skip ticker name
        i.next() # skip daily/intraday indication (intraday has simply a "null" time)

        dttxt = linetokens[i.next()]
        y, m, d = int(dttxt[0:4]), int(dttxt[4:6]), int(dttxt[6:8])

        tmtxt = linetokens[i.next()]
        hh, mmss = divmod(int(tmtxt), 10000)
        mm, ss = divmod(mmss, 100)

        self.lines.datetime = datetime.datetime(y, m, d, hh, mm, ss)
        self.lines.open = float(linetokens[i.next()])
        self.lines.high = float(linetokens[i.next()])
        self.lines.low = float(linetokens[i.next()])
        self.lines.close = float(linetokens[i.next()])
        self.lines.volume = float(linetokens[i.next()])
        self.lines.openinterest = float(linetokens[i.next()])

        return True


class MyCSV(feed.CSVFeedBase):
    DataCls = MyCSVData
