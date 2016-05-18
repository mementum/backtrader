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

import collections
from datetime import datetime, timedelta
import inspect
import itertools
import random
import threading
import time

from ib.ext.Contract import Contract
import ib.opt as ibopt

from backtrader import TimeFrame, Position
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import bytes, queue, with_metaclass
from backtrader.utils.flushfile import StdOutDevNull
from backtrader.utils.date import UTC
from backtrader.utils import AutoDict


def _ts2dt(tstamp=None, tz=None):
    # Transforms a RTVolume timestamp to a datetime object using the tz to
    # transform if provided, although the final object is naive to allow for a
    # sensible comparison to other naive objects in the system
    if tstamp is None:
        dt = datetime.utcnow()
        if tz is not None:
            dt = dt.replace(tzinfo=UTC).astimezone(tz).replace(tzinfo=None)
        return dt

    sec, msec = divmod(long(tstamp), 1000)
    usec = msec * 1000
    dt = datetime.utcfromtimestamp(sec).replace(microsecond=usec)
    if tz is not None:
        # convert to local time and make it naive again to ensure it stays
        # right when converting to a number
        dt = dt.replace(tzinfo=UTC).astimezone(tz).replace(tzinfo=None)
    return dt


class RTVolume(object):
    '''Parses a tickString tickType 48 (RTVolume) event from the IB API into its
    constituent fields

    Supports using a "price" to simulate an RTVolume from a price event
    '''
    _fields = [
        ('price', float),
        ('size', int),
        ('datetime', int),
        ('volume', int),
        ('vwap', float),
        ('single', bool)
    ]

    def __init__(self, rtvol='', price=None, tz=None):
        # Use a provided string or simulate a list of empty tokens
        tokens = iter(rtvol.split(';'))

        # Put the tokens as attributes using the corresponding func
        for name, func in self._fields:
            setattr(self, name, func(next(tokens)) if rtvol else func())

        self.datetime = _ts2dt(self.datetime, tz=tz)

        # If price was provided use it
        if price is not None:
            self.price = price


class MetaSingleton(MetaParams):
    '''Metaclass to make a metaclassed class a singleton'''
    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


# Decorator to mark methods to register with ib.opt
def ibregister(f):
    f._ibregister = True
    return f


