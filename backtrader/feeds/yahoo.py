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
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import urllib2

from .. import dataseries
from .. import linebuffer

class YahooFinance(dataseries.OHLCDateTime):
    baseurl = 'http://ichart.yahoo.com/table.csv?'

    def __init__(self, ticker, fromdate, todate, period='d', adjclose=True, savetofile=None):
        self.adjclose = adjclose

        self.error = None

        url = self.baseurl

        url += 's=%s' % ticker

        url += '&a=%d' % (fromdate.month - 1)
        url += '&b=%d' % fromdate.day
        url += '&c=%d' % fromdate.year

        url += '&d=%d' % (todate.month - 1)
        url += '&e=%d' % todate.day
        url += '&f=%d' % todate.year

        url += '&g=%s' % period

        url += '&ignore=.csv'

        try:
            datafile = urllib2.urlopen(url)
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

        filedata = StringIO(data[i:])
        headers = filedata.readline()

        lines = list()
        for line in filedata:
            lines.append(line)

        lines.reverse() # yahoo sends first the last date
        csvlines = [headers,] + lines
        csvfile = StringIO()
        csvfile.writelines(csvlines)
        csvfile.seek(0)
        self.fromfile = YahooFinanceCSV(csvfile, adjclose=adjclose)

        if savetofile is not None:
            diskfile = open(savetofile, 'wb')
            diskfile.write(csvfile.getvalue())
            diskfile.close()

    def getdata(self):
        return self.fromfile

    def start(self):
        self.fromfile.start()

    def stop(self):
        self.fromfile.stop()

    def next(self):
        return self.fromfile.next()


class YahooFinanceCSV(dataseries.OHLCDateTime):

    linecls = linebuffer.LineBufferFull

    def __init__(self, path, adjclose=True):
        self.path = path
        self.f = None
        self.adjclose = adjclose

    def getdata(self):
        return self

    def start(self):
        self.reset()

        if hasattr(self.path, 'readline'):
            self.f = self.path
        else:
            try:
                self.f = open(self.path, 'rb')
            except IOError:
                self.f = None
                return

        # skip the headers line
        self.f.readline()

        # Load the data
        while self.load():
            pass

        self.home()
        self.blen = self.buflen()
        self.curidx = 0

    def preload(self):
        # one time calculation
        pass # done in start

    def next(self):
        if self.curidx < self.blen:
            self.curidx += 1
            self.advance()
            return True
        return False

    def load(self):
        if self.f is None:
            return False

        try:
            line = self.f.readline()
        except (IOError, ValueError,):
            self.f.close()
            self.f = None
            return False

        if not line:
            return False

        linetokens = line.rstrip('\r\n').split(',')

        self.forward() # advance data pointer
        i = itertools.count(0)

        dttxt = linetokens[i.next()]
        y, m, d = int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10])

        self.lines.date = datetime.date(y, m, d).toordinal()
        self.lines.time = 0
        self.lines.open = float(linetokens[i.next()])
        self.lines.high = float(linetokens[i.next()])
        self.lines.low = float(linetokens[i.next()])
        self.lines.close = float(linetokens[i.next()])
        self.lines.volume = float(linetokens[i.next()])
        self.lines.openinterest = 0.0
        if self.adjclose:
            adjustedclose = float(linetokens[i.next()])
            adjfactor = self.lines.close[0] / adjustedclose
            self.lines.open[0] /= adjfactor
            self.lines.high[0] /= adjfactor
            self.lines.low[0] /= adjfactor
            self.lines.close[0] = adjustedclose
            self.lines.volume[0] /= adjfactor

        return True

    def stop(self):
        if self.f is not None:
            self.f.close()
            self.f = None
