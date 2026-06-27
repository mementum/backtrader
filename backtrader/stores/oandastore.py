#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
import time as _time
import json
import threading

import oandapy
import requests  # oandapy 依赖

import backtrader as bt
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import queue, with_metaclass
from backtrader.utils import AutoDict


# 扩展异常以支持额外场景

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
        # 覆盖默认逻辑，将 request.RequestException 转成可处理响应，
        # 而不是仅执行 print(str(e))
        url = '%s/%s' % (self.api_url, endpoint)

        method = method.lower()
        params = params or {}

        func = getattr(self.client, method)

        request_args = {}
        if method == 'get':
            request_args['params'] = params
        else:
            request_args['data'] = params

        # 增加异常捕获
        try:
            response = func(url, **request_args)
        except requests.RequestException as e:
            return OandaRequestError().error_response

        content = response.content.decode('utf-8')
        content = json.loads(content)

        # 错误消息
        if response.status_code >= 400:
            # 从 raise 改为 return
            return oandapy.OandaError(content).error_response

        return content


class Streamer(oandapy.Streamer):
    def __init__(self, q, headers=None, *args, **kwargs):
        # 覆盖以提供 headers，该能力存在于标准 API interface 中
        super(Streamer, self).__init__(*args, **kwargs)

        if headers:
            self.client.headers.update(headers)

        self.q = q

    def run(self, endpoint, params=None):
        # 覆盖以更好地管理异常，并尽量保持接近原始实现
        self.connected = True

        params = params or {}

        ignore_heartbeat = None
        if 'ignore_heartbeat' in params:
            ignore_heartbeat = params['ignore_heartbeat']

        request_args = {}
        request_args['params'] = params

        url = '%s/%s' % (self.api_url, endpoint)

        while self.connected:
            # 在这里增加异常控制
            try:
                response = self.client.get(url, **request_args)
            except requests.RequestException as e:
                self.q.put(OandaRequestError().error_response)
                break

            if response.status_code != 200:
                self.on_error(response.content)
                break  # 在这里增加 break

            # chunk_size 从 90 改为 None
            try:
                for line in response.iter_lines(chunk_size=None):
                    if not self.connected:
                        break

                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if not (ignore_heartbeat and 'heartbeat' in data):
                            self.on_success(data)

            except:  # 曾观察到 socket.error
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
    '''让带 metaclass 的类成为 singleton 的 metaclass。'''
    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


