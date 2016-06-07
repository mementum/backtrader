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

import datetime

from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num, num2date
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

    Supports the following contract specifications in parameter ``dataname``:

          - TICKER  # Stock type and SMART exchange
          - TICKER-STK  # Stock and SMART exchange
          - TICKER-STK-EXCHANGE  # Stock
          - TICKER-STK-EXCHANGE-CURRENCY  # Stock

          - TICKER-IND-EXCHANGE  # Index
          - TICKER-IND-EXCHANGE-CURRENCY  # Index

          - TICKER-YYYYMM-EXCHANGE  # Future
          - TICKER-YYYYMM-EXCHANGE-CURRENCY  # Future
          - TICKER-YYYYMM-EXCHANGE-CURRENCY-MULT  # Future
          - TICKER-FUT-EXCHANGE-CURRENCY-YYYYMM-MULT # Future

          - TICKER-YYYYMM-EXCHANGE-CURRENCY-STRIKE-RIGHT  # FOP
          - TICKER-YYYYMM-EXCHANGE-CURRENCY-STRIKE-RIGHT-MULT  # FOP
          - TICKER-FOP-EXCHANGE-CURRENCY-YYYYMM-STRIKE-RIGHT # FOP
          - TICKER-FOP-EXCHANGE-CURRENCY-YYYYMM-STRIKE-RIGHT-MULT # FOP

          - CUR1.CUR2-CASH-IDEALPRO  # Forex

          - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-STRIKE-RIGHT  # OPT
          - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-STRIKE-RIGHT-MULT  # OPT
          - TICKER-OPT-EXCHANGE-CURRENCY-YYYYMMDD-STRIKE-RIGHT # OPT
          - TICKER-OPT-EXCHANGE-CURRENCY-YYYYMMDD-STRIKE-RIGHT-MULT # OPT

    Params:

      - ``sectype`` (default: ``STK``)

        Default value to apply as *security type* if not provided in the
        ``dataname`` specification

      - ``exchange`` (default: ``SMART``)

        Default value to apply as *exchange* if not provided in the
        ``dataname`` specification

      - ``currency`` (default: ``''``)

        Default value to apply as *currency* if not provided in the
        ``dataname`` specification

      - ``useRT`` (default: ``False``)

        If ``True`` the ``5 Seconds Realtime bars`` provided by Interactive
        Brokers will be used as the smalles tick. According to the
        documentation they correspond to real-time values (once collated and
        curated by IB)

        If ``False`` then the ``RTVolume`` prices will be used, which are based
        on receiving ticks. In the case of ``CASH`` assets (like for example
        EUR.JPY) ``RTVolume`` will always be used and from it the ``bid`` price
        (industry de-facto standard with IB according to the literature
        scattered over the Internet)

    The default values in the params are the to allow things like ```TICKER``,
    to which the parameter ``sectype`` (default: ``STK``) and ``exchange``
    (default: ``SMART``) are applied.

    Some assets like ``AAPL`` need full specification including ``currency``
    (default: '') whereas others like ``TWTR`` can be simply passed as it is.

      - ``AAPL-STK-SMART-USD`` would be the full specification for dataname

        Or else: ``IBData`` as ``IBData(dataname='AAPL', currency='USD')``
        which uses the default values (``STK`` and ``SMART``) and overrides
        the currency to be ``USD``
    '''
    params = (
        ('sectype', 'STK'),  # usual industry value
        ('exchange', 'SMART'),  # usual industry value
        ('currency', ''),
        ('useRT', False),  # use RealTime 5 seconds bars
        ('historical', False),  # only historical download
        ('what', 'TRADES'),  # historical - what to show
        ('useRTH', False),  # historical - download only Regular Trading Hours
        ('startbackfill', True),  # do initial backfilling
        ('reconnbackfill', True),  # backfill attempt on reconnection
    )

    _store = ibstore.IBStore

    # States for the Finite State Machine in _load
    _ST_START, _ST_LIVE, _ST_HISTORBACK = range(3)

    def islive(self):
        '''Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated'''
        return True

    def __init__(self, **kwargs):
        self.ib = self._store(**kwargs)
        self.parsecontract()

    def setenvironment(self, env):
        '''Receives an environment (cerebro) and passes it over to the store it
        belongs to'''
        super(IBData, self).setenvironment(env)
        env.addstore(self.ib)

    def parsecontract(self):
        '''Parses dataname generates a default contract'''
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
        self.contractdetails = None
        self.precontract = self.ib.makecontract(
            symbol=symbol, sectype=sectype, exch=exch, curr=curr,
            expiry=expiry, strike=strike, right=right, mult=mult)

        self.cashtype = sectype == 'CASH'

    def start(self):
        '''Starts the IB connecction and gets the real contract and
        contractdetails if it exists'''
        super(IBData, self).start()
        # Kickstart store and get queue to wait on
        self.qlive = self.ib.start(data=self)
        self.qhist = None

        self.contract = None
        self.contractdetails = None

        self._state = self._ST_START  # initial state for _load
        self._statelivereconn = False  # if reconnecting in live state
        self._storedmsg = dict()  # keep pending live message (under None)

        if self.ib.connected():
            # get real contract details with real conId (contractId)
            cds = self.ib.getContractDetails(self.precontract, maxcount=1)
            if cds is not None:
                cdetails = cds[0]
                self.contract = cdetails.contractDetails.m_summary
                self.contractdetails = cdetails.contractDetails

    def stop(self):
        '''Stops and tells the store to stop'''
        super(IBData, self).stop()
        self.ib.stop()

    def reqdata(self):
        '''request real-time data. checks cash vs non-cash) and param useRT'''
        if self.contract is None:
            return

        if not self.p.useRT or self.cashtype:
            self.qlive = self.ib.reqMktData(self.contract)
        else:
            self.qlive = self.ib.reqRealTimeBars(self.contract)

        return self.qlive

    def canceldata(self):
        '''Cancels Market Data subscription, checking asset type and useRT'''
        if self.contract is None:
            return

        if not self.p.useRT or self.cashtype:
            self.ib.cancelMktData(self.qlive)
        else:
            self.ib.cancelRealTimeBars(self.qlive)

    def _load(self):
        if self.contract is None:
            self.put_notification(self.DISCONNECTED)
            return False  # nothing can be done

        while True:
            if self._state == self._ST_START:
                if self.p.historical:
                    self.put_notification(self.DELAYED)
                    dtend = None
                    if self.todate < float('inf'):
                        dtend = num2date(self.todate)

                    dtbegin = None
                    if self.fromdate > float('-inf'):
                        dtbegin = num2date(self.fromdate)

                    self.qhist = self.ib.reqHistoricalDataEx(
                        self.contract, dtend, dtbegin,
                        self._timeframe, self._compression,
                        what=self.p.what, useRTH=self.p.useRTH)

                    self._state = self._ST_HISTORBACK
                    continue

                # Live is requested
                if not self.ib.reconnect(resub=True):
                    self.put_notification(self.DISCONNECTED)
                    return False  # failed

                self.put_notification(self.DELAYED)
                self._statelivereconn = True  # attempt backfilling
                self._state = self._ST_LIVE

            elif self._state == self._ST_HISTORBACK:
                msg = self.qhist.get()
                if msg is None:  # Conn broken during historical/backfilling
                    # Situation not managed. Simply bail out
                    self.put_notification(self.DISCONNECTED)
                    return False  # error management cancelled the queue

                if msg.date is not None:
                    if self._load_rtbar(msg, hist=True):
                        return True  # loading worked

                    # the date is from overlapping historical request
                    continue

                # End of histdata
                if self.p.historical:  # only historical
                    self.put_notification(self.DISCONNECTED)
                    return False  # end of historical

                # Live is also wished - go for it
                self._state = self._ST_LIVE
                continue

            elif self._state == self._ST_LIVE:
                try:
                    # FIXME: timeout as parameter and automatically calculated
                    # with a potentially top limit
                    msg = self._storedmsg.pop(
                        None, self.qlive.get(timeout=2.0))
                except queue.Empty:
                    return None  # indicate timeout situation

                if msg is None:  # Conn broken during historical/backfilling
                    self.put_notification(self.CONNBROKEN)
                    # Try to reconnect
                    if not self.ib.reconnect(resub=True):
                        self.put_notification(self.DISCONNECTED)
                        return False  # failed

                    self._statelivereconn = True
                    continue

                if msg == -1102:  # conn broken/restored / tickerId maintained
                    self._statelivereconn = True  # backfill and live again
                    continue

                elif msg == -1101:  # conn broken/restored tickerId gone
                    self._statelivereconn = True  # backfill and live again
                    self.reqdata()  # resubscribe
                    continue

                # Process the message according to expected return type
                if not self._statelivereconn:
                    if self._laststatus != self.LIVE:
                        if self.qlive.qsize() <= 1:  # very short live queue
                            self.put_notification(self.LIVE)

                    if not self.p.useRT or self.cashtype:
                        return self._load_rtvolume(msg)

                    return self._load_rtbar(msg)

                # Fall through to processing reconnect - try to backfill
                self._storedmsg[None] = msg  # keep the msg

                # else do a backfill
                self.put_notification(self.DELAYED)

                dtend = None
                if len(self) > 1:
                    # len == 1 ... forwarded for the 1st time
                    dtbegin = self.datetime.datetime(-1)
                elif self.fromdate > float('-inf'):
                    dtbegin = num2date(self.fromdate)
                else:  # 1st bar and no begin set
                    # passing None to fetch max possible in 1 request
                    dtbegin = None

                rtvolume = not self.p.useRT or self.cashtype
                dtend = msg.datetime if rtvolume else msg.time

                self.qhist = self.ib.reqHistoricalDataEx(
                    self.contract, dtend, dtbegin,
                    self._timeframe, self._compression,
                    what=self.p.what,
                    useRTH=self.p.useRTH)

                self._state = self._ST_HISTORBACK
                self._statelivereconn = False
                continue

    def _load_rtbar(self, rtbar, hist=False):
        # A complete 5 second bar made of real-time ticks is delivered and
        # contains open/high/low/close/volume prices
        # The historical data has the same data but with 'date' instead of
        # 'time' for datetime
        dt = date2num(rbar.time if not hist else rtbar.date)
        if dt <= self.lines.datetime[0]:
            return False  # cannot deliver earlier than already delivered

        self.lines.datetime[0] = dt
        # Put the tick into the bar
        self.lines.open[0] = rtbar.open
        self.lines.high[0] = rtbar.high
        self.lines.low[0] = rtbar.low
        self.lines.close[0] = rtbar.close
        self.lines.volume[0] = rtbar.volume
        self.lines.openinterest[0] = 0

        return True

    def _load_rtvolume(self, rtvol):
        # A single tick is delivered and is therefore used for the entire set
        # of prices. Ideally the
        # contains open/high/low/close/volume prices
        # Datetime transformation
        dt = date2num(rtvol.datetime)
        if dt <= self.lines.datetime[0]:
            return False  # cannot deliver earlier than already delivered

        self.lines.datetime[0] = dt

        # Put the tick into the bar
        tick = rtvol.price
        self.lines.open[0] = tick
        self.lines.high[0] = tick
        self.lines.low[0] = tick
        self.lines.close[0] = tick
        self.lines.volume[0] = rtvol.size
        self.lines.openinterest[0] = 0

        return True
