#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
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
from copy import copy
from datetime import date, datetime, timedelta
import inspect
import itertools
import random
import threading
import time
import logging
_logger = logging.getLogger()

from ctp import MdApi,TraderApi,FunBroker
from ctp import error as ctperror

from backtrader import TimeFrame, Position
from backtrader.store import Store
from backtrader.utils.py3 import bytes, bstr, queue, with_metaclass, long
from backtrader.utils import AutoDict, UTC


class RTVolume(object):

    def __init__(self, field):
        dt = field['ActionDay'] # 'ActionDay': '20210205'
        tm = field['UpdateTime'] # 'UpdateTime': '22:04:48'
        ms = field['UpdateMillisec'] # 'UpdateMillisec': 500
        self.datetime = datetime.strptime(f'{dt} {tm}.{ms}','%Y%m%d %H:%M:%S.%f')
        self.price = field['LastPrice'] # 'LastPrice': 4276.0
        self.volume = field['Volume'] # 'Volume': 796510
        self.openinterest = field['OpenInterest']  # 'OpenInterest': 18510.0


class LogBroker(FunBroker):
    '''derived only for logging, use base class directly is ok'''
    def errcheck(self, result, func, arguments):
        _logger.info(f'{self.funname}{self.origargs} {arguments} -> {result}')
        return super().errcheck(result, func, arguments)


class Md(MdApi):
    '''derived only for logging, use base class directly is ok'''
    def call_back(self,fun,p,rsp,res,last,ext):
        #print(f'{fun}({p},{rsp},{res},{last},{ext})')
        newargs = super().call_back(fun,p,rsp,res,last,ext)
        if fun != b'OnRtnDepthMarketData':
            fun = fun.decode()
            _logger.info(f'md:{fun}{newargs}')
        return newargs


class Td(TraderApi):
    '''derived only for logging, use base class directly is ok'''
    def call_back(self,fun,p,rsp,res,last,ext):
        #print(f'{fun}({p},{rsp},{res},{last},{ext})')
        newargs = super().call_back(fun,p,rsp,res,last,ext)
        fun = fun.decode()
        _logger.info(f'td:{fun}{newargs}')
        return newargs


# Decorator to mark methods to register with ctp
def ctpregister(f):
    f._ctpregister = True
    return f


