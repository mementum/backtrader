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
from datetime import datetime
import time as _time
import json
import threading

import oandapy
import requests  # oandapy depdendency

import backtrader as bt
from backtrader import TimeFrame, Position
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import queue, with_metaclass
from backtrader.utils import AutoDict


# Extend the exceptions to support extra cases

class OandaRequestError(oandapy.OandaError):
    def __init__(self):
        er = dict(code=599, message='Request Error', description='')
        super(self.__class__, self).__init__(er)


class OandaStreamError(oandapy.OandaError):
    def __init__(self, content=''):
        er = dict(code=598, message='Failed Streaming', description=content)
        super(self.__class__, self).__init__(er)


class OandaTimeFrameError(oandapy.OandaError):
    def __init__(self, content):
        er = dict(code=597, message='Not supported TimeFrame', description='')
        super(self.__class__, self).__init__(er)


class OandaNetworkError(oandapy.OandaError):
    def __init__(self):
        er = dict(code=596, message='Network Error', description='')
        super(self.__class__, self).__init__(er)


class API(oandapy.API):
    def request(self, endpoint, method='GET', params=None):
        # Overriden to make something sensible out of a
        # request.RequestException rather than simply issuing a print(str(e))
        url = '%s/%s' % (self.api_url, endpoint)

        method = method.lower()
        params = params or {}

        func = getattr(self.client, method)

        request_args = {}
        if method == 'get':
            request_args['params'] = params
        else:
            request_args['data'] = params

        # Added the try block
        try:
            response = func(url, **request_args)
        except requests.RequestException as e:
            return OandaRequestError().error_response

        content = response.content.decode('utf-8')
        content = json.loads(content)

        # error message
        if response.status_code >= 400:
            # changed from raise to return
            return oandapy.OandaError(content).error_response

        return content


class Streamer(oandapy.Streamer):
    def __init__(self, q, headers=None, *args, **kwargs):
        # Override to provide headers, which is in the standard API interface
        super(Streamer, self).__init__(*args, **kwargs)

        if headers:
            self.client.headers.update(headers)

        self.q = q

    def run(self, endpoint, params=None):
        # Override to better manage exceptions.
        # Kept as much as possible close to the original
        self.connected = True

        params = params or {}

        ignore_heartbeat = None
        if 'ignore_heartbeat' in params:
            ignore_heartbeat = params['ignore_heartbeat']

        request_args = {}
        request_args['params'] = params

        url = '%s/%s' % (self.api_url, endpoint)

        while self.connected:
            # Added exception control here
            try:
                response = self.client.get(url, **request_args)
            except requests.RequestException as e:
                self.q.put(OandaRequestError().error_response)
                break

            if response.status_code != 200:
                self.on_error(response.content)
                break  # added break here

            # Changed chunk_size 90 -> None
            try:
                for line in response.iter_lines(chunk_size=None):
                    if not self.connected:
                        break

                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if not (ignore_heartbeat and 'heartbeat' in data):
                            self.on_success(data)

            except:  # socket.error has been seen
                self.q.put(OandaStreamError().error_response)
                break

    def on_success(self, data):
        if 'tick' in data:
            self.q.put(data['tick'])
        elif 'transaction' in data:
            self.q.put(data['transaction'])

    def on_error(self, data):
        self.disconnect()
        self.q.put(OandaStreamError(data).error_response)


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


