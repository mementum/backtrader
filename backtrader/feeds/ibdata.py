#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015,2016 Daniel Rodriguez
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

from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num
from backtrader.utils.py3 import bytes, with_metaclass, queue
from backtrader.metabase import MetaParams
from backtrader.stores import ibstore


class MetaIBData(DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaIBData, cls).__init__(name, bases, dct)

        # Register with the store
        ibstore.IBStore.DataCls = cls


class IBData(with_metaclass(MetaIBData, DataBase)):
    '''Interactive Brokers Data Feed.

    Supports the following contract specifications in ``dataname``:

          - TICKER  # Stock type and SMART exchange
          - TICKER-STK  # Stock and SMART exchange
          - TICKER-STK-EXCHANGE  # Stock
          - TICKER-STK-EXCHANGE-CURRENCY  # Stock

          - TICKER-IND-EXCHANGE  # Index
          - TICKER-IND-EXCHANGE-CURRENCY  # Index

          - TICKER-YYYYMM-EXCHANGE-CURRENCY  # Future
          - TICKER-YYYYMM-EXCHANGE-CURRENCY-MULTIPLIER  # Future

          - TICKER-YYYYMM-EXCHANGE-CURRENCY-RIGHT-STRIKE  # FOP
          - TICKER-YYYYMM-EXCHANGE-CURRENCY-RIGHT-STRIKE-MULT  # FOP

          - CUR1.CUR2-CASH-IDEALPRO  # Forex

          - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-RIGHT-STRIKE  # OPT
          - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-RIGHT-STRIKE-MULT  # OPT

    The default values in the params are the to allow things like ```TICKER``,
    to which the parameter ``sectype`` (default: ``STK``) and ``exchange``
    (default: ``SMART``) are applied.

    Some assets like ``AAPL`` need full specification including ``currency``
    (default: '') whereas others like ``TWTR`` can be simply passed as it is.

      - ``AAPL-STK-SMART-USD`` would be the full specification

    Default ``sectype``, ``exchange`` and ``currency`` can be specified as
    parameters to the data feed.

    A timezone (``tz``: default None) can be applied to work directly in the
    specifiec timezone rather than in UTC, but internally the objects are
    managed without timezones.  This must be a ``pytz`` object (or compatible)

    Real-Time Bars (5 seconds Real-Time) can be requested with ``useRT``
    (default: False). This doesn't work with demo accounts.
    '''

    params = (
        ('sectype', 'STK'),  # usual industry value
        ('exchange', 'SMART'),  # usual industry value
        ('currency', ''),
        ('tz', None),
        ('useRT', False),  # use RealTime 5 seconds bars
    )

    _store = ibstore.IBStore

    def islive(self):
        return True

    def __init__(self, **kwargs):
        self.ib = self._store(**kwargs)
        self.parsecontract()

    def setenvironment(self, env):
        super(IBData, self).setenvironment(env)
        env.addstore(self.ib)

    def parsecontract(self):
        # Set defaults for optional tokens in the ticker string
        exch = self.p.exchange
        curr = self.p.currency
        expiry = ''
        strike = 0.0
        right = ''
        mult = ''

        # split the ticker string
        tokens = iter(self.p.dataname.split('-'))

        # Symbol and security type are compulsory
        symbol = next(tokens)
        try:
            sectype = next(tokens)
        except StopIteration:
            sectype = self.p.sectype

        # security type can be an expiration date
        if sectype.isdigit():
            expiry = sectype  # save the expiration ate

            if len(sectype) == 6:  # YYYYMM
                sectype = 'FUT'
            else:  # Assume OPTIONS - YYYYMMDD
                sectype = 'OPT'

        if sectype == 'CASH':  # need to address currency for Forex
            symbol, curr = symbol.split('.')

        # See if the optional tokens were provided
        try:
            exch = next(tokens)  # on exception it will be the default
            curr = next(tokens)  # on exception it will be the default

            if sectype == 'FUT':
                if not expiry:
                    expiry = next(tokens)
                mult = next(tokens)

                # Try to see if this is FOP - Futures on OPTIONS
                right = next(tokens)
                # if still here this is a FOP and not a FUT
                sectype = 'FOP'
                strike, mult = float(mult), ''  # assign to strike and void

                mult = next(tokens)  # try again to see if there is any

            elif sectype == 'OPT':
                if not expiry:
                    expiry = next(tokens)
                strike = float(next(tokens))  # on exception - default
                right = next(tokens)  # on exception it will be the default

                mult = next(tokens)  # ?? no harm in any case

        except StopIteration:
            pass

        # Make the initial contract
        self.cdetails = None
        self.precontract = self.ib.makecontract(
            symbol=symbol, sectype=sectype, exch=exch, curr=curr,
            expiry=expiry, strike=strike, right=right, mult=mult)

        self.cashtype = sectype == 'CASH'

    def start(self):
        '''Starts the IB connecction and gets the real contract if it exists'''
        super(IBData, self).start()
        # Kickstart store and get queue to wait on
        self.q = self.ib.start(data=self)

        if self.ib.connected():
            # get real contract details with real conId (contractId)
            q = self.ib.reqContractDetails(self.precontract)
            msg = q.get()
            if msg is None:
                self.contract = None
                self.contractdetails = None
            else:
                self.contract = msg.contractDetails.m_summary
                self.contractdetails = msg.contractDetails
        else:
            self.contract = None
            self.contractdetails = None

    def stop(self):
        '''Stops and tells the store to stop'''
        super(IBData, self).stop()
        self.ib.stop()

    def reqdata(self):
        '''request real-time data. checks item time and parameter useRT'''
        if self.contract is None:
            return

        if not self.p.useRT or self.cashtype:
            self.q = self.ib.reqMktData(self.contract, tz=self.p.tz)
        else:
            self.q = self.ib.reqRealTimeBars(self.contract, tz=self.p.tz)

        return self.q

    def canceldata(self):
        '''Cancels Market Data subscription, checking asset type and useRT'''
        if self.contract is None:
            return

        if not self.p.useRT or self.cashtype:
            self.ib.cancelMktData(self.q)
        else:
            self.ib.cancelRealTimeBars(self.q)

    def _load(self):
        # Wait on the qeue until None arrives (no data). Try to reconnect and
        # if not possible for whatever the reason, bail out.
        # Else process the message with the appropriate parser (asset
        while True:
            msg = self.q.get()
            if msg is None:
                if self.contract is None:
                    return False

                if not self.ib.reconnect(resub=True):
                    return False  # no reconnect or failed

                continue  # back to data fetch

            if self.p.useRT:
                return self._load_rtbar(msg)

            return self._load_rtvolume(msg)

    def _load_rtbar(self, rtbar):
        # Datetime transformation
        self.lines.datetime[0] = date2num(rtbar.time)

        # Put the tick into the bar
        self.lines.open[0] = rtbar.open
        self.lines.high[0] = rtbar.high
        self.lines.low[0] = rtbar.low
        self.lines.close[0] = rtbar.close
        self.lines.volume[0] = rtbar.volume
        self.lines.openinterest[0] = 0

        return True

    def _load_rtvolume(self, rtvol):
        # Datetime transformation
        self.lines.datetime[0] = date2num(rtvol.datetime)

        # Put the tick into the bar
        tick = rtvol.price
        self.lines.open[0] = tick
        self.lines.high[0] = tick
        self.lines.low[0] = tick
        self.lines.close[0] = tick
        self.lines.volume[0] = rtvol.size
        self.lines.openinterest[0] = 0

        return True
