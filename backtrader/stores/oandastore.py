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

from datetime import datetime
import time as _time
import json
import threading

import oandapy
import requests  # oandapy depdendency

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

        self._oenv = self._ENVPRACTICE if self.p.practice else self._ENVLIVE
        self.oapi = API(environment=self._oenv,
                        access_token=self.p.token,
                        headers={'X-Accept-Datetime-Format': 'UNIX'})

    def start(self, data=None, broker=None):
        # Datas require some processing to kickstart data reception
        if data is not None:
            self._env = data._env
            # For datas simulate a queue with None to kickstart co
            self.datas.append(data)

        elif broker is not None:
            self.broker = broker

    def stop(self):
        pass  # nothing to do

    def logmsg(self, *args):
        # for logging purposes
        if self.p._debug:
            print(*args)

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
            q.put(None)  # CHECK
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

    if False:
        def getposition(self, contract, clone=False):
            # Lock access to the position dicts. This is called from main
            # thread and updates could be happening in the background
            with self._lock_pos:
                position = self.positions[contract.m_conId]
                if clone:
                    return copy(position)

                return position
