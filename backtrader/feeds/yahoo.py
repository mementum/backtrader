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
from datetime import date, datetime
import io
import itertools

from ..utils.py3 import (urlopen, urlquote, ProxyHandler, build_opener,
                         install_opener)

import backtrader as bt
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

      - ``version`` (default: ``v7``)

        In May-2017 Yahoo discontinued the original ``ichart`` API for
        downloads and moved to a new API, which contains a ``v7`` string. This
        is the default version.

        Set it to the empty string to get the original behavior

      - ``swapcloses`` (default: ``False``)

        If ``True`` the allegedly *adjusted close* and *non-adjusted close*
        will be swapped. The downloads with the new ``v7`` API show at random
        times the closing prices swapped. There is no known pattern

    '''
    params = (
        ('reverse', False),
        ('adjclose', True),
        ('round', True),
        ('decimals', 2),
        ('version', 'v7'),
        ('swapcloses', False),
    )

    def start(self):
        super(YahooFinanceCSVData, self).start()

        if self.p.version == 'v7':
            return  # no need to reverse

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
        while True:
            nullseen = False
            for tok in linetokens[1:]:
                if tok == 'null':
                    nullseen = True
                    linetokens = self._getnextline()  # refetch tokens
                    if not linetokens:
                        return False  # cannot fetch, go away

                    # out of for to carry on wiwth while True logic
                    break

            if not nullseen:
                break  # can proceed

        i = itertools.count(0)

        dttxt = linetokens[next(i)]
        dt = date(int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10]))
        dtnum = date2num(datetime.combine(dt, self.p.sessionend))

        self.lines.datetime[0] = dtnum
        o = float(linetokens[next(i)])
        h = float(linetokens[next(i)])
        l = float(linetokens[next(i)])
        c = float(linetokens[next(i)])
        self.lines.openinterest[0] = 0.0

        if self.p.version == 'v7':  # in v7 ohlc,adc,v, get real volume
            # In v7, the final seq is "adj close", close, volume
            adjustedclose = c  # c was read above
            c = float(linetokens[next(i)])
            try:
                v = float(linetokens[next(i)])
            except:  # cover the case in which volume is "null"
                v = 0.0

            if self.p.swapcloses:  # swap closing prices if requested
                c, adjustedclose = adjustedclose, c

            adjfactor = adjustedclose / c  # reversed for v7

            # in v7 "adjusted prices" seem to be given, scale back for non adj
            if not self.params.adjclose:
                o *= adjfactor
                h *= adjfactor
                l *= adjfactor
                c = adjustedclose
                # v *= adjfactor  # except volume which is the same as in v1
            else:
                v /= adjfactor  # rescale vol down
        else:
            v = float(linetokens[next(i)])
            adjustedclose = float(linetokens[next(i)])

            if self.params.adjclose:
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


class YahooLegacyCSV(YahooFinanceCSVData):
    '''
    This is intended to load files which were downloaded before Yahoo
    discontinued the original service in May-2017

    '''
    params = (
        ('version', ''),
    )


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

      - ``proxies``

        A dict indicating which proxy to go through for the download as in
        {'http': 'http://myproxy.com'} or {'http': 'http://127.0.0.1:8080'}

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

      - ``urlhist``

        The url of the historical quotes in Yahoo Finance used to gather a
        ``crumb`` authorization cookie for the download

      - ``urldown``

        The url of the actual download server

      - ``retries``

        Number of times (each) to try to get a ``crumb`` cookie and download
        the data

      '''

    params = (
        ('baseurl', 'http://ichart.yahoo.com/table.csv?'),
        ('proxies', {}),
        ('period', 'd'),
        ('buffered', True),
        ('reverse', True),
        ('urlhist', 'https://finance.yahoo.com/quote/{}/history'),
        ('urldown', 'https://query1.finance.yahoo.com/v7/finance/download'),
        ('retries', 3),
    )

    def start_v1(self):
        self.error = None

        url = self.params.baseurl
        url += 's=%s' % urlquote(self.params.dataname)
        fromdate = self.params.fromdate
        url += '&a=%d&b=%d&c=%d' % \
               ((fromdate.month - 1), fromdate.day, fromdate.year)
        todate = self.params.todate
        if todate is None:
            todate = date.today()
        url += '&d=%d&e=%d&f=%d' % \
               ((todate.month - 1), todate.day, todate.year)
        url += '&g=%s' % self.params.period
        url += '&ignore=.csv'

        if self.p.proxies:
            proxy = ProxyHandler(self.p.proxies)
            opener = build_opener(proxy)
            install_opener(opener)

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

    def start_v1(self):
        self.error = None

        url = self.params.baseurl
        url += 's=%s' % urlquote(self.params.dataname)
        fromdate = self.params.fromdate
        url += '&a=%d&b=%d&c=%d' % \
               ((fromdate.month - 1), fromdate.day, fromdate.year)
        todate = self.params.todate
        if todate is None:
            todate = date.today()
        url += '&d=%d&e=%d&f=%d' % \
               ((todate.month - 1), todate.day, todate.year)
        url += '&g=%s' % self.params.period
        url += '&ignore=.csv'

        if self.p.proxies:
            proxy = ProxyHandler(self.p.proxies)
            opener = build_opener(proxy)
            install_opener(opener)

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

    def start_v7(self):
        try:
            import requests
        except ImportError:
            msg = ('The new Yahoo data feed requires to have the requests '
                   'module installed. Please use pip install requests or '
                   'the method of your choice')
            raise Exception(msg)

        self.error = None
        url = self.p.urlhist.format(self.p.dataname)

        sesskwargs = dict()
        if self.p.proxies:
            sesskwargs['proxies'] = self.p.proxies

        crumb = None
        sess = requests.Session()
        for i in range(self.p.retries + 1):  # at least once
            resp = sess.get(url, **sesskwargs)
            if resp.status_code != requests.codes.ok:
                continue

            txt = resp.text
            i = txt.find('CrumbStore')
            if i == -1:
                continue
            i = txt.find('crumb', i)
            if i == -1:
                continue
            istart = txt.find('"', i + len('crumb') + 1)
            if istart == -1:
                continue
            istart += 1
            iend = txt.find('"', istart)
            if iend == -1:
                continue

            crumb = txt[istart:iend]
            crumb = crumb.encode('ascii').decode('unicode-escape')
            break

        if crumb is None:
            self.error = 'Crumb not found'
            self.f = None
            return

        # urldown/ticker?period1=posix1&period2=posix2&interval=1d&events=history&crumb=crumb

        # Try to download
        urld = '{}/{}'.format(self.p.urldown, self.p.dataname)

        urlargs = []
        posix = date(1970, 1, 1)
        if self.p.todate is not None:
            period2 = (self.p.todate.date() - posix).total_seconds()
            urlargs.append('period2={}'.format(int(period2)))

        if self.p.todate is not None:
            period1 = (self.p.fromdate.date() - posix).total_seconds()
            urlargs.append('period1={}'.format(int(period1)))

        intervals = {
            bt.TimeFrame.Days: '1d',
            bt.TimeFrame.Weeks: '1wk',
            bt.TimeFrame.Months: '1mo',
        }

        urlargs.append('interval={}'.format(intervals[self.p.timeframe]))
        urlargs.append('events=history')
        urlargs.append('crumb={}'.format(crumb))

        urld = '{}?{}'.format(urld, '&'.join(urlargs))
        f = None
        for i in range(self.p.retries + 1):  # at least once
            resp = sess.get(urld, **sesskwargs)
            if resp.status_code != requests.codes.ok:
                continue

            ctype = resp.headers['Content-Type']
            if 'text/csv' not in ctype:
                self.error = 'Wrong content type: %s' % ctype
                continue  # HTML returned? wrong url?

            # buffer everything from the socket into a local buffer
            try:
                # r.encoding = 'UTF-8'
                f = io.StringIO(resp.text, newline=None)
            except Exception:
                continue  # try again if possible

            break

        self.f = f

    def start(self):
        if self.p.version == 'v7':
            self.start_v7()
        else:
            self.start_v1()

        # Prepared a "path" file -  CSV Parser can take over
        super(YahooFinanceData, self).start()


class YahooFinance(feed.CSVFeedBase):
    DataCls = YahooFinanceData

    params = DataCls.params._gettuple()
