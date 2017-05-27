#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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


import argparse
import collections
import datetime
import io
import logging
import sys


PY2 = sys.version_info.major == 2
if PY2:
    from urllib2 import urlopen
    from urllib import quote as urlquote
else:
    from urllib.request import urlopen
    from urllib.parse import quote as urlquote


logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging.INFO)


class YahooDownloadLegacy(object):
    baseurl = 'http://ichart.yahoo.com/table.csv?'

    def __init__(self, ticker, fromdate, todate, period='d', reverse=True):

        url = self.baseurl
        url += 's=%s' % urlquote(ticker)
        fromdate = fromdate
        url += '&a=%d&b=%d&c=%d' % \
               ((fromdate.month - 1), fromdate.day, fromdate.year)
        todate = todate
        url += '&d=%d&e=%d&f=%d' % \
               ((todate.month - 1), todate.day, todate.year)
        url += '&g=%s' % period
        url += '&ignore=.csv'

        self.datafile = urlopen(url)
        if self.datafile.headers['Content-Type'] != 'text/csv':
            self.datafile.close()
            raise ValueError(
                'Wrong Content Type in headers %s' %
                self.datafile.headers['Content-Type'])

        # skip the headers
        self.headers = self.datafile.readline().decode('utf-8')

        # buffer everything from the socket into a local buffer
        f = io.StringIO(self.datafile.read().decode('utf-8'), newline=None)
        self.datafile.close()
        self.datafile = f

        if reverse:
            # Yahoo data is in reverse order - reverse it
            dq = collections.deque()
            for line in self.datafile:
                dq.appendleft(line)

            f = io.StringIO(newline=None)
            f.writelines(dq)

            self.datafile.close()
            self.datafile = f

    def writetofile(self, filename):
        if not self.datafile:
            return

        if not hasattr(filename, 'read'):
            # It's not a file - open it
            f = io.open(filename, 'w')
        else:
            f = filename

        f.write(self.headers)

        self.datafile.seek(0)
        for line in self.datafile:
            f.write(line)

        f.close()


class YahooDownload(object):
    urlhist = 'https://finance.yahoo.com/quote/{}/history'
    urldown = 'https://query1.finance.yahoo.com/v7/finance/download'
    retries = 3

    def __init__(self, ticker, fromdate, todate, period='d', reverse=True):
        try:
            import requests
        except ImportError:
            msg = ('The new Yahoo data feed requires to have the requests '
                   'module installed. Please use pip install requests or '
                   'the method of your choice')
            raise Exception(msg)

        url = self.urlhist.format(ticker)

        sesskwargs = dict()
        if False and self.p.proxies:
            sesskwargs['proxies'] = self.p.proxies

        crumb = None
        sess = requests.Session()
        for i in range(self.retries + 1):  # at least once
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
        urld = '{}/{}'.format(self.urldown, ticker)

        urlargs = []
        posix = datetime.date(1970, 1, 1)
        if todate is not None:
            period2 = (todate.date() - posix).total_seconds()
            urlargs.append('period2={}'.format(int(period2)))

        if todate is not None:
            period1 = (fromdate.date() - posix).total_seconds()
            urlargs.append('period1={}'.format(int(period1)))

        intervals = {
            'd': '1d',
            'w': '1wk',
            'm': '1mo',
        }

        urlargs.append('interval={}'.format(intervals[period]))
        urlargs.append('events=history')
        urlargs.append('crumb={}'.format(crumb))

        urld = '{}?{}'.format(urld, '&'.join(urlargs))
        f = None
        for i in range(self.retries + 1):  # at least once
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

        self.datafile = f

    def writetofile(self, filename):
        if not self.datafile:
            return

        if not hasattr(filename, 'read'):
            # It's not a file - open it
            f = io.open(filename, 'w')
        else:
            f = filename

        self.datafile.seek(0)
        for line in self.datafile:
            f.write(line)

        f.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download Yahoo CSV Finance Data')

    parser.add_argument('--ticker', required=True,
                        help='Ticker to be downloaded')

    parser.add_argument('--notreverse', action='store_true', default=False,
                        help='Do not reverse the downloaded files')

    parser.add_argument('--timeframe', default='d',
                        help='Timeframe: d -> day, w -> week, m -> month')

    parser.add_argument('--fromdate', required=True,
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', required=True,
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--outfile', required=True,
                        help='Output file name')

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    logging.info('Processing input parameters')
    logging.info('Processing fromdate')
    try:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    except Exception as e:
        logging.error('Converting fromdate failed')
        logging.error(str(e))
        sys.exit(1)

    logging.info('Processing todate')
    try:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    except Exception as e:
        logging.error('Converting todate failed')
        logging.error(str(e))
        sys.exit(1)

    logging.info('Do Not Reverse flag status')
    reverse = not args.notreverse

    logging.info('Downloading from yahoo')
    try:
        yahoodown = YahooDownload(
            ticker=args.ticker,
            fromdate=fromdate,
            todate=todate,
            period=args.timeframe,
            reverse=reverse)

    except Exception as e:
        logging.error('Downloading data from Yahoo failed')
        logging.error(str(e))
        sys.exit(1)

    logging.info('Opening output file')
    try:
        ofile = io.open(args.outfile, 'w')
    except IOError as e:
        logging.error('Error opening output file')
        logging.error(str(e))
        sys.exit(1)

    logging.info('Writing downloaded data to output file')
    try:
        yahoodown.writetofile(ofile)
    except Exception as e:
        logging.error('Writing to output file failed')
        logging.error(str(e))
        sys.exit(1)

    logging.info('All operations completed successfully')
    sys.exit(0)