class OandaStore(with_metaclass(MetaSingleton, object)):
    '''控制 Oanda 连接的 singleton store。

    Args:
        token: API access token。
        account: account id。
        practice: 是否使用测试环境。
        account_tmout: account value/cash 刷新周期。

    Returns:
        OandaStore: 用于管理 Oanda API、streaming、order 与 account 状态的 store。
    '''

    BrokerCls = None  # broker class 会自动注册
    DataCls = None  # data class 会自动注册

    params = (
        ('token', ''),
        ('account', ''),
        ('practice', False),
        ('account_tmout', 10.0),  # account balance 刷新 timeout
    )

    _DTEPOCH = datetime(1970, 1, 1)
    _ENVPRACTICE = 'practice'
    _ENVLIVE = 'live'

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''使用 args/kwargs 返回 ``DataCls`` 实例。'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''使用注册的 ``BrokerCls`` 与 args/kwargs 返回 broker。'''
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self):
        super(OandaStore, self).__init__()

        self.notifs = collections.deque()  # 发送给 cerebro 的 store 通知

        self._env = None  # 指向 cerebro，用于通用通知
        self.broker = None  # broker 实例
        self.datas = list()  # start 期间注册的 data

        self._orders = collections.OrderedDict()  # 映射 order.ref -> oid
        self._ordersrev = collections.OrderedDict()  # 映射 oid -> order.ref
        self._transpend = collections.defaultdict(collections.deque)

        self._oenv = self._ENVPRACTICE if self.p.practice else self._ENVLIVE
        self.oapi = API(environment=self._oenv,
                        access_token=self.p.token,
                        headers={'X-Accept-Datetime-Format': 'UNIX'})

        self._cash = 0.0
        self._value = 0.0
        self._evt_acct = threading.Event()

    def start(self, data=None, broker=None):
        # data 需要一些处理来启动数据接收
        if data is None and broker is None:
            self.cash = None
            return

        if data is not None:
            self._env = data._env
            # 对 data 使用带 None 的模拟 queue 启动连接
            self.datas.append(data)

            if self.broker is not None:
                self.broker.data_started(data)

        elif broker is not None:
            self.broker = broker
            self.streaming_events()
            self.broker_threads()

    def stop(self):
        # 标记线程结束
        if self.broker is not None:
            self.q_ordercreate.put(None)
            self.q_orderclose.put(None)
            self.q_account.put(None)

    def put_notification(self, msg, *args, **kwargs):
        self.notifs.append((msg, args, kwargs))

    def get_notifications(self):
        '''返回待处理的 "store" 通知。'''
        self.notifs.append(None)  # 放置标记；线程仍可能继续 append
        return [x for x in iter(self.notifs.popleft, None)]

    # Oanda 支持的 granularity
    _GRANULARITIES = {
        (bt.TimeFrame.Seconds, 5): 'S5',
        (bt.TimeFrame.Seconds, 10): 'S10',
        (bt.TimeFrame.Seconds, 15): 'S15',
        (bt.TimeFrame.Seconds, 30): 'S30',
        (bt.TimeFrame.Minutes, 1): 'M1',
        (bt.TimeFrame.Minutes, 2): 'M3',
        (bt.TimeFrame.Minutes, 3): 'M3',
        (bt.TimeFrame.Minutes, 4): 'M4',
        (bt.TimeFrame.Minutes, 5): 'M5',
        (bt.TimeFrame.Minutes, 10): 'M5',
        (bt.TimeFrame.Minutes, 15): 'M5',
        (bt.TimeFrame.Minutes, 30): 'M5',
        (bt.TimeFrame.Minutes, 60): 'H1',
        (bt.TimeFrame.Minutes, 120): 'H2',
        (bt.TimeFrame.Minutes, 180): 'H3',
        (bt.TimeFrame.Minutes, 240): 'H4',
        (bt.TimeFrame.Minutes, 360): 'H6',
        (bt.TimeFrame.Minutes, 480): 'H8',
        (bt.TimeFrame.Days, 1): 'D',
        (bt.TimeFrame.Weeks, 1): 'W',
        (bt.TimeFrame.Months, 1): 'M',
    }

    def get_positions(self):
        try:
            positions = self.oapi.get_positions(self.p.account)
        except (oandapy.OandaError, OandaRequestError,):
            return None

        poslist = positions.get('positions', [])
        return poslist

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

    def streaming_events(self, tmout=None):
        q = queue.Queue()
        kwargs = {'q': q, 'tmout': tmout}

        t = threading.Thread(target=self._t_streaming_listener, kwargs=kwargs)
        t.daemon = True
        t.start()

        t = threading.Thread(target=self._t_streaming_events, kwargs=kwargs)
        t.daemon = True
        t.start()
        return q

    def _t_streaming_listener(self, q, tmout=None):
        while True:
            trans = q.get()
            self._transaction(trans)

    def _t_streaming_events(self, q, tmout=None):
        if tmout is not None:
            _time.sleep(tmout)

        streamer = Streamer(q,
                            environment=self._oenv,
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
            q.put(None)
            return

        for candle in response.get('candles', []):
            q.put(candle)

        q.put({})  # 传输结束

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
        return self._cash

    def get_value(self):
        return self._value

    _ORDEREXECS = {
        bt.Order.Market: 'market',
        bt.Order.Limit: 'limit',
        bt.Order.Stop: 'stop',
        bt.Order.StopLimit: 'stop',
    }

    def broker_threads(self):
        self.q_account = queue.Queue()
        self.q_account.put(True)  # 强制立即更新
        t = threading.Thread(target=self._t_account)
        t.daemon = True
        t.start()

        self.q_ordercreate = queue.Queue()
        t = threading.Thread(target=self._t_order_create)
        t.daemon = True
        t.start()

        self.q_orderclose = queue.Queue()
        t = threading.Thread(target=self._t_order_cancel)
        t.daemon = True
        t.start()

        # 等待一次，确保值已设置
        self._evt_acct.wait(self.p.account_tmout)

    def _t_account(self):
        while True:
            try:
                msg = self.q_account.get(timeout=self.p.account_tmout)
                if msg is None:
                    break  # 线程结束
            except queue.Empty:  # timeout -> 到刷新时间
                pass

            try:
                accinfo = self.oapi.get_account(self.p.account)
            except Exception as e:
                self.put_notification(e)
                continue

            try:
                self._cash = accinfo['marginAvail']
                self._value = accinfo['balance']
            except KeyError:
                pass

            self._evt_acct.set()

    def order_create(self, order, stopside=None, takeside=None, **kwargs):
        okwargs = dict()
        okwargs['instrument'] = order.data._dataname
        okwargs['units'] = abs(order.created.size)
        okwargs['side'] = 'buy' if order.isbuy() else 'sell'
        okwargs['type'] = self._ORDEREXECS[order.exectype]
        if order.exectype != bt.Order.Market:
            okwargs['price'] = order.created.price
            if order.valid is None:
                # 1 年和 datetime.max 会失败；1 个月可用
                valid = datetime.utcnow() + timedelta(days=30)
            else:
                valid = order.data.num2date(order.valid)
                # 转成秒级 timestamp
            okwargs['expiry'] = int((valid - self._DTEPOCH).total_seconds())

        if order.exectype == bt.Order.StopLimit:
            okwargs['lowerBound'] = order.created.pricelimit
            okwargs['upperBound'] = order.created.pricelimit

        if order.exectype == bt.Order.StopTrail:
            okwargs['trailingStop'] = order.trailamount

        if stopside is not None:
            okwargs['stopLoss'] = stopside.price

        if takeside is not None:
            okwargs['takeProfit'] = takeside.price

        okwargs.update(**kwargs)  # 用户传入的其他内容

        self.q_ordercreate.put((order.ref, okwargs,))
        return order

    _OIDSINGLE = ['orderOpened', 'tradeOpened', 'tradeReduced']
    _OIDMULTIPLE = ['tradesClosed']

    def _t_order_create(self):
        while True:
            msg = self.q_ordercreate.get()
            if msg is None:
                break

            oref, okwargs = msg
            try:
                o = self.oapi.create_order(self.p.account, **okwargs)
            except Exception as e:
                self.put_notification(e)
                self.broker._reject(oref)
                return

            # id 会在不同字段中返回，必须全部取出，才能作为 execution 匹配到这里生成的 order
            oids = list()
            for oidfield in self._OIDSINGLE:
                if oidfield in o and 'id' in o[oidfield]:
                    oids.append(o[oidfield]['id'])

            for oidfield in self._OIDMULTIPLE:
                if oidfield in o:
                    for suboidfield in o[oidfield]:
                        oids.append(suboidfield['id'])

            if not oids:
                self.broker._reject(oref)
                return

            self._orders[oref] = oids[0]
            self.broker._submit(oref)
            if okwargs['type'] == 'market':
                self.broker._accept(oref)  # 立即接收

            for oid in oids:
                self._ordersrev[oid] = oref  # 映射 id 到 backtrader order

                # transaction 可能已经发生并被暂存
                tpending = self._transpend[oid]
                tpending.append(None)  # eom 标记
                while True:
                    trans = tpending.popleft()
                    if trans is None:
                        break
                    self._process_transaction(oid, trans)

    def order_cancel(self, order):
        self.q_orderclose.put(order.ref)
        return order

    def _t_order_cancel(self):
        while True:
            oref = self.q_orderclose.get()
            if oref is None:
                break

            oid = self._orders.get(oref, None)
            if oid is None:
                continue  # order 已不存在
            try:
                o = self.oapi.close_order(self.p.account, oid)
            except Exception as e:
                continue  # 未取消 - FIXME: 通知

            self.broker._cancel(oref)

    _X_ORDER_CREATE = ('STOP_ORDER_CREATE',
                       'LIMIT_ORDER_CREATE', 'MARKET_IF_TOUCHED_ORDER_CREATE',)

    def _transaction(self, trans):
        # 从 Streaming Events 调用。可能收到某个 oid 的事件，但创建 order 后该 oid 尚未返回。
        # 因此未见过时先暂存，否则转发给处理器。
        ttype = trans['type']
        if ttype == 'MARKET_ORDER_CREATE':
            try:
                oid = trans['tradeReduced']['id']
            except KeyError:
                try:
                    oid = trans['tradeOpened']['id']
                except KeyError:
                    return  # 无法继续处理

        elif ttype in self._X_ORDER_CREATE:
            oid = trans['id']
        elif ttype == 'ORDER_FILLED':
            oid = trans['orderId']

        elif ttype == 'ORDER_CANCEL':
            oid = trans['orderId']

        elif ttype == 'TRADE_CLOSE':
            oid = trans['id']
            pid = trans['tradeId']
            if pid in self._orders and False:  # 对 trade 无可用信息
                return  # 无法处理

            # 跳过上方逻辑；当前不做处理。
            # 例如直接从 WebGUI 收到关闭现有 position 的事件，该 position 关联 order id -> pid。
            # 可考虑生成一个假的反向 order，以平滑关闭现有 position。
            msg = ('Received TRADE_CLOSE for unknown order, possibly generated'
                   ' over a different client or GUI')
            self.put_notification(msg, trans)
            return

        else:  # 平稳退出未知情况
            try:
                oid = trans['id']
            except KeyError:
                oid = 'None'

            msg = 'Received {} with oid {}. Unknown situation'
            msg = msg.format(ttype, oid)
            self.put_notification(msg, trans)
            return

        try:
            oref = self._ordersrev[oid]
            self._process_transaction(oid, trans)
        except KeyError:  # 尚未见过，保留为 pending
            self._transpend[oid].append(trans)

    _X_ORDER_FILLED = ('MARKET_ORDER_CREATE',
                       'ORDER_FILLED', 'TAKE_PROFIT_FILLED',
                       'STOP_LOSS_FILLED', 'TRAILING_STOP_FILLED',)

    def _process_transaction(self, oid, trans):
        try:
            oref = self._ordersrev.pop(oid)
        except KeyError:
            return

        ttype = trans['type']

        if ttype in self._X_ORDER_FILLED:
            size = trans['units']
            if trans['side'] == 'sell':
                size = -size
            price = trans['price']
            self.broker._fill(oref, size, price, ttype=ttype)

        elif ttype in self._X_ORDER_CREATE:
            self.broker._accept(oref)
            self._ordersrev[oid] = oref

        elif ttype in 'ORDER_CANCEL':
            reason = trans['reason']
            if reason == 'ORDER_FILLED':
                pass  # 单个 execution 已完成工作
            elif reason == 'TIME_IN_FORCE_EXPIRED':
                self.broker._expire(oref)
            elif reason == 'CLIENT_REQUEST':
                self.broker._cancel(oref)
            else:  # 其他情况的默认动作
                self.broker._reject(oref)
