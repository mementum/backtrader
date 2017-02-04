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

import collections
import datetime
import io
import itertools

from ..utils.py3 import urlopen, urlquote


from .. import feed
from ..utils import date2num


class YahooFinanceCSVData(feed.CSVDataBase):
    '''
    Parses pre-downloaded Yahoo CSV Data Feeds (or locally generated if they
    comply to the Yahoo format)

    Specific parameters:

      - ``dataname``: The filename to parse or a file-like object

      - ``reverse`` (default: ``False``)

        It is assumed that locally stored files have already been reversed
        during the download process

      - ``adjclose`` (default: ``True``)

        Whether to use the dividend/split adjusted close and adjust all
        values according to it.

      - ``round`` (default: ``True``)

        Whether to round the values to a specific number of decimals after
        having adjusted the close

      - ``decimals`` (default: ``2``)

        Number of decimals to round to
    '''
    params = (
        ('reverse', False),
        ('adjclose', True),
        ('round', True),
        ('decimals', 2),
    )

    def start(self):
        super(YahooFinanceCSVData, self).start()

        if not self.params.reverse:
            return

        # Yahoo sends data in reverse order and the file is still unreversed
        dq = collections.deque()
        for line in self.f:
            dq.appendleft(line)

        f = io.StringIO(newline=None)
        f.writelines(dq)
        f.seek(0)
        self.f.close()
        self.f = f

    def _loadline(self, linetokens):
        i = itertools.count(0)

        dttxt = linetokens[next(i)]
        y, m, d = int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10])

        # get the time from the sessionend parameter
        hh = self.p.sessionend.hour
        mm = self.p.sessionend.minute
        ss = self.p.sessionend.second
        dtnum = date2num(datetime.datetime(y, m, d, hh, mm, ss))

        self.lines.datetime[0] = dtnum
        o = float(linetokens[next(i)])
        h = float(linetokens[next(i)])
        l = float(linetokens[next(i)])
        c = float(linetokens[next(i)])
        v = float(linetokens[next(i)])
        self.lines.openinterest[0] = 0.0

        if self.params.adjclose:
            adjustedclose = float(linetokens[next(i)])
            adjfactor = c / adjustedclose

            o /= adjfactor
            h /= adjfactor
            l /= adjfactor
            c = adjustedclose
            v /= adjfactor

            if self.p.round:
                decimals = self.p.decimals
                o = round(o, decimals)
                h = round(h, decimals)
                l = round(l, decimals)
                c = round(c, decimals)
                v = round(v, decimals)

        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v

        return True


class YahooFinanceCSV(feed.CSVFeedBase):
    DataCls = YahooFinanceCSVData


class YahooFinanceData(YahooFinanceCSVData):
    '''
    Executes a direct download of data from Yahoo servers for the given time
    range.

    Specific parameters (or specific meaning):

      - ``dataname``

        The ticker to download ('YHOO' for Yahoo own stock quotes)

      - ``baseurl``

        The server url. Someone might decide to open a Yahoo compatible service
        in the future.

      - ``period``

        The timeframe to download data in. Pass 'w' for weekly and 'm' for
        monthly.

      - ``buffered``

        If True the entire socket connection wil be buffered locally before
        parsing starts.

      - ``reverse``

        Yahoo returns the data with last dates first (against all industry
        standards) and it must be reversed for it to work. Should this Yahoo
        standard change, the parameter is available.

      - ``adjclose``

        Whether to use the dividend/split adjusted close and adjust all values
        according to it.

      '''

    params = (('baseurl', 'http://ichart.yahoo.com/table.csv?'),
              ('period', 'd'), ('buffered', True), ('reverse', True))

    def start(self):
        self.error = None

        url = self.params.baseurl
        url += 's=%s' % urlquote(self.params.dataname)
        fromdate = self.params.fromdate
        url += '&a=%d&b=%d&c=%d' % \
               ((fromdate.month - 1), fromdate.day, fromdate.year)
        todate = self.params.todate
        if todate is None:
            todate = datetime.date.today()
        url += '&d=%d&e=%d&f=%d' % \
               ((todate.month - 1), todate.day, todate.year)
        url += '&g=%s' % self.params.period
        url += '&ignore=.csv'

        try:
            datafile = urlopen(url)
        except IOError as e:
            self.error = str(e)
            # leave us empty
            return

        if datafile.headers['Content-Type'] != 'text/csv':
            self.error = 'Wrong content type: %s' % datafile.headers
            return  # HTML returned? wrong url?

        if self.params.buffered:
            # buffer everything from the socket into a local buffer
            f = io.StringIO(datafile.read().decode('utf-8'), newline=None)
            datafile.close()
        else:
            f = datafile

        self.f = f

        # Prepared a "path" file -  CSV Parser can take over
        super(YahooFinanceData, self).start()


class YahooFinance(feed.CSVFeedBase):
    DataCls = YahooFinanceData

    params = DataCls.params._gettuple()