class OandaStore(with_metaclass(MetaSingleton, object)):
    '''Singleton class wrapping to control the connections to Oanda.

    Params:

      - ``token`` (default:``None``): API access token

      - ``account`` (default: ``None``): account id

      - ``practice`` (default: ``False``): use the test environment
    '''

    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    params = (
        ('token', ''),
        ('account', ''),
        ('practice', False),
    )

    _DTEPOCH = datetime(1970, 1, 1)
    _ENVPRACTICE = 'practice'
    _ENVLIVE = 'live'

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''Returns ``DataCls`` with args, kwargs'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self):
        super(OandaStore, self).__init__()

        self.notifs = queue.Queue()  # store notifications for cerebro

        self._env = None  # reference to cerebro for general notifications
        self.broker = None  # broker instance
        self.datas = list()  # datas that have registered over start

        self.orders = collections.OrderedDict()  # map order.ref to oid
        self.orderrev = collections.OrderedDict()  # map oid to order.ref

        self._oenv = self._ENVPRACTICE if self.p.practice else self._ENVLIVE
        self.oapi = API(environment=self._oenv,
                        access_token=self.p.token,
                        headers={'X-Accept-Datetime-Format': 'UNIX'})

    def start(self, data=None, broker=None):
        # Datas require some processing to kickstart data reception
        if data is None and broker is None:
            self.cash = None
            return

        if data is not None:
            self._env = data._env
            # For datas simulate a queue with None to kickstart co
            self.datas.append(data)

        elif broker is not None:
            self.broker = broker

    def stop(self):
        pass  # nothing to do

    def get_notifications(self):
        '''Return the pending "store" notifications'''
        # The background thread could keep on adding notifications. The None
        # mark allows to identify which is the last notification to deliver
        self.notifs.put(None)  # put a mark
        notifs = list()
        while True:
            notif = self.notifs.get()
            if notif is None:  # mark is reached
                break
            notifs.append(notif)

        return notifs

    # Oanda supported granularities
    _GRANULARITIES = {
        (TimeFrame.Seconds, 5): 'S5',
        (TimeFrame.Seconds, 10): 'S10',
        (TimeFrame.Seconds, 15): 'S15',
        (TimeFrame.Seconds, 30): 'S30',
        (TimeFrame.Minutes, 1): 'M1',
        (TimeFrame.Minutes, 2): 'M3',
        (TimeFrame.Minutes, 3): 'M3',
        (TimeFrame.Minutes, 4): 'M4',
        (TimeFrame.Minutes, 5): 'M5',
        (TimeFrame.Minutes, 10): 'M5',
        (TimeFrame.Minutes, 15): 'M5',
        (TimeFrame.Minutes, 30): 'M5',
        (TimeFrame.Minutes, 60): 'H1',
        (TimeFrame.Minutes, 120): 'H2',
        (TimeFrame.Minutes, 180): 'H3',
        (TimeFrame.Minutes, 240): 'H4',
        (TimeFrame.Minutes, 360): 'H6',
        (TimeFrame.Minutes, 480): 'H8',
        (TimeFrame.Days, 1): 'D',
        (TimeFrame.Weeks, 1): 'W',
        (TimeFrame.Months, 1): 'M',
    }

    def get_granularity(self, timeframe, compression):
        return self._GRANULARITIES.get((timeframe, compression), None)

    def get_instrument(self, dataname):
        try:
            insts = self.oapi.get_instruments(self.p.account,
                                              instruments=dataname)
        except (oandapy.OandaError, OandaRequestError,):
            return None

        i = insts.get('instruments', [{}])
        return i[0] or None

    def streaming_events(self):
        q = queue.Queue()
        kwargs = {'q': q}

        t = threading.Thread(target=self._t_streaming_listener, kwargs=kwargs)
        t.daemon = True
        t.start()

        t = threading.Thread(target=self._t_streaming_events, kwargs=kwargs)
        t.daemon = True
        t.start()
        return q

    def _t_streaming_listener(self, q):
        trans = q.get()
        newcash = trans.get('accountBalance', None)
        if newcash is not None:
            self.cash = newcash
        self._transaction(trans)

    def _t_streaming_events(self, dataname, q):
        if tmout is not None:
            _time.sleep(tmout)

        streamer = StreamerEvents(q, environment=self._oenv,
                                  access_token=self.p.token,
                                  headers={'X-Accept-Datetime-Format': 'UNIX'})

        streamer.events(ignore_heartbeat=False)

    def candles(self, dataname, dtbegin, dtend, timeframe, compression,
                candleFormat, includeFirst):

        kwargs = locals().copy()
        kwargs.pop('self')
        kwargs['q'] = q = queue.Queue()
        t = threading.Thread(target=self._t_candles, kwargs=kwargs)
        t.daemon = True
        t.start()
        return q

    def _t_candles(self, dataname, dtbegin, dtend, timeframe, compression,
                   candleFormat, includeFirst, q):

        granularity = self.get_granularity(timeframe, compression)
        if granularity is None:
            e = OandaTimeFrameError()
            q.put(e.error_response)
            return

        dtkwargs = {}
        if dtbegin is not None:
            dtkwargs['start'] = int((dtbegin - self._DTEPOCH).total_seconds())

        if dtend is not None:
            dtkwargs['end'] = int((dtend - self._DTEPOCH).total_seconds())

        try:
            response = self.oapi.get_history(instrument=dataname,
                                             granularity=granularity,
                                             candleFormat=candleFormat,
                                             **dtkwargs)

        except oandapy.OandaError as e:
            q.put(e.error_response)
            q.put(None)  # CHECK
            return

        for candle in response.get('candles', []):
            q.put(candle)

        q.put({})  # end of transmission

    def streaming_prices(self, dataname, tmout=None):
        q = queue.Queue()
        kwargs = {'q': q, 'dataname': dataname, 'tmout': tmout}
        t = threading.Thread(target=self._t_streaming_prices, kwargs=kwargs)
        t.daemon = True
        t.start()
        return q

    def _t_streaming_prices(self, dataname, q, tmout):
        if tmout is not None:
            _time.sleep(tmout)

        streamer = Streamer(q, environment=self._oenv,
                            access_token=self.p.token,
                            headers={'X-Accept-Datetime-Format': 'UNIX'})

        streamer.rates(self.p.account, instruments=dataname)

    def get_cash(self):
        if self.cash is None:
            try:
                account = oanda.get_account(account_id=accid)
            except:  # no matter what
                self.cash = 0.0
            else:
                self.cash = float(account['balance'])

        return self.cash

    def get_value(self):
        # FIXME:
        return 0.0

    def getposition(self, instrument, clone=False):
        # Lock access to the position dicts. This is called from main
        # thread and updates could be happening in the background
        with self._lock_pos:
            position = self.positions[instrument]
            if clone:
                return position.clone()

            return position

    _ORDEREXECS = {
        bt.Order.Market: 'market',
        bt.Order.Limit: 'limit',
        bt.Order.Stop: 'stop',
    }

    def order_create(self, order, **kwargs):
        okwargs = dict()
        okwargs['instruments'] = order.data._dataname
        okwargs['units'] = abs(order.created.size)
        okwargs['side'] = 'buy' if order.isbuy() else 'sell'
        okwargs['type'] = self._ORDEREXECS[order.exectype]
        if order.exectype != bt.order.Market:
            okwargs['price'] = order.created.price
            if order.valid is None:
                valid = datetime.datetime.max
            else:
                valid = order.data.num2date(order.valid)

            # To timestamp with seconds precision
            okwargs['expiry'] = int((valid - self._DTEPOCH).total_seconds())

        okwargs.update(**kwargs)  # anything from the user

        t = threading.Thread(target=self._t_order_reate, args=(order,),
                             kwargs=okwargs)
        t.daemon = True
        t.start()
        return order

    def _t_order_create(self, order, **kwwargs):
        try:
            o = self.oapi.create_order(self.p.account, **kwargs)
        except Exception as e:
            order._o = {}
            self.broker._reject(order)
        else:
            order._o = _o = o.get('orderOpened', {})
            oref, oid = order.ref, _o['id']
            self._orders[oref] = oid
            self._ordersrev[oid] = oref
            self.broker._submit(order)

    def order_cancel(self, order):
        t = threading.Thread(target=self._t_order_cancel, args=(order,))
        t.daemon = True
        t.start()
        return order

    def _t_order_cancel(self, order, **kwwargs):
        oid = self.orders.get(order.ref, None)
        try:
            if oid is None:
                raise Exception

            o = self.oapi.close_order(self.p.account, oid)
        except Exception as e:
            pass
        else:
            order._o = o.get('orderOpened', {})
            self.broker._t_cancel()

    _X_ORDER_CREATE = ['MARKET_ORDER_CREATE', 'STOP_ORDER_CREATE',
                       'LIMIT_ORDER_CREATE', 'MARKET_IF_TOUCHED_ORDER_CREATE']

    _X_ORDER_CANCEL = ['ORDER_CANCEL']

    _X_ORDER_FILLED = ['ORDER_FILLED', 'TAKE_PROFIT_FILLED',
                       'STOP_LOSS_FILLED', 'TRAILING_STOP_FILLED']

    def _transaction(self, trans):
        oid = trans['id']
        ttype = trans['type']

        oref = self.order_refs[oid]

        if ttype in self._X_ORDER_CREATE:
            self.broker._accept(oref)

        elif ttype in self._X_ORDER_CANCEL:
            self.broker._cancel(oref)

        elif ttype in self._X_ORDER_FILLED:
            # FIXME: parse parameters
            self.broker._fill(oref, size, price)