class CTPStore(Store):
    '''Singleton class wrapping an ibpy ibConnection instance.

    The parameters can also be specified in the classes which use this store,
    like ``IBData`` and ``IBBroker``

    Params:

      - ``host`` (default:``127.0.0.1``): where IB TWS or IB Gateway are
        actually running. And although this will usually be the localhost, it
        must not be

      - ``port`` (default: ``7496``): port to connect to. The demo system uses
        ``7497``

      - ``clientId`` (default: ``None``): which clientId to use to connect to
        TWS.

        ``None``: generates a random id between 1 and 65535
        An ``integer``: will be passed as the value to use.

      - ``notifyall`` (default: ``False``)

        If ``False`` only ``error`` messages will be sent to the
        ``notify_store`` methods of ``Cerebro`` and ``Strategy``.

        If ``True``, each and every message received from TWS will be notified

      - ``_debug`` (default: ``False``)

        Print all messages received from TWS to standard output

      - ``reconnect`` (default: ``3``)

        Number of attempts to try to reconnect after the 1st connection attempt
        fails

        Set it to a ``-1`` value to keep on reconnecting forever

      - ``timeout`` (default: ``3.0``)

        Time in seconds between reconnection attemps

      - ``timeoffset`` (default: ``True``)

        If True, the time obtained from ``reqCurrentTime`` (IB Server time)
        will be used to calculate the offset to localtime and this offset will
        be used for the price notifications (tickPrice events, for example for
        CASH markets) to modify the locally calculated timestamp.

        The time offset will propagate to other parts of the ``backtrader``
        ecosystem like the **resampling** to align resampling timestamps using
        the calculated offset.

      - ``timerefresh`` (default: ``60.0``)

        Time in seconds: how often the time offset has to be refreshed

      - ``indcash`` (default: ``True``)

        Manage IND codes as if they were cash for price retrieval
    '''

    # Set a base for the data requests (historical/realtime) to distinguish the
    # id in the error notifications from orders, where the basis (usually
    # starting at 1) is set by TWS
    REQIDBASE = 0x01000000

    params = (
        ('mdfront', 'tcp://180.168.146.187:10110'),
        ('tdfront', 'tcp://180.168.146.187:10101'),
        ('brokerid', '9999'),
        ('username', '010631'),
        ('password', '123456'),
        ('notifyall', False),
        ('_debug', False),
        ('timeout', 10.0),  # timeout between reconnections
        ('timeoffset', True),  # Use offset to server for timestamps if needed
        ('timerefresh', 60.0),  # How often to refresh the timeoffset
    )

    def __init__(self):
        super(CTPStore, self).__init__()

        self._lock_q = threading.Lock()  # sync access to _tickerId/Queues
        self._lock_accupd = threading.Lock()  # sync account updates
        self._lock_pos = threading.Lock()  # sync account updates
        self._lock_notif = threading.Lock()  # sync access to notif queue

        # Account list received
        self._event_managed_accounts = threading.Event()
        self._event_accdownload = threading.Event()

        self.dontreconnect = False  # for non-recoverable connect errors

        self._env = None  # reference to cerebro for general notifications
        self.broker = None  # broker instance
        self.datas = list()  # datas that have registered over start
        self.ccount = 0  # requests to start (from cerebro or datas)

        self._lock_tmoffset = threading.Lock()
        self.tmoffset = timedelta()  # to control time difference with server

        # Structures to hold datas requests
        self.qs = collections.OrderedDict()  # key: tickerId -> queues
        self.ts = collections.OrderedDict()  # key: queue -> tickerId
        self.iscash = dict()  # tickerIds from cash products (for ex: EUR.JPY)

        self.histexreq = dict()  # holds segmented historical requests
        self.histfmt = dict()  # holds datetimeformat for request
        self.histsend = dict()  # holds sessionend (data time) for request
        self.histtz = dict()  # holds sessionend (data time) for request

        self.acc_cash = AutoDict()  # current total cash per account
        self.acc_value = AutoDict()  # current total value per account
        self.acc_upds = AutoDict()  # current account valueinfos per account

        self.port_update = False  # indicate whether to signal to broker

        self.positions = collections.defaultdict(Position)  # actual positions

        self._tickerId = itertools.count(self.REQIDBASE)  # unique tickerIds
        self.orderid = None  # next possible orderid (will be itertools.count)

        self.cdetails = collections.defaultdict(list)  # hold cdetails requests

        self.managed_accounts = list()  # received via managedAccounts

        self.notifs = queue.Queue()  # store notifications for cerebro

        self.reqid = itertools.count(1)
        self.mdconnectevent = threading.Event()
        self.tdconnectevent = threading.Event()
        self.mdloginevent = threading.Event()
        self.tdloginevent = threading.Event()
        self.mdlogined = False  # user login state
        self.tdlogined = False
        self.mderrcode = ctperror.NONE
        self.tderrcode = ctperror.NONE
        self.md = Md(broker=LogBroker)  # create md instance
        self.td = Td(broker=LogBroker)
        # Register decorated methods in md instance
        methods = inspect.getmembers(self, inspect.ismethod)
        for name, method in methods:
            if getattr(method, '_ctpregister', False):
                segs = name.split('_')
                api = getattr(self, segs[0], None)
                if api:
                    setattr(api,segs[-1],method)

        self.md.RegisterFront(self.p.mdfront)  # registe ctp md front
        self.td.RegisterFront(self.p.tdfront)
        self.md.Init()  # init ctp
        self.td.Init()


    def start(self, data=None, broker=None):
        super(CTPStore, self).start(data,broker)
        self.reconnect(fromstart=True)  # reconnect should be an invariant

    def stop(self):
        super(CTPStore, self).stop()

    def logmsg(self, *args):
        # for logging purposes
        if self.p._debug:
            _logger.info(*args)


    def connected(self):
        return self.mdlogined and self.tdlogined  # non-connected (including non-initialized)


    def reconnect(self, fromstart=False, resub=False):

        if self.connected():
            if resub:
                self.startdatas()
            return True  # nothing to do

        while not self.connected():
            if not (self.mdconnectevent.wait(timeout=self.p.timeout) and self.tdconnectevent.wait(timeout=self.p.timeout)):
                return False
            if not self.mdlogined:
                self.mdloginevent.clear()
                self.mderrcode = ctperror.NONE
                self.md.ReqUserLogin(dict(BrokerID=self.p.brokerid,UserID=self.p.username,Password=self.p.password),next(self.reqid))
            if not self.tdlogined:
                self.tdloginevent.clear()
                self.tderrcode = ctperror.NONE
                self.td.ReqUserLogin(dict(BrokerID=self.p.brokerid,UserID=self.p.username,Password=self.p.password),next(self.reqid))

            if not self.mdlogined:
                self.mdloginevent.wait(timeout=self.p.timeout)
                if self.mderrcode in (ctperror.INVALID_LOGIN,):
                    return False
            if not self.tdlogined:
                self.tdloginevent.wait(timeout=self.p.timeout)
                if self.tderrcode in (ctperror.INVALID_LOGIN,):
                    return False

        if self.connected():
            if not fromstart or resub:
                self.startdatas()
            return True
        return False


    def startdatas(self):
        # kickstrat datas, not returning until all of them have been done
        for data in self.datas:
            data.reqdata()


    def stopdatas(self):
        # stop subs and force datas out of the loop (in LIFO order)
        for data in self.datas:
            data.canceldata()

    
    @ctpregister
    def md_OnFrontConnected(self):
        self.mdconnectevent.set()

    @ctpregister
    def td_OnFrontConnected(self):
        self.tdconnectevent.set()


    @ctpregister
    def md_OnFrontDisconnected(self, reason):
        # when disconnected, the low api will auto reconncet
        connected = self.connected()
        self.mdlogined = False
        self.mdconnectevent.clear()
        self.mdloginevent.set() # in case of logining and disconnect
        # notify datas disconnected
        if connected:
            with self._lock_q:
                for q in self.ts:
                    q.put(None)
    

    @ctpregister
    def td_OnFrontDisconnected(self, reason):
        # when disconnected, the low api will auto reconncet
        connected = self.connected()
        self.tdlogined = False
        self.tdconnectevent.clear()
        self.tdloginevent.set() # in case of logining and disconnect
        # notify datas disconnected
        if connected:
            with self._lock_q:
                for q in self.ts:
                    q.put(None)


    @ctpregister
    def md_OnRspUserLogin(self, field, info, reqid, islast):
        # md:OnRspUserLogin[{'TradingDay': '20210113', 'LoginTime': '', 'BrokerID': '', 'UserID': '', 'SystemName': '', 'FrontID': 0, 'SessionID': 0, 'MaxOrderRef': '', 'SHFETime': '', 'DCETime': '', 'CZCETime': '', 'FFEXTime': '', 'INETime': ''}, {'ErrorID': 0, 'ErrorMsg': 'CTP:No Error'}, 0, True]
        errcode = info['ErrorID']
        if errcode == ctperror.NONE:
            self.mdlogined = True
        self.mderrcode = errcode
        self.logmsg(f'user {self.p.username} mdlogin {info}')
        self.mdloginevent.set() #succeed or fail


    @ctpregister
    def td_OnRspUserLogin(self, field, info, reqid, islast):
        # 
        errcode = info['ErrorID']
        if errcode == ctperror.NONE:
            self.tdlogined = True
        self.tderrcode = errcode
        self.logmsg(f'user {self.p.username} tdlogin {info}')
        self.tdloginevent.set() #succeed or fail


    @ctpregister
    def md_OnRspUserLogout(self, field, info, reqid, islast):
        pass

    @ctpregister
    def md_OnRspSubMarketData(self, field, info, reqid, islast):
        # the info['ErrorID'] always ctperror.NONE,even if sub InstrumentID not exist
        pass

    @ctpregister
    def md_OnRspUnSubMarketData(self, field, info, reqid, islast):
        # the info['ErrorID'] always ctperror.NONE,even if sub InstrumentID not exist
        pass


    @ctpregister
    def md_OnRtnDepthMarketData(self, field):
        # {'TradingDay': '20210205', 'InstrumentID': 'rb2105', 'ExchangeID': '', 'ExchangeInstID': '', 
        # 'LastPrice': 4275.0, 'PreSettlementPrice': 4216.0, 'PreClosePrice': 4246.0, 
        # 'PreOpenInterest': 1174941.0, 'OpenPrice': 4243.0, 'HighestPrice': 4279.0, 'LowestPrice': 4226.0, 
        # 'Volume': 796475, 'Turnover': 33813341680.0, 'OpenInterest': 1154243.0, 'ClosePrice': 1.7976931348623157e+308, 
        # 'SettlementPrice': 1.7976931348623157e+308, 'UpperLimitPrice': 4426.0, 'LowerLimitPrice': 4005.0, 
        # 'PreDelta': 0.0, 'CurrDelta': 1.7976931348623157e+308, 'UpdateTime': '10:56:23', 'UpdateMillisec': 0, 
        # 'BidPrice1': 4275.0, 'BidVolume1': 94, 'AskPrice1': 4276.0, 'AskVolume1': 642, 'BidPrice2': 1.7976931348623157e+308, 
        # 'BidVolume2': 0, 'AskPrice2': 1.7976931348623157e+308, 'AskVolume2': 0, 'BidPrice3': 1.7976931348623157e+308, 
        # 'BidVolume3': 0, 'AskPrice3': 1.7976931348623157e+308, 'AskVolume3': 0, 'BidPrice4': 1.7976931348623157e+308, 
        # 'BidVolume4': 0, 'AskPrice4': 1.7976931348623157e+308, 'AskVolume4': 0, 'BidPrice5': 1.7976931348623157e+308, 
        # 'BidVolume5': 0, 'AskPrice5': 1.7976931348623157e+308, 'AskVolume5': 0, 'AveragePrice': 42453.738886970714, 
        # 'ActionDay': '20210205'}
        contract = field['InstrumentID']
        self.qs[contract].put(RTVolume(field))


    @ctpregister
    def md_OnRspError(self, info, reqid, islast):
        self.logmsg(f'md:OnRspError:{info} {reqid} {islast}')
        errcode = info['ErrorID']
        self.mderrcode = errcode
        with self._lock_q:
            for q in self.ts:
                q.put(errcode)
    
    @ctpregister
    def td_OnRspError(self, info, reqid, islast):
        self.logmsg(f'td:OnRspError:{info} {reqid} {islast}')
        errcode = info['ErrorID']
        self.tderrcode = errcode
        with self._lock_q:
            for q in self.ts:
                q.put(errcode)


    def timeoffset(self):
        with self._lock_tmoffset:
            return self.tmoffset

    def getQueue(self, contract=None):
        '''Creates ticker/Queue for data delivery to a data feed'''
        with self._lock_q:
            if contract in self.qs:
                return self.qs[contract]
            else:
                q = queue.Queue()
                if contract:
                    self.qs[contract] = q  # can be managed from other thread
                    self.ts[q] = contract
                else:
                    q.put(None)
                return q

    def cancelQueue(self, q, sendnone=False):
        '''Cancels a Queue for data delivery'''
        # pop ts (tickers) and with the result qs (queues)
        with self._lock_q:
            contract = self.ts.pop(q, None)
            self.qs.pop(contract, None)
        if sendnone:
            q.put(None)

    def validQueue(self, q):
        '''Returns (bool)  if a queue is still valid'''
        return q in self.ts  # queue -> ticker


    def reqMktData(self, contract):
        '''Creates a MarketData subscription

        Params:
          - contract: a ib.ext.Contract.Contract intance

        Returns:
          - a Queue the client can wait on to receive a RTVolume instance
        '''
        # get a ticker/queue for identification/data delivery
        q = self.getQueue(contract)
        if self.connected():
            self.md.SubscribeMarketData([contract])
        return q

    def cancelMktData(self, q):
        '''Cancels an existing MarketData subscription

        Params:
          - q: the Queue returned by reqMktData
        '''
        with self._lock_q:
            contract = self.ts.get(q, None)
        if contract and self.connected():
            self.md.UnSubscribeMarketData([contract])
        self.cancelQueue(q, True)

