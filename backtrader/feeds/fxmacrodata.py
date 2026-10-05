#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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

from datetime import date, datetime
import io
import json

from ..utils.py3 import (urlopen, ProxyHandler, build_opener,
                         install_opener)

try:
    from urllib.request import Request
except ImportError:  # Python 2
    from urllib2 import Request

from .. import feed
from ..utils import date2num


__all__ = ['FXMacroDataCSV', 'FXMacroData']


class FXMacroDataCSV(feed.CSVDataBase):
    '''
    Parses pre-downloaded FXMacroData CSV rows.

    The online :class:`FXMacroData` feed converts FXMacroData REST JSON rows
    into ``date,open,high,low,close,volume`` lines.  FXMacroData spot history
    provides one daily value, so open/high/low/close are set to the same value
    and volume is set to zero.
    '''

    _online = False

    def _loadline(self, linetokens):
        dttxt = linetokens[0]  # YYYY-MM-DD
        dt = date(int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10]))
        dtnum = date2num(datetime.combine(dt, self.p.sessionend))

        self.lines.datetime[0] = dtnum
        self.lines.open[0] = float(linetokens[1])
        self.lines.high[0] = float(linetokens[2])
        self.lines.low[0] = float(linetokens[3])
        self.lines.close[0] = float(linetokens[4])
        self.lines.volume[0] = float(linetokens[5])
        self.lines.openinterest[0] = 0.0

        return True


class FXMacroData(FXMacroDataCSV):
    '''
    Downloads daily FX spot rates from FXMacroData.

    Specific parameters:

      - ``dataname``: FX pair to download, for example ``EURUSD`` or
        ``EUR/USD``.

      - ``baseurl``: FXMacroData API base URL.

      - ``apikey``: optional FXMacroData Professional API key.  It is sent in
        the ``X-API-Key`` request header.

      - ``proxies``: optional proxy dictionary as in ``{'http':
        'http://myproxy.com'}``.

      - ``buffered``: retained for consistency with other online feeds.  The
        JSON response is parsed before the CSV parser is started.
    '''

    _online = True

    params = (
        ('baseurl', 'https://api.fxmacrodata.com/v1'),
        ('proxies', {}),
        ('buffered', True),
        ('apikey', None),
        ('headers', False),
    )

    def start(self):
        self.error = None

        base, quote = self._split_pair(self.p.dataname)
        url = '{}/forex/{}/{}'.format(
            self.p.baseurl.rstrip('/'), base.lower(), quote.lower())

        urlargs = ['limit=100']

        if self.p.fromdate:
            urlargs.append('start_date={}'.format(
                self.p.fromdate.strftime('%Y-%m-%d')))

        if self.p.todate:
            urlargs.append('end_date={}'.format(
                self.p.todate.strftime('%Y-%m-%d')))

        apikey = (self.p.apikey or '').strip()
        if any(c.isspace() or ord(c) < 32 for c in apikey):
            # never include the key itself in the error text
            self.error = 'FXMacroData API key contains invalid characters'
            return

        if self.p.proxies:
            proxy = ProxyHandler(self.p.proxies)
            opener = build_opener(proxy)
            install_opener(opener)

        # The API returns at most 100 rows per request, newest first, so
        # follow the offsets until the whole window has been read
        rows = []
        offset = 0
        while True:
            pageurl = '{}?{}&offset={}'.format(url, '&'.join(urlargs), offset)
            request = Request(pageurl)
            if apikey:
                # unredirected headers are not copied onto a followed
                # redirect, so the key is never sent to another host
                request.add_unredirected_header('X-API-Key', apikey)
            try:
                datafile = urlopen(request)
                payload = json.loads(datafile.read().decode('utf-8'))
                datafile.close()
            except IOError as e:
                self.error = str(e)
                return
            except ValueError:
                self.error = 'FXMacroData returned a non-JSON response'
                return

            page = payload.get('data') if isinstance(payload, dict) else None
            if not isinstance(page, list):
                self.error = 'Unexpected FXMacroData response: {}'.format(
                    payload.get('detail', 'no data list')
                    if isinstance(payload, dict) else 'no data list')
                return
            rows.extend(page)
            pagination = payload.get('pagination') or {}
            if not page or not pagination.get('has_more'):
                break
            offset = pagination.get('next_offset') or len(rows)

        if not rows:
            self.error = 'No FXMacroData rows returned for {}'.format(
                self.p.dataname)
            return

        rows = [row for row in rows
                if isinstance(row, dict) and row.get('date')]
        rows.sort(key=lambda row: row['date'])

        lines = []
        for row in rows:
            value = row.get('val')
            if value is None:
                continue
            lines.append('{},{},{},{},{},0.0\n'.format(
                row['date'], value, value, value, value))

        self.f = io.StringIO(''.join(lines), newline=None)
        super(FXMacroData, self).start()

    @staticmethod
    def _split_pair(pair):
        clean_pair = pair.replace('/', '').replace('-', '').upper()

        if len(clean_pair) != 6:
            raise ValueError(
                'FXMacroData dataname should be a six-letter FX pair, '
                'for example EURUSD')

        return clean_pair[:3], clean_pair[3:]
