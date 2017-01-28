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

import datetime

from .. import feed
from ..utils import date2num


class BacktraderCSVData(feed.CSVDataBase):
    '''
    Parses a self-defined CSV Data used for testing.

    Specific parameters:

      - ``dataname``: The filename to parse or a file-like object
    '''

    def _loadline(self, linetokens):
        itoken = iter(linetokens)

        dttxt = next(itoken)
        # Format is YYYY-MM-DD
        y = int(dttxt[0:4])
        m = int(dttxt[5:7])
        d = int(dttxt[8:10])

        if len(linetokens) == 8:
            tmtxt = next(itoken)

            # Format if present HH:MM:SS
            hh = int(tmtxt[0:2])
            mm = int(tmtxt[3:5])
            ss = int(tmtxt[6:8])
        else:
            # put it at the end of the session parameter
            hh = self.p.sessionend.hour
            mm = self.p.sessionend.minute
            ss = self.p.sessionend.second

        dt = datetime.datetime(y, m, d, hh, mm, ss)
        dtnum = date2num(dt)

        self.lines.datetime[0] = dtnum
        self.lines.open[0] = float(next(itoken))
        self.lines.high[0] = float(next(itoken))
        self.lines.low[0] = float(next(itoken))
        self.lines.close[0] = float(next(itoken))
        self.lines.volume[0] = float(next(itoken))
        self.lines.openinterest[0] = float(next(itoken))

        return True


class BacktraderCSV(feed.CSVFeedBase):
    DataCls = BacktraderCSVData
