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
from functools import wraps

import ccxt
from ccxt.base.errors import NetworkError, ExchangeError

import backtrader as bt
from backtrader import OrderBase

class CCXTOrder(OrderBase):
    def __init__(self, owner, data, size, ccxt_order):
        self.owner = owner
        self.data = data
        self.ccxt_order = ccxt_order
        self.ordtype = self.Buy if ccxt_order['side'] == 'buy' else self.Sell
        amount = ccxt_order.get('amount')
        if amount:
            self.size = float(amount)
        else:
            self.size = size

        super(CCXTOrder, self).__init__()

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

    # exchange -> store dictionary to track already initialized exchanges
    stores = {}
    # exchange -> config dictionry
    configs = {}

    @classmethod
    def get_store(cls, exchange, config, retries):
        store = cls.stores.get(exchange)
        if store:
            store_conf = cls.configs[exchange]
            if store_conf:
                if not set(config.items()).issubset(set(store_conf.items())):
                    raise ValueError("%s exchange is already configured: %s" % \
                                     (exchange, store_conf))
            return store

        cls.configs[exchange] = config
        cls.stores[exchange] = cls(exchange, config, retries)

        return cls.stores[exchange]

    def __init__(self, exchange, config, retries):
        self.exchange = getattr(ccxt, exchange)(config)
        self.retries = retries

    def get_granularity(self, timeframe, compression):
        if not self.exchange.has['fetchOHLCV']:
            raise NotImplementedError("'%s' exchange doesn't support fetching OHLCV data" % \
                                      self.exchange.name)

        granularity = self._GRANULARITIES.get((timeframe, compression))
        if granularity is None:
            raise ValueError("backtrader CCXT module doesn't support fetching OHLCV "
                             "data for time frame %s, comression %s" % \
                             (bt.TimeFrame.getname(timeframe), compression))

        if self.exchange.timeframes and granularity not in self.exchange.timeframes:
            raise ValueError("'%s' exchange doesn't support fetching OHLCV data for "
                             "%s time frame" % (self.exchange.name, granularity))

        return granularity

    def retry(method):
        @wraps(method)
        def retry_method(self, *args, **kwargs):
            for i in range(self.retries):
                time.sleep(self.exchange.rateLimit / 1000)
                try:
                    return method(self, *args, **kwargs)
                except (NetworkError, ExchangeError):
                    if i == self.retries - 1:
                        raise

        return retry_method

    @retry
    def getcash(self, currency):
        return self.exchange.fetch_balance()['free'].get(currency, 0.0)

    @retry
    def getvalue(self, currency):
        return self.exchange.fetch_balance()['total'].get(currency, 0.0)

    @retry
    def getposition(self, currency):
        return self.getvalue(currency)

    @retry
    def create_order(self, symbol, order_type, side, amount, price, params):
        order = self.exchange.create_order(symbol=symbol, type=order_type, side=side,
                                           amount=amount, price=price, params=params)
        return self.exchange.parse_order(order['info'])

    @retry
    def cancel_order(self, order):
        return self.exchange.cancel_order(order.ccxt_order['id'])

    @retry
    def fetch_trades(self, symbol):
        return self.exchange.fetch_trades(symbol)

    @retry
    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)

    @retry
    def fetch_open_orders(self):
        return self.exchange.fetchOpenOrders()
