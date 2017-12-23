#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2017 Ed Bartosh <bartosh@gmail.com>
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

import time

import ccxt

import backtrader as bt


class CCXTStore(object):
    '''API provider for CCXT feed and broker classes.'''

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

    def __init__(self, exchange, config):
        self.exchange = getattr(ccxt, exchange)(config)

    def get_granularity(self, timeframe, compression):
        if not self.exchange.hasFetchOHLCV:
            raise NotImplementedError("'%s' exchange doesn't support fetching OHLCV data" % \
                                      self.exchange.name)

        granularity = self._GRANULARITIES.get((timeframe, compression))
        if granularity is None:
            raise ValueError("'%s' exchange doesn't support fetching OHLCV data for "
                             "time frame %s, comression %s" % \
                             (self.exchange.name, bt.TimeFrame.getname(timeframe), compression))

        return granularity

    def getcash(self, currency):
        return self.exchange.fetch_balance()['free'][currency]

    def getvalue(self, currency):
        return self.exchange.fetch_balance()['total'][currency]

    def getposition(self, currency):
        return self.getvalue(currency)

    def create_order(self, symbol, order_type, side, amount, price, params):
        return self.exchange.create_order(symbol=symbol, type=order_type, side=side,
                                          amount=amount, price=price, params=params)

    def cancel_order(self, order_id):
        return self.exchange.cancel_order(order_id)

    def fetch_trades(self, symbol):
        time.sleep(self.exchange.rateLimit / 1000) # time.sleep wants seconds
        return self.exchange.fetch_trades(symbol)

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        time.sleep(self.exchange.rateLimit / 1000) # time.sleep wants seconds
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
