#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
# Copyright (C) 2017 Ed Bartosh
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

from collections import deque
from datetime import datetime
from time import sleep

import backtrader as bt
from backtrader.feed import DataBase

import ccxt

class CCXT(DataBase):
    """
    CryptoCurrency eXchange Trading Library Data Feed.

    Params:

      - ``historical`` (default: ``False``)

        If set to ``True`` the data feed will stop after doing the first
        download of data.

        The standard data feed parameters ``fromdate`` and ``todate`` will be
        used as reference.

      - ``backfill_start`` (default: ``True``)

        Perform backfilling at the start. The maximum possible historical data
        will be fetched in a single request.
    """

    params = (
        ('historical', False),  # only historical download
        ('backfill_start', False),  # do backfilling at the start
    )

    # Supported granularities
    _GRANULARITIES = {
        (bt.TimeFrame.Minutes, 1): '1m',
        (bt.TimeFrame.Minutes, 3): '3m',
        (bt.TimeFrame.Minutes, 5): '5m',
        (bt.TimeFrame.Minutes, 15): '15m',
        (bt.TimeFrame.Minutes, 30): '30m',
        (bt.TimeFrame.Minutes, 60): '1h',
        (bt.TimeFrame.Minutes, 90): '90m',
        (bt.TimeFrame.Minutes, 120): '2h',
        (bt.TimeFrame.Minutes, 240): '4h',
        (bt.TimeFrame.Minutes, 360): '6h',
        (bt.TimeFrame.Minutes, 480): '8h',
        (bt.TimeFrame.Minutes, 720): '12h',
        (bt.TimeFrame.Days, 1): '1d',
        (bt.TimeFrame.Days, 3): '3d',
        (bt.TimeFrame.Weeks, 1): '1w',
        (bt.TimeFrame.Weeks, 2): '2w',
        (bt.TimeFrame.Months, 1): '1M',
        (bt.TimeFrame.Months, 3): '3M',
        (bt.TimeFrame.Months, 6): '6M',
        (bt.TimeFrame.Years, 1): '1y',
    }

    # States for the Finite State Machine in _load
    _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(3)

    def __init__(self, exchange, symbol, ohlcv_limit=10):
        self.exchange = getattr(ccxt, exchange)()
        self.symbol = symbol
        self.ohlcv_limit = ohlcv_limit

        self._data = deque() # data queue for price data
        self._last_id = '' # last processed trade id for ohlcv
        self._last_ts = 0 # last processed timestamp for ohlcv

    def start(self, ):
        super(CCXT, self).start()

        if self.p.fromdate:
            self._state = self._ST_HISTORBACK
            self.put_notification(self.DELAYED)

            self._fetch_ohlcv(self.p.fromdate)
        else:
            self._state = self._ST_LIVE
            self.put_notification(self.LIVE)

    def _load(self):
        if self._state == self._ST_OVER:
            return False

        while True:
            if self._state == self._ST_LIVE:
                if self._timeframe == bt.TimeFrame.Ticks:
                    return self._load_ticks()
                elif self.exchange.hasFetchOHLCV:
                    self._fetch_ohlcv()
                    return self._load_ohlcv()
                else:
                    raise NotImplementedError("'%s' exchange doesn't support fetching OHLCV data" % \
                                              self.exchange.name)
            elif self._state == self._ST_HISTORBACK:
                ret = self._load_ohlcv()
                if ret:
                    return ret
                else:
                    # End of historical data
                    if self.p.historical:  # only historical
                        self.put_notification(self.DISCONNECTED)
                        self._state = self._ST_OVER
                        return False  # end of historical
                    else:
                        self._state = self._ST_LIVE
                        self.put_notification(self.LIVE)
                        continue

    def _fetch_ohlcv(self, fromdate=None):
        """Fetch OHLCV data into self._data queue"""
        granularity = self._GRANULARITIES.get((self._timeframe, self._compression))
        if granularity is None:
            raise ValueError("'%s' exchange doesn't support fetching OHLCV data for "
                             "time frame %s, comression %s" % \
                             (self.exchange.name, bt.TimeFrame.getname(self._timeframe),
                             self._compression))

        if fromdate:
            since = int((fromdate - datetime(1970, 1, 1)).total_seconds() * 1000)
            limit = None
        else:
            since = None
            limit = self.ohlcv_limit

        sleep(self.exchange.rateLimit / 1000) # time.sleep wants seconds

        for ohlcv in self.exchange.fetch_ohlcv(self.symbol, timeframe=granularity,
                                               since=since, limit=limit)[::-1]:
            tstamp = ohlcv[0]
            if tstamp > self._last_ts:
                self._data.append(ohlcv)
                self._last_ts = tstamp

    def _load_ticks(self):
        sleep(self.exchange.rateLimit / 1000) # time.sleep wants seconds
        if self._last_id is None:
            # first time get the latest trade only
            trades = [self.exchange.fetch_trades(self.symbol)[-1]]
        else:
            trades = self.exchange.fetch_trades(self.symbol)

        for trade in trades:
            trade_id = trade['id']

            if trade_id > self._last_id:
                trade_time = datetime.strptime(trade['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
                self._data.append((trade_time, float(trade['price']), float(trade['amount'])))
                self._last_id = trade_id

        try:
            trade = self._data.popleft()
        except IndexError:
            return # no data in the queue

        trade_time, price, size = trade

        self.lines.datetime[0] = bt.date2num(trade_time)
        self.lines.open[0] = price
        self.lines.high[0] = price
        self.lines.low[0] = price
        self.lines.close[0] = price
        self.lines.volume[0] = size

        print("%s: loaded tick: time: %s, price: %s, size: %s" % (self._name, trade_time, price, size))

        return True

    def _load_ohlcv(self):
        try:
            ohlcv = self._data.popleft()
        except IndexError:
            return  # no data in the queue

        tstamp, open_, high, low, close, volume = ohlcv

        dtime = datetime.utcfromtimestamp(tstamp // 1000)

        self.lines.datetime[0] = bt.date2num(dtime)
        self.lines.open[0] = open_
        self.lines.high[0] = high
        self.lines.low[0] = low
        self.lines.close[0] = close
        self.lines.volume[0] = volume

        print("%s: loaded ohlcv:  time: %s, open: %s, high: %s, low: %s, close: %s, volume: %s" % \
              (self._name, dtime.strftime('%Y-%m-%d %H:%M:%S'), open_, high, low, close, volume))

        return True

    def haslivedata(self):
        return self._state == self._ST_LIVE and self._data

    def islive(self):
        return not self.p.historical
