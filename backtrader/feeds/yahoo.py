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

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import datetime
import io
import itertools

from six.moves import urllib

from .. import dataseries
from .. import feed
from .. import linebuffer


class YahooFinanceCSVData(feed.CSVDataFeedBase):
    params = (('adjclose', True), ('reversed', False),)

    def start(self):
        super(YahooFinanceCSVData, self).start()

        if self.params.reversed:
            return

        # Yahoo sends the data in reverse order and the file is still unreversed
        dq = collections.deque()
        for line in self.f:
            dq.appendleft(line)

        f = io.StringIO()
        f.writelines(dq)
        self.f.close()
        self.f = f

    def _loadline(self, linetokens):
        i = itertools.count(0)

        dttxt = linetokens[next(i)]
        y, m, d = int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10])

        self.lines.datetime = datetime.datetime(y, m, d)
        self.lines.open = float(linetokens[next(i)])
        self.lines.high = float(linetokens[next(i)])
        self.lines.low = float(linetokens[next(i)])
        self.lines.close = float(linetokens[next(i)])
        self.lines.volume = float(linetokens[next(i)])
        self.lines.openinterest = 0.0
        if self.params.adjclose:
            adjustedclose = float(linetokens[next(i)])
            adjfactor = self.lines.close[0] / adjustedclose

            self.lines.open = round(self.lines.open[0] / adjfactor, 2)
            self.lines.high = round(self.lines.high[0] / adjfactor, 2)
            self.lines.low = round(self.lines.low[0] / adjfactor, 2)
            self.lines.close = round(adjustedclose, 2)
            self.lines.volume = round(self.lines.volume[0] / adjfactor, 2)

        return True


class YahooFinanceCSV(feed.CSVFeedBase):
    DataCls = YahooFinanceCSVData


class YahooFinanceData(YahooFinanceCSVData):
    params = (('baseurl', 'http://ichart.yahoo.com/table.csv?'), ('period', 'd'), ('buffered', True),)

    def start(self):
        self.error = None

        url = self.params.baseurl
        url += 's=%s' % self.params.ticker
        fromdate = self.params.fromdate
        url += '&a=%d&b=%d&c=%d' % ((fromdate.month - 1), fromdate.day, fromdate.year)
        todate = self.params.todate
        url += '&d=%d&e=%d&f=%d' % ((todate.month - 1), todate.day, todate.year)
        url += '&g=%s' % self.params.period
        url += '&ignore=.csv'

        try:
            datafile = urllib.urlopen(url)
        except IOError as e:
            self.error = str(e)
            # leave us empty
            return

        if datafile.headers['Content-Type'] != 'text/csv':
            self.error = 'Wrong content type: %s' % datafile.headers
            return # HTML returned? wrong url?

        data = datafile.read()
        # Strip the BOM if present
        i = 0
        while not data[i].isalnum():
            i += 1

        if self.params.buffered:
            # buffer everything from the socket into a local buffer
            f = io.StringIO(datafile.read())
            datafile.close()
        else:
            f = datafile

        self.params.data = f

        # We have prepared a "path" file and can now let the CSV Parser take over
        super(YahooFinanceData, self).start()


class YahooFinance(feed.DataFeedBase):
    DataCls = YahooFinanceData

    params = DataCls.params._gettuple()
