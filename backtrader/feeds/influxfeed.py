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

import backtrader as bt
import backtrader.feed as feed
from ..utils import date2num
import datetime as dt

from influxdb import InfluxDBClient as idbclient
from influxdb.exceptions import InfluxDBClientError

TIMEFRAMES = dict(
    (
        (bt.TimeFrame.Seconds, 's'),
        (bt.TimeFrame.Minutes, 'm'),
        (bt.TimeFrame.Days, 'd'),
        (bt.TimeFrame.Weeks, 'w'),
        (bt.TimeFrame.Months, 'm'),
        (bt.TimeFrame.Years, 'y'),
    )
)


class InfluxDB(feed.DataBase):
    params = (
        ('host', '127.0.0.1'),
        ('port', '8086'),
        ('username', None),
        ('password', None),
        ('database', 'instruments'),
        ('timeframe', bt.TimeFrame.Days),
        ('high', 'high'),
        ('low', 'low'),
        ('open', 'open'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', 'openinterest'),
    )

    def start(self):
        super(InfluxDB, self).start()
        try:
            self.ndb = idbclient(self.p.host, self.p.port, self.p.username,
                                 self.p.password, self.p.database)
        except InfluxDBClientError as err:
            print('Failed to establish connection to InfluxDB: %s' % err)

        tf = '{multiple}{timeframe}'.format(
            multiple=(self.p.compression if self.p.compression else 1),
            timeframe=TIMEFRAMES.get(self.p.timeframe, 'd'))

        if not self.p.todate:
            st = 'time <= now()'
        else:
            st = 'time <= \'%s\'' % self.p.todate

        if self.p.fromdate:
            st += ' AND time >= \'%s\'' % self.p.fromdate

        qstr = ('SELECT first("{open_f}") AS "open", max("{high_f}") AS "high", '
                'min("{low_f}") AS "low", last("{close_f}") AS "close", '
                'sum("{volume_f}") AS "volume", sum("{openinterest_f}") AS "openinterest" '
                'FROM "{dataname}" '
                'WHERE {time} '
                'GROUP BY time({timeframe}) fill(none)').format(
                    open_f=self.p.open, high_f=self.p.high,
                    low_f=self.p.low, close_f=self.p.close,
                    volume_f=self.p.volume, openinterest_f=self.p.openinterest,
                    timeframe=tf, time=st, dataname=self.p.dataname)

        try:
            dbars = list(self.ndb.query(qstr).get_points())
        except InfluxDBClientError as err:
            print('InfluxDB query failed: %s' % err)

        self._rows = iter(dbars)

    def _load(self):
        try:
            bar = next(self._rows)
        except StopIteration:
            return False

        self.l.datetime[0] = date2num(dt.datetime.strptime(bar['time'],
                                                           '%Y-%m-%dT%H:%M:%SZ'))

        self.l.open[0] = bar['open']
        self.l.high[0] = bar['high']
        self.l.low[0] = bar['low']
        self.l.close[0] = bar['close']
        self.l.volume[0] = bar['volume']

        return True