class IBStore(with_metaclass(MetaSingleton, object)):
    '''Singleton class wrapping an ibpy ibConnection instance.'''

    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    params = (
        ('host', '127.0.0.1'),
        ('port', 7496),
        ('clientId', None),  # None generates a random clientid 1 -> 2^16
        ('_debug', False),
        ('reconnect', 3),  # -1 forever, 0 No, > 0 number of retries
        ('timeout', 3.0),  # timeout between reconnections
    )

    @classmethod
    def getdata(self, *args, **kwargs):
        '''Returns data with *args, **kwargs from registered ``DataCls``'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(self, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self):
        super(IBStore, self).__init__()

        self._lock_q = threading.Lock()  # sync access to _tickerId/Queues
        self._lock_accupd = threading.Lock()  # sync account updates
        self._lock_pos = threading.Lock()  # sync account updates
        # Account list received
        self._event_managed_accounts = threading.Event()
        self._event_accdownload = threading.Event()

        self.dontreconnect = False  # for non-recoverable connect errors

        self._env = None  # reference to cerebro for general notifications
        self.broker = None  # broker instance
        self.datas = list()  # datas that have registered over start
        self.ccount = 0  # requests to start (from cerebro or datas)

        # Structures to hold datas requests
        self.qs = collections.OrderedDict()  # key: tickerId -> queues
        self.ts = collections.OrderedDict()  # key: queue -> tickerId
        self.tzs = collections.OrderedDict()  # key: tickerId -> timezone
        self.iscash = set()  # tickerIds from cash products (for ex: EUR.JPY)

        self.acc_cash = AutoDict()  # current total cash per account
        self.acc_value = AutoDict()  # current total value per account
        self.acc_upds = AutoDict()  # current account valueinfos per account

        self.ordbyid = dict()

        self.positions = collections.defaultdict(Position)  # actual positions

        self._tickerId = itertools.count(1)  # unique tickerIds
        self.orderid = None  # next possible orderid (will be itertools.count)

        self.managed_accounts = list()  # received via managedAccounts

        self.ostatus = queue.Queue()  # keep non yet broker processed statuses

        self.notifs = queue.Queue()  # store notifications for cerebro

        # Use the provided clientId or a random one
        if self.p.clientId is None:
            self.clientId = random.randint(1, pow(2, 16) - 1)
        else:
            self.clientId = self.p.clientId

        # ibpy connection object
        self.conn = ibopt.ibConnection(
            host=self.p.host, port=self.p.port, clientId=self.clientId)

        # register a printall method if requested
        if self.p._debug:
            self.conn.registerAll(self.watcher)

        # Register decorated methods with the conn
        methods = inspect.getmembers(self, inspect.ismethod)
        for name, method in methods:
            if not getattr(method, '_ibregister', False):
                continue

            message = getattr(ibopt.message, name)
            self.conn.register(method, message)

    def start(self, data=None, broker=None):
        self.reconnect(fromstart=True)  # reconnect should be an invariant

        # Datas require some processing to kickstart data reception
        if data is not None:
            self._env = data._env
            # For datas simulate a queue with None to kickstart co
            self.datas.append(data)

            # if connection fails, get a fake registration that will force the
            # datas to try to reconnect or else bail out
            return self.getTickerQueue(start=True)

        elif broker is not None:
            self.broker = broker

    def stop(self):
        self.conn.disconnect()  # disconnect should be an invariant

    def logmsg(self, *args):
        # for logging purposes
        if self.p._debug:
            print(*args)

    def watcher(self, msg):
        # will be registered to see all messages if debug is requested
        self.logmsg(str(msg))

    def connected(self):
        # The isConnected method is available through __getattr__ indirections
        # and may not be present, which indicates that no connection has been
        # made because the subattribute sender has not yet been created, hence
        # the check for the AttributeError exception
        try:
            return self.conn.isConnected()
        except AttributeError:
            pass

        return False  # non-connected (including non-initialized)

    def reconnect(self, fromstart=False, resub=False):
        # This method must be an invariant in that it can be called several
        # times from the same source and must be consistent. An exampler would
        # be 5 datas which are being received simultaneously and all request a
        # reconnect

        # Policy:
        #  - if dontreconnect has been set, no option to connect is possible
        #  - check connection and use the absence of isConnected as signal of
        #    first ever connection (add 1 to retries too)
        #  - Calculate the retries (forever or not)
        #  - Try to connct
        #  - If achieved and fromstart is false, the datas will be
        #    re-kickstarted to recreate the subscription
        firstconnect = False
        try:
            if self.conn.isConnected():
                if resub:
                    self.startdatas()
                return True  # nothing to do
        except AttributeError:
            # Not connected, several __getattr__ indirections to
            # self.conn.sender.client.isConnected
            firstconnect = True

        if self.dontreconnect:
            return False

        # This is only invoked from the main thread by datas and therefore no
        # lock is needed to control synchronicity to it
        retries = self.p.reconnect
        if retries >= 0:
            retries += firstconnect

        while retries < 0 or retries:
            if not firstconnect:
                time.sleep(self.p.timeout)

            firstconnect = False

            if self.conn.connect():
                if not fromstart or resub:
                    self.startdatas()
                return True  # connection successful

            if retries > 0:
                retries -= 1

        self.dontreconnect = True
        return False  # connection/reconnection failed

    def startdatas(self):
        # kickstrat datas, not returning until all of them have been done
        ts = list()
        for data in self.datas:
            t = threading.Thread(target=data.reqdata)
            t.start()
            ts.append(t)

        for t in ts:
            t.join()

    def stopdatas(self):
        # stop subs and force datas out of the loop (in LIFO order)
        qs = list(self.qs.values())
        ts = list()
        for data in self.datas:
            t = threading.Thread(target=data.canceldata)
            t.start()
            ts.append(t)

        for t in ts:
            t.join()

        for q in reversed(qs):  # datamaster the last one to get a None
            q.put(None)

    def get_notification(self):
        '''Return the pending "store" notifications until the queue is empty'''
        try:
            return self.notifs.get(False)  # non-blocking provoke exception
        except queue.Empty:
            pass

        return None

    @ibregister
    def error(self, msg):
        # All errors are logged to the environment (cerebro), because many
        # errors in Interactive Brokers are actually informational and many may
        # actually be of interest to the user
        self.notifs.put((msg, tuple(msg.values()), dict(msg.items())))

        # Manage those events which have to do with connection
        if msg.errorCode is None:
            # Usually received as an error in connection of just before disconn
            pass
        if msg.errorCode == 200:
            # contractDetails - security was not found, notify over right queue
            q = self.qs[msg.id]
            q.put(None)
            self.cancelQueue(q)
        elif msg.errorCode == 1300:
            # Connection has been lost. The port for a new connection is there
            # newport = int(msg.errorMsg.split('-')[-1])  # bla bla bla -7496
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 502:
            # Cannot connect to TWS: port, config not open, tws off (504 then)
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 504:  # Not Connected for data op
            # Once for each data
            pass  # don't need to manage it

        elif msg.errorCode == 326:  # not recoverable, clientId in use
            self.dontreconnect = True
            self.conn.disconnect()
            self.stopdatas()

    @ibregister
    def connectionClosed(self, msg):
        # Sometmes this comes without 1300/502 or any other and will not be
        # seen in error hence the need to manage the situation independently
        self.conn.disconnect()
        self.stopdatas()

    @ibregister
    def managedAccounts(self, msg):
        # 1st message in the stream
        self.managed_accounts = msg.accountsList.split(',')

        self._event_managed_accounts.set()

    def reqCurrentTime(self):
        self.conn.reqCurrentTime()

    @ibregister
    def currentTime(self, msg):
        pass

    def nextTickerId(self):
        # Get the next ticker using next on the itertools.count
        return next(self._tickerId)

    @ibregister
    def nextValidId(self, msg):
        # Create a counter from the TWS notified value to apply to orders
        self.orderid = itertools.count(msg.orderId)

    def nextOrderId(self):
        # Get the next ticker using next on the itertools.count made with the
        # notified value from TWS
        return next(self.orderid)

    def getTickerQueue(self, tz=None, start=False):
        '''Creates ticker/Queue for data delivery to a data feed'''

        q = queue.Queue()
        if start:
            q.put(None)
            return q

        with self._lock_q:
            tickerId = self.nextTickerId()
            self.qs[tickerId] = q  # can be managed from other thread
            self.ts[q] = tickerId
            self.tzs[tickerId] = tz

        return tickerId, q

    def cancelQueue(self, q):
        '''Cancels a Queue for data delivery'''
        # pop ts (tickers) and with the result qs (queues)
        tickerId = self.ts.pop(q, None)
        self.qs.pop(tickerId, None)
        # sets don't have a pop with default argument
        if tickerId in self.iscash:
            self.iscash.remove(tickerId)

        self.tzs.pop(tickerId, None)  # remove timezone

    def reqContractDetails(self, contract):
        # get a ticker/queue for identification/data delivery
        tickerId, q = self.getTickerQueue()
        self.conn.reqContractDetails(tickerId, contract)
        return q

    @ibregister
    def contractDetails(self, msg):
        q = self.qs[msg.reqId]
        q.put(msg)
        self.cancelQueue(q)

    def reqHistoricalData(self, contract, enddate, barsize, duration,
                          useRTH=False):
        '''Proxy to reqHistorical Data'''

        # get a ticker/queue for identification/data delivery
        tickerId, q = self.getTickerQueue()

        # process enddate
        enddate_str = num2date(enddate).strftime('%Y%m%d %H:%M:%S')

        self.conn.reqHistoricalData(
            tickerId,
            contract,
            enddate_str,
            duration,
            barsize,
            bytes('TRADES'),
            int(useRTH))

        return q

    def cancelHistoricalData(self, q):
        '''Cancels an existing HistoricalData request

        Params:
          - q: the Queue returned by reqMktData
        '''
        with self._lock_q:
            self.conn.cancelHistoricalData(self.ts[q])
            self.cancelQueue(q)

    def reqRealTimeBars(self, contract, useRTH=False, duration=5):
        '''Creates a request for (5 seconds) Real Time Bars

        Params:
          - contract: a ib.ext.Contract.Contract intance
          - useRTH: (default: False) passed to TWS
          - duration: (default: 5) passed to TWS, no other value works in 2016)

        Returns:
          - a Queue the client can wait on to receive a RTVolume instance
        '''
        # get a ticker/queue for identification/data delivery
        tickerId, q = self.getTickerQueue()

        # 20150929 - Only 5 secs supported for duration
        self.conn.reqRealTimeBars(
            tickerId,
            contract,
            duration,
            bytes('TRADES'),
            int(useRTH))

        return q

    def cancelRealTimeBars(self, q):
        '''Cancels an existing MarketData subscription

        Params:
          - q: the Queue returned by reqMktData
        '''
        with self._lock_q:
            tickerId = self.ts.get(q, None)
            if tickerId is not None:
                self.conn.cancelRealTimeBars(tickerId)

            self.cancelQueue(q)

    def reqMktData(self, contract, tz=None):
        '''Creates a MarketData subscription

        Params:
          - contract: a ib.ext.Contract.Contract intance

        Returns:
          - a Queue the client can wait on to receive a RTVolume instance
        '''
        # get a ticker/queue for identification/data delivery
        tickerId, q = self.getTickerQueue(tz)
        ticks = '233'  # request RTVOLUME tick delivered over tickString

        if contract.m_secType == 'CASH':
            self.iscash.add(tickerId)
            ticks = ''  # cash markets do not get RTVOLUME

        # Can request 233 also for cash ... nothing will arrive
        self.conn.reqMktData(tickerId, contract, bytes(ticks), False)
        return q

    def cancelMktData(self, q):
        '''Cancels an existing MarketData subscription

        Params:
          - q: the Queue returned by reqMktData
        '''
        with self._lock_q:
            tickerId = self.ts.get(q, None)
            if tickerId is not None:
                self.conn.cancelMktData(tickerId)

            self.cancelQueue(q)

    @ibregister
    def tickString(self, msg):
        # Receive and process a tickString message
        if msg.tickType == 48:  # RTVolume
            try:
                rtvol = RTVolume(msg.value, tz=self.tzs[msg.tickerId])
            except ValueError:  # price not in message ...
                pass
            else:
                self.qs[msg.tickerId].put(rtvol)

    @ibregister
    def tickPrice(self, msg):
        '''Cash Markets have no notion of "last_price"/"last_size" and the
        tracking of the price is done (industry de-facto standard at least with
        the IB API) following the BID price

        A RTVolume which will only contain a price is put into the client's
        queue to have a consistent cross-market interface
        '''
        # Used for "CASH" markets
        if msg.tickerId in self.iscash:
            if msg.field == 1:  # Bid Price
                try:
                    rtvol = RTVolume(price=msg.price)
                except ValueError:  # price not in message ...
                    pass
                else:
                    self.qs[msg.tickerId].put(rtvol)

    def _parsemsgtime(self, msg):
        # Parse datetime of RealTimeBars/HistoricalData using tz if not None
        tz = self.tzs[msg.tickerId]
        dt = datetime.utcfromtimestamp(msgtime)
        if tz is not None:
            dt = dt.replace(tzinfo=UTC).astimezone(tz).replace(tzinfo=None)
        return dt

    @ibregister
    def realtimeBar(self, msg):
        '''Receives x seconds Real Time Bars (at the time of writing only 5
        seconds are supported)

        Not valid for cash markets
        '''
        msg.time = self._parsemsgtime(msg)
        self.qs[msg.reqId].put(msg)

    @ibregister
    def historicalData(self, msg):
        '''Receives the events of a historical data request'''
        if msg.time.startswith('finished-'):
            msg = None
        else:
            msg.time = self._parsemsgtime(msg)

        self.qs[msg.reqId].put(msg)

    # The _durations are meant to calculate the needed historical data to
    # perform backfilling at the start of a connetion or a connection is lost.
    # Using a timedelta as a key allows to quickly find out which bar size
    # bar size (values in the tuples int the dict) can be used.

    _durations = [
        # 60 seconds - 1 min
        (timedelta(seconds=60),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs', '1 min')),

        # 120 seconds - 2 mins
        (timedelta(seconds=120),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins')),

        # 180 seconds - 3 mins
        (timedelta(seconds=180),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins')),

        # 300 seconds - 5 mins
        (timedelta(seconds=300),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins')),

        # 600 seconds - 10 mins
        (timedelta(seconds=600),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins')),

        # 900 seconds - 15 mins
        (timedelta(seconds=900),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins')),

        # 1200 seconds - 20 mins
        (timedelta(seconds=1200),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins')),

        # 1800 seconds - 30 mins
        (timedelta(seconds=1800),
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins')),

        # 3600 seconds - 1 hour
        (timedelta(seconds=3600),
         ('5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins', '1 hour')),

        # 7200 seconds - 2 hours
        (timedelta(seconds=7200),
         ('5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins', '1 hour', '2 hours')),

        # 10800 seconds - 3 hours
        (timedelta(seconds=10800),
         ('10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins', '1 hour', '2 hours', '3 hours')),

        # 14400 seconds - 4 hours
        (timedelta(seconds=14400),
         ('15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins', '1 hour', '2 hours', '3 hours', '4 hours')),

        # 28800 seconds - 8 hours
        (timedelta(seconds=28800),
         ('30 secs', '1 min', '2 mins', '3 mins', '5 mins', '10 mins',
          '15 mins', '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours', '8 hours')),

        # 1 days
        (timedelta(days=1),
         ('1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins', '1 hour', '2 hours', '3 hours', '4 hours',
          '1 day')),

        # 2 days
        (timedelta(days=2),
         ('2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins',
          '30 mins', '1 hour', '2 hours', '3 hours', '4 hours',
          '1 day')),

        # 1 weeks
        (timedelta(days=7),
         ('3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours',
          '1 day', '1 W')),

        # 2 weeks
        (timedelta(days=2 * 7),
         ('15 mins', '20 mins', '30 mins', '1 hour', '2 hours', '3 hours',
          '4 hours', '1 day', '1 W')),

        # 1 months
        (timedelta(days=1 * 31),
         ('30 mins', '1 hour', '2 hours', '3 hours', '4 hours',
          '1 day', '1 W', '1 M')),

        # 2+ months
        (timedelta(days=2 * 31),
         ('1 day', '1 W', '1 M')),

        # 1+ years
        (timedelta(days=365),
         ('1 day', '1 W', '1 M')),
    ]

    # Sizes allow for quick translation from bar sizes above to actual
    # timeframes to make a comparison with the actual data
    _sizes = {
        'secs': (TimeFrame.Seconds, 1),
        'min': (TimeFrame.Minutes, 1),
        'mins': (TimeFrame.Minutes, 1),
        'hour': (TimeFrame.Minutes, 60),
        'hours': (TimeFrame.Minutes, 60),
        'day': (TimeFrame.Days, 1),
        'W': (TimeFrame.Weeks, 1),
        'W': (TimeFrame.Months, 1),
    }

    def calcdurations(self, dtbegin, dtend):
        '''Calculate a diration in between 2 datetimes'''
        td = dtend - dtbegin

        index = bisect.bisect_left(self._durations, (td, ('',)))
        index = min(index, len(self._durations) - 1)  # cap at last item
        duration, sizes = self_durations[index]

    def calcduration(self, dtbegin, dtend):
        '''Calculate a diration in between 2 datetimes. Returns single size'''
        duration, sizes = self._calcdurations(dtbegin, dtend)
        return duration, sizes[0]

    def makecontract(self, symbol, sectype, exch, curr,
                     expiry='', strike=0.0, right='', mult=1):
        '''returns a contract from the parameters without check'''

        contract = Contract()
        contract.m_symbol = bytes(symbol)
        contract.m_secType = bytes(sectype)
        contract.m_exchange = bytes(exch)
        if curr:
            contract.m_currency = bytes(curr)
        if sectype in ['FUT', 'OPT', 'FOP']:
            contract.m_expiry = bytes(expiry)
        if sectype in ['OPT', 'FOP']:
            contract.m_strike = strike
            contract.m_right = bytes(right)
        if mult:
            contract.m_multiplier = bytes(mult)
        return contract

    def cancelOrder(self, orderid):
        '''Proxy to cancelOrder'''
        self.conn.cancelOrder(orderid)

    def placeOrder(self, orderid, contract, order):
        '''Proxy to placeOrder'''
        self.conn.placeOrder(orderid, contract, order)

    @ibregister
    def openOrder(self, msg):
        '''Receive the event ``openOrder`` events'''
        # received when the order is in the system after placeOrder
        # the message contains: order, contract, orderstate
        # no need to manage it. wait for orderstatus to notify
        os = msg.orderState
        print('-*' * 10, 'ORDERSTATE')
        for f in ['m_status', 'm_initMargin', 'm_maintMargin',
                  'm_equityWithLoan', 'm_commission', 'm_minCommission',
                  'm_maxCommission', 'm_commissionCurrency', 'm_warningText']:

            print(f, ':', getattr(os, f))
        print('-*' * 10)

    @ibregister
    def execDetails(self, msg):
        '''Receive execDetails'''
        ex = msg.execution
        print('-*' * 10, 'EXECUTION')
        for f in ['m_orderId', 'm_clientId', 'm_execId', 'm_time',
                  'm_acctNumber', 'm_exchange', 'm_side', 'm_shares',
                  'm_price', 'm_permId', 'm_liquidation', 'm_cumQty',
                  'm_avgPrice', 'm_orderRef', 'm_evRule', 'm_evMultiplier']:

            print(f, ':', getattr(ex, f))
        print('-*' * 10)

    @ibregister
    def orderStatus(self, msg):
        '''Receive the event ``orderStatus``'''
        self.ostatus.put(msg)
        # self.broker.push_orderstatus(msg)

    @ibregister
    def commissionReport(self, msg):
        '''Receive the event commissionReport'''
        cr = msg.commissionReport
        print('-*' * 10, 'COMMISSION REPORT')
        for f in ['m_execId', 'm_commission', 'm_currency', 'm_realizedPNL',
                  'm_yield', 'm_yieldRedemptionDate']:

            print(f, ':', getattr(cr, f))
        print('-*' * 10)

    def get_orderstatus(self):
        '''For client brokers. Gets orderstatus messages that have been put
        into the Queue until it is empty

        Returns the OrderStatus or None if the queue is Empty
        '''
        try:
            return self.ostatus.get(False)  # non-blocking provoking Exception
        except queue.Empty:
            pass

        return None

    def reqPositions(self):
        '''Proxy to reqPositions'''
        self.conn.reqPositions()

    @ibregister
    def position(self, msg):
        '''Receive event positions'''
        pass

    def reqAccountUpdates(self, subscribe=True, account=None):
        '''Proxy to reqAccountUpdates

        If ``account`` is ``None``, wait for the ``managedAccounts`` message to
        set the account codes
        '''
        if account is None:
            self._event_managed_accounts.wait()
            account = self.managed_accounts[0]

        self.conn.reqAccountUpdates(subscribe, bytes(account))

    @ibregister
    def accountDownloadEnd(self, msg):
        # Signas the end of an account update
        # the event indicates it's over. It's only false once, and can be used
        # to find out if it has at least been downloaded once
        self._event_accdownload.set()

    @ibregister
    def updatePortfolio(self, msg):
        # Lock access to the position dicts. This is called in sub-thread and
        # can kick in at any time
        with self._lock_pos:
            if not self._event_accdownload.is_set():  # 1st event seen
                position = Position(msg.position, msg.averageCost)
                self.positions[msg.contract.m_conId] = position
            else:
                position = self.positions[msg.contract.m_conId]
                position.set(msg.position, msg.averageCost)

    def getposition(self, contract):
        # Lock access to the position dicts. This is called from main thread
        # and updates could be happening in the background
        with self._lock_pos:
            return self.positions[contract.m_conId]

    @ibregister
    def updateAccountValue(self, msg):
        # Lock access to the dicts where values are updated. This happens in a
        # sub-thread and could kick it at anytime
        with self._lock_accupd:
            try:
                value = float(msg.value)
            except ValueError:
                value = msg.value

            self.acc_upds[msg.accountName][msg.key][msg.currency] = value

            if msg.key == 'NetLiquidation':
                # NetLiquidationByCurrency and currency == 'BASE' is the same
                self.acc_value[msg.accountName] = value
            elif msg.key == 'TotalCashBalance' and msg.currency == 'BASE':
                self.acc_cash[msg.accountName] = value

    def get_acc_values(self, account=None):
        '''Returns all account value infos sent by TWS during regular updates
        Waits for at least 1 successful download

        If ``account`` is ``None`` then a dictionary with accounts as keys will
        be returned containing all accounts

        If account is specified or the system has only 1 account the dictionary
        corresponding to that account is returned
        '''
        # Wait for at least 1 account update download to have been finished
        # before the account infos can be returned to the calling client
        self._event_accdownload.wait()
        # Lock access to acc_cash to avoid an event intefering
        with self._updacclock:
            if account is None:
                # wait for the managedAccount Messages
                self._event_managed_accounts.wait()
                if len(self.managed_accounts) > 1:
                    return self.acc_upds.copy()

                # Only 1 account, fall through to return only 1
                account = self.managed_accounts[0]

            return self.acc_upds[account].copy()

    def get_acc_value(self, account=None):
        '''Returns the net liquidation value sent by TWS during regular updates
        Waits for at least 1 successful download

        If ``account`` is ``None`` then a dictionary with accounts as keys will
        be returned containing all accounts

        If account is specified or the system has only 1 account the dictionary
        corresponding to that account is returned
        '''
        # Wait for at least 1 account update download to have been finished
        # before the value can be returned to the calling client
        self._event_accdownload.wait()
        # Lock access to acc_cash to avoid an event intefering
        with self._lock_accupd:
            if account is None:
                # wait for the managedAccount Messages
                self._event_managed_accounts.wait()
                if len(self.managed_accounts) > 1:
                    return sum(self.acc_value.values())

                # Only 1 account, fall through to return only 1
                account = self.managed_accounts[0]

            return self.acc_value[account]

    def get_acc_cash(self, account=None):
        '''Returns the total cash value sent by TWS during regular updates
        Waits for at least 1 successful download

        If ``account`` is ``None`` then a dictionary with accounts as keys will
        be returned containing all accounts

        If account is specified or the system has only 1 account the dictionary
        corresponding to that account is returned
        '''
        # Wait for at least 1 account update download to have been finished
        # before the cash can be returned to the calling client
        self._event_accdownload.wait()
        # Lock access to acc_cash to avoid an event intefering
        with self._lock_accupd:
            if account is None:
                # wait for the managedAccount Messages
                self._event_managed_accounts.wait()
                if len(self.managed_accounts) > 1:
                    return sum(self.acc_cash.values())

                # Only 1 account, fall through to return only 1
                account = self.managed_accounts[0]

            return self.acc_cash[account]
