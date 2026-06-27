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
from copy import copy
from datetime import date, datetime, timedelta
import inspect
import itertools
import random
import threading
import time

from ib.ext.Contract import Contract
import ib.opt as ibopt

from backtrader import TimeFrame, Position
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import bytes, bstr, queue, with_metaclass, long
from backtrader.utils import AutoDict, UTC

bytes = bstr  # ibpy 需要 py2/3 兼容 bytes


def _ts2dt(tstamp=None):
    # 将 RTVolume timestamp 转为 datetime 对象
    if not tstamp:
        return datetime.utcnow()

    sec, msec = divmod(long(tstamp), 1000)
    usec = msec * 1000
    return datetime.utcfromtimestamp(sec).replace(microsecond=usec)


class RTVolume(object):
    '''将 IB API 中 tickString tickType 48（RTVolume）事件解析为组成字段。

    支持使用 "price" 从 tickPrice event 模拟 RTVolume。
    '''
    _fields = [
        ('price', float),
        ('size', int),
        ('datetime', _ts2dt),
        ('volume', int),
        ('vwap', float),
        ('single', bool)
    ]

    def __init__(self, rtvol='', price=None, tmoffset=None):
        # 使用传入字符串，或模拟一个空 token 列表
        tokens = iter(rtvol.split(';'))

        # 使用对应 func 将 token 放入属性
        for name, func in self._fields:
            setattr(self, name, func(next(tokens)) if rtvol else func())

        # 如提供 price，则使用该值
        if price is not None:
            self.price = price

        if tmoffset is not None:
            self.datetime += tmoffset


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


# 标记方法需要注册到 ib.opt 的 decorator
def ibregister(f):
    f._ibregister = True
    return f


class IBStore(with_metaclass(MetaSingleton, object)):
    '''封装 ibpy ibConnection 实例的 singleton store。

    参数也可在使用该 store 的类中指定，例如 ``IBData`` 和 ``IBBroker``。

    Args:
        host: IB TWS 或 IB Gateway 实际运行的 host，通常是 localhost，但并非必须。
        port: 连接端口。demo 系统使用 ``7497``。
        clientId: 连接 TWS 使用的 clientId。``None`` 表示随机生成 1 到 65535 之间的 id。
        notifyall: 是否将收到的所有 TWS 消息都通知给 ``notify_store``。
        _debug: 是否将收到的全部 TWS 消息打印到标准输出。
        reconnect: 第一次连接失败后的重连次数；``-1`` 表示永久重连。
        timeout: 重连尝试之间的秒数。
        timeoffset: 是否用 ``reqCurrentTime`` 获取 IB Server time 并计算本地时间偏移。
        timerefresh: 刷新 time offset 的秒数间隔。
        indcash: 是否像 cash 一样管理 IND 代码以获取价格。

    Returns:
        IBStore: 用于管理 IB 连接、data request、order/account 回调的 store。
    '''

    # 为 data request（historical/realtime）设置 id 基准，以便在 error notification 中
    # 与 order id 区分。order id 的基准通常由 TWS 设置，并从 1 附近开始。
    REQIDBASE = 0x01000000

    BrokerCls = None  # broker class 会自动注册
    DataCls = None  # data class 会自动注册

    params = (
        ('host', '127.0.0.1'),
        ('port', 7496),
        ('clientId', None),  # None generates a random clientid 1 -> 2^16
        ('notifyall', False),
        ('_debug', False),
        ('reconnect', 3),  # -1 forever, 0 No, > 0 number of retries
        ('timeout', 3.0),  # timeout between reconnections
        ('timeoffset', True),  # Use offset to server for timestamps if needed
        ('timerefresh', 60.0),  # How often to refresh the timeoffset
        ('indcash', True),  # Treat IND codes as CASH elements
    )

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''使用 args/kwargs 返回 ``DataCls`` 实例。'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''使用注册的 ``BrokerCls`` 与 args/kwargs 返回 broker。'''
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self):
        super(IBStore, self).__init__()

        self._lock_q = threading.Lock()  # 同步访问 _tickerId/Queues
        self._lock_accupd = threading.Lock()  # 同步 account 更新
        self._lock_pos = threading.Lock()  # 同步 position 更新
        self._lock_notif = threading.Lock()  # 同步访问 notification queue

        # account list 已接收
        self._event_managed_accounts = threading.Event()
        self._event_accdownload = threading.Event()

        self.dontreconnect = False  # 用于不可恢复连接错误

        self._env = None  # 指向 cerebro，用于通用通知
        self.broker = None  # broker 实例
        self.datas = list()  # start 期间注册的 data
        self.ccount = 0  # 来自 cerebro 或 data 的 start request 数量

        self._lock_tmoffset = threading.Lock()
        self.tmoffset = timedelta()  # 控制与 server 的时间差

        # 保存 data request 的结构
        self.qs = collections.OrderedDict()  # key: tickerId -> queues
        self.ts = collections.OrderedDict()  # key: queue -> tickerId
        self.iscash = dict()  # cash 产品的 tickerId（例如 EUR.JPY）

        self.histexreq = dict()  # 保存分段 historical request
        self.histfmt = dict()  # 保存 request 的 datetimeformat
        self.histsend = dict()  # 保存 request 的 sessionend（data time）
        self.histtz = dict()  # 保存 request 的 timezone

        self.acc_cash = AutoDict()  # 每个 account 当前 total cash
        self.acc_value = AutoDict()  # 每个 account 当前 total value
        self.acc_upds = AutoDict()  # 每个 account 当前 value info

        self.port_update = False  # 指示是否需要通知 broker

        self.positions = collections.defaultdict(Position)  # 实际 position

        self._tickerId = itertools.count(self.REQIDBASE)  # 唯一 tickerId
        self.orderid = None  # 下一个可用 orderid（会是 itertools.count）

        self.cdetails = collections.defaultdict(list)  # 保存 cdetails request

        self.managed_accounts = list()  # 通过 managedAccounts 接收

        self.notifs = queue.Queue()  # 发送给 cerebro 的 store 通知

        # 使用提供的 clientId，或随机生成一个
        if self.p.clientId is None:
            self.clientId = random.randint(1, pow(2, 16) - 1)
        else:
            self.clientId = self.p.clientId

        # ibpy connection 对象
        self.conn = ibopt.ibConnection(
            host=self.p.host, port=self.p.port, clientId=self.clientId)

        # 按需注册 printall 方法
        if self.p._debug or self.p.notifyall:
            self.conn.registerAll(self.watcher)

        # 将带 decorator 的方法注册到 conn
        methods = inspect.getmembers(self, inspect.ismethod)
        for name, method in methods:
            if not getattr(method, '_ibregister', False):
                continue

            message = getattr(ibopt.message, name)
            self.conn.register(method, message)

        # 该工具 key 函数将 barsize 转成：
        #   (Timeframe, Compression) tuple which can be sorted
        def keyfn(x):
            n, t = x.split()
            tf, comp = self._sizes[t]
            return (tf, int(n) * comp)

        # 该工具 key 函数将 duration 转成：
        #   (Timeframe, Compression) tuple which can be sorted
        def key2fn(x):
            n, d = x.split()
            tf = self._dur2tf[d]
            return (tf, int(n))

        # 生成反向 duration 表
        self.revdur = collections.defaultdict(list)
        # 原表（dict）是 ONE to MANY 关系：
        #   duration -> barsizes
        # 这里反转为 ONE to MANY 关系：
        #   barsize -> durations
        for duration, barsizes in self._durations.items():
            for barsize in barsizes:
                self.revdur[keyfn(barsize)].append(duration)

        # 生成后按真实 duration 排序，而不是按文本形式排序
        for barsize in self.revdur:
            self.revdur[barsize].sort(key=key2fn)

    def start(self, data=None, broker=None):
        self.reconnect(fromstart=True)  # reconnect 应保持不变式

        # data 需要一些处理来启动数据接收
        if data is not None:
            self._env = data._env
            # 对 data 使用带 None 的模拟 queue 启动连接
            self.datas.append(data)

            # 如果连接失败，返回一个假注册，强制 data 尝试重连或退出
            return self.getTickerQueue(start=True)

        elif broker is not None:
            self.broker = broker

    def stop(self):
        try:
            self.conn.disconnect()  # disconnect 应保持不变式
        except AttributeError:
            pass    # conn 可能从未连接，因此没有 "disconnect"

        # 解除等待这些 event 的调用
        self._event_managed_accounts.set()
        self._event_accdownload.set()

    def logmsg(self, *args):
        # 用于 logging
        if self.p._debug:
            print(*args)

    def watcher(self, msg):
        # 请求 debug 时注册，用于观察所有 message
        self.logmsg(str(msg))
        if self.p.notifyall:
            self.notifs.put((msg, tuple(msg.values()), dict(msg.items())))

    def connected(self):
        # isConnected 通过 __getattr__ 间接提供，可能不存在。
        # 不存在表示尚未创建子属性 sender，即尚未建立连接，因此需要捕获 AttributeError。
        try:
            return self.conn.isConnected()
        except AttributeError:
            pass

        return False  # 未连接（包括未初始化）

    def reconnect(self, fromstart=False, resub=False):
        # 该方法必须保持不变式：同一来源可多次调用，结果必须一致。
        # 例如 5 个 data 同时接收并同时请求 reconnect。

        # 策略：
        #  - 如果 dontreconnect 已设置，则不再尝试连接
        #  - 检查连接；缺少 isConnected 表示首次连接（retries 也加 1）
        #  - 计算 retries（永久或有限次数）
        #  - 尝试连接
        #  - 如果成功且 fromstart 为 False，则重新启动 data 以重建 subscription
        firstconnect = False
        try:
            if self.conn.isConnected():
                if resub:
                    self.startdatas()
                return True  # 无需操作
        except AttributeError:
            # 未连接，需要通过多层 __getattr__ 间接访问 self.conn.sender.client.isConnected
            firstconnect = True

        if self.dontreconnect:
            return False

        # 该方法只由 data 在主线程中调用，因此无需加锁控制同步
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
                return True  # 连接成功

            if retries > 0:
                retries -= 1

        self.dontreconnect = True
        return False  # 连接/重连失败

    def startdatas(self):
        # 启动 data，直到全部完成后才返回
        ts = list()
        for data in self.datas:
            t = threading.Thread(target=data.reqdata)
            t.start()
            ts.append(t)

        for t in ts:
            t.join()

    def stopdatas(self):
        # 停止 subscription，并按 LIFO 顺序强制 data 退出循环
        qs = list(self.qs.values())
        ts = list()
        for data in self.datas:
            t = threading.Thread(target=data.canceldata)
            t.start()
            ts.append(t)

        for t in ts:
            t.join()

        for q in reversed(qs):  # datamaster 最后收到 None
            q.put(None)

    def get_notifications(self):
        '''返回待处理的 "store" 通知。'''
        # 后台线程可能持续添加 notification。None 标记用于识别本次要发送的最后一个 notification。
        self.notifs.put(None)  # 放置标记
        notifs = list()
        while True:
            notif = self.notifs.get()
            if notif is None:  # 到达标记
                break
            notifs.append(notif)

        return notifs

    @ibregister
    def error(self, msg):
        # 100-199 Order/Data/Historical related
        # 200-203 tickerId and Order Related
        # 300-399 A mix of things: orders, connectivity, tickers, misc errors
        # 400-449 Seem order related again
        # 500-531 Connectivity/Communication Errors
        # 10000-100027 Mix of special orders/routing
        # 1100-1102 TWS connectivy to the outside
        # 1300- Socket dropped in client-TWS communication
        # 2100-2110 Informative about Data Farm status (id=-1)

        # 所有 error 都记录到 environment（cerebro），因为 IB 的很多 error 实际上是信息性消息，
        # 且其中不少可能对用户有价值。
        if not self.p.notifyall:
            self.notifs.put((msg, tuple(msg.values()), dict(msg.items())))

        # 管理与连接相关的 event
        if msg.errorCode is None:
            # 通常在连接出错或即将断开前收到
            pass
        elif msg.errorCode in [200, 203, 162, 320, 321, 322]:
            # cdetails 200 security not found，通过对应 queue 通知
            # cdetails 203 security not allowed for acct
            try:
                q = self.qs[msg.id]
            except KeyError:
                pass  # 理论上不应发生，但可能发生
            else:
                self.cancelQueue(q, True)

        elif msg.errorCode in [354, 420]:
            # 354 no subscription，420 no real-time bar for contract。
            # 通知调用 data，让 data 知道不能 resub。
            try:
                q = self.qs[msg.id]
            except KeyError:
                pass  # 理论上不应发生，但可能发生
            else:
                q.put(-msg.errorCode)
                self.cancelQueue(q)

        elif msg.errorCode == 10225:
            # 10225-Bust event occurred，当前 subscription 已停用，需要立即重新订阅 real-time bars。
            try:
                q = self.qs[msg.id]
            except KeyError:
                pass  # 理论上不应发生，但可能发生
            else:
                q.put(-msg.errorCode)

        elif msg.errorCode == 326:  # 不可恢复，clientId 已被使用
            self.dontreconnect = True
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 502:
            # 无法连接 TWS：端口/配置未打开，或 TWS 关闭（随后可能出现 504）
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 504:  # data 操作时未连接
            # 每个 data 可能各出现一次
            pass  # 无需处理

        elif msg.errorCode == 1300:
            # TWS 已关闭。新连接端口包含在消息中
            # newport = int(msg.errorMsg.split('-')[-1])  # bla bla bla -7496
            self.conn.disconnect()
            self.stopdatas()

        elif msg.errorCode == 1100:
            # 连接丢失，通知 data；data 会在 queue 上等待但不会收到消息
            for q in self.ts:  # key: queue -> ticker
                q.put(-msg.errorCode)

        elif msg.errorCode == 1101:
            # 连接恢复，但 tickerId 已丢失
            for q in self.ts:  # key: queue -> ticker
                q.put(-msg.errorCode)

        elif msg.errorCode == 1102:
            # 连接恢复，tickerId 保持有效
            for q in self.ts:  # key: queue -> ticker
                q.put(-msg.errorCode)

        elif msg.errorCode < 500:
            # errorCode 类型很多，先假设它是 order error；若不是，后续检查会放过它
            if msg.id < self.REQIDBASE:
                if self.broker is not None:
                    self.broker.push_ordererror(msg)
            else:
                # 如果给出 "data" reqId error，则取消 queue，属于 sanity 处理
                q = self.qs[msg.id]
                self.cancelQueue(q, True)

    @ibregister
    def connectionClosed(self, msg):
        # 有时该事件不伴随 1300/502 或其他 error，因此需要独立处理
        self.conn.disconnect()
        self.stopdatas()

    @ibregister
    def managedAccounts(self, msg):
        # stream 中的第 1 条消息
        self.managed_accounts = msg.accountsList.split(',')
        self._event_managed_accounts.set()

        # 请求时间以避免同步问题
        self.reqCurrentTime()

    def reqCurrentTime(self):
        self.conn.reqCurrentTime()

    @ibregister
    def currentTime(self, msg):
        if not self.p.timeoffset:  # 仅在请求时应用 timeoffset
            return
        curtime = datetime.fromtimestamp(float(msg.time))
        with self._lock_tmoffset:
            self.tmoffset = curtime - datetime.now()

        threading.Timer(self.p.timerefresh, self.reqCurrentTime).start()

    def timeoffset(self):
        with self._lock_tmoffset:
            return self.tmoffset

    def nextTickerId(self):
        # 通过 itertools.count 获取下一个 ticker
        return next(self._tickerId)

    @ibregister
    def nextValidId(self, msg):
        # 从 TWS 通知值创建 counter，用于 order
        self.orderid = itertools.count(msg.orderId)

    def nextOrderId(self):
        # 从基于 TWS 通知值创建的 itertools.count 获取下一个 order id
        return next(self.orderid)

    def reuseQueue(self, tickerId):
        '''为 tickerId 复用 queue，并返回新的 tickerId 与 q。'''
        with self._lock_q:
            # 在 qs 中使 tickerId 失效（它是 key）
            q = self.qs.pop(tickerId, None)  # 使旧值失效
            iscash = self.iscash.pop(tickerId, None)

            # 更新 ts: q -> ticker
            tickerId = self.nextTickerId()  # 获取新的 tickerId
            self.ts[q] = tickerId  # 更新 ts: q -> tickerId
            self.qs[tickerId] = q  # 更新 qs: tickerId -> q
            self.iscash[tickerId] = iscash

        return tickerId, q

    def getTickerQueue(self, start=False):
        '''创建用于向 data feed 传递数据的 ticker/Queue。'''
        q = queue.Queue()
        if start:
            q.put(None)
            return q

        with self._lock_q:
            tickerId = self.nextTickerId()
            self.qs[tickerId] = q  # 可由其他线程管理
            self.ts[q] = tickerId
            self.iscash[tickerId] = False

        return tickerId, q

    def cancelQueue(self, q, sendnone=False):
        '''取消用于数据传递的 Queue。'''
        # pop ts（tickers），并用结果 pop qs（queues）
        tickerId = self.ts.pop(q, None)
        self.qs.pop(tickerId, None)

        self.iscash.pop(tickerId, None)

        if sendnone:
            q.put(None)

    def validQueue(self, q):
        '''返回 queue 是否仍然有效。'''
        return q in self.ts  # queue -> ticker

    def getContractDetails(self, contract, maxcount=None):
        cds = list()
        q = self.reqContractDetails(contract)
        while True:
            msg = q.get()
            if msg is None:
                break
            cds.append(msg)

        if not cds or (maxcount and len(cds) > maxcount):
            err = 'Ambiguous contract: none/multiple answers received'
            self.notifs.put((err, cds, {}))
            return None

        return cds

    def reqContractDetails(self, contract):
        # 获取 ticker/queue，用于识别和数据传递
        tickerId, q = self.getTickerQueue()
        self.conn.reqContractDetails(tickerId, contract)
        return q

    @ibregister
    def contractDetailsEnd(self, msg):
        '''标记 contractdetails 结束。'''
        self.cancelQueue(self.qs[msg.reqId], True)

    @ibregister
    def contractDetails(self, msg):
        '''接收响应并传入 queue。'''
        self.qs[msg.reqId].put(msg)

    def reqHistoricalDataEx(self, contract, enddate, begindate,
                            timeframe, compression,
                            what=None, useRTH=False, tz='', sessionend=None,
                            tickerId=None):
        '''
        raw reqHistoricalData proxy 的扩展版本，接收两个日期，而不是 duration、
        barsize 和 date。

        它使用 IB 发布的有效 duration/barsize 建立映射，并在需要时将一个 historical
        request 拆成多个 request。
        '''
        # 保留一份副本，用于 error reporting
        kwargs = locals().copy()
        kwargs.pop('self', None)  # 移除 self，无需报告

        if timeframe < TimeFrame.Seconds:
            # 不支持 ticks
            return self.getTickerQueue(start=True)

        if enddate is None:
            enddate = datetime.now()

        if begindate is None:
            duration = self.getmaxduration(timeframe, compression)
            if duration is None:
                err = ('No duration for historical data request for '
                       'timeframe/compresison')
                self.notifs.put((err, (), kwargs))
                return self.getTickerQueue(start=True)
            barsize = self.tfcomp_to_size(timeframe, compression)
            if barsize is None:
                err = ('No supported barsize for historical data request for '
                       'timeframe/compresison')
                self.notifs.put((err, (), kwargs))
                return self.getTickerQueue(start=True)

            return self.reqHistoricalData(contract=contract, enddate=enddate,
                                          duration=duration, barsize=barsize,
                                          what=what, useRTH=useRTH, tz=tz,
                                          sessionend=sessionend)

        # 检查请求的 timeframe/compression 是否被 IB 支持
        durations = self.getdurations(timeframe, compression)
        if not durations:  # 返回一个 queue，并放入 None
            return self.getTickerQueue(start=True)

        # 获取或复用 queue
        if tickerId is None:
            tickerId, q = self.getTickerQueue()
        else:
            tickerId, q = self.reuseQueue(tickerId)  # reuse q for old tickerId

        # 获取最佳 duration，以减少 request 数量
        duration = None
        for dur in durations:
            intdate = self.dt_plus_duration(begindate, dur)
            if intdate >= enddate:
                intdate = enddate
                duration = dur  # begin -> end 可放入单个 request
                break

        if duration is None:  # 没有足够大的 duration 覆盖 request
            duration = durations[-1]

            # 保存计算出的数据
            self.histexreq[tickerId] = dict(
                contract=contract, enddate=enddate, begindate=intdate,
                timeframe=timeframe, compression=compression,
                what=what, useRTH=useRTH, tz=tz, sessionend=sessionend)

        barsize = self.tfcomp_to_size(timeframe, compression)
        self.histfmt[tickerId] = timeframe >= TimeFrame.Days
        self.histsend[tickerId] = sessionend
        self.histtz[tickerId] = tz

        if contract.m_secType in ['CASH', 'CFD']:
            self.iscash[tickerId] = 1  # msg.field code
            if not what:
                what = 'BID'  # cash 默认值，除非另行指定

        elif contract.m_secType in ['IND'] and self.p.indcash:
            self.iscash[tickerId] = 4  # msg.field code

        what = what or 'TRADES'

        self.conn.reqHistoricalData(
            tickerId,
            contract,
            bytes(intdate.strftime('%Y%m%d %H:%M:%S') + ' GMT'),
            bytes(duration),
            bytes(barsize),
            bytes(what),
            int(useRTH),
            2)  # dateformat 1 表示 string，2 表示 unix time seconds

        return q

    def reqHistoricalData(self, contract, enddate, duration, barsize,
                          what=None, useRTH=False, tz='', sessionend=None):
        '''reqHistoricalData 的 proxy。'''

        # 获取 ticker/queue，用于识别和数据传递
        tickerId, q = self.getTickerQueue()

        if contract.m_secType in ['CASH', 'CFD']:
            self.iscash[tickerId] = True
            if not what:
                what = 'BID'  # TRADES 不可用
            elif what == 'ASK':
                self.iscash[tickerId] = 2
        else:
            what = what or 'TRADES'

        # 拆分 barsize "x time"，在 sizes 中查找 (tf, comp) 并得到 tf
        tframe = self._sizes[barsize.split()[1]][0]
        self.histfmt[tickerId] = tframe >= TimeFrame.Days
        self.histsend[tickerId] = sessionend
        self.histtz[tickerId] = tz

        self.conn.reqHistoricalData(
            tickerId,
            contract,
            bytes(enddate.strftime('%Y%m%d %H:%M:%S') + ' GMT'),
            bytes(duration),
            bytes(barsize),
            bytes(what),
            int(useRTH),
            2)

        return q

    def cancelHistoricalData(self, q):
        '''取消已有 HistoricalData request。

        Args:
            q: reqMktData 返回的 Queue。
        '''
        with self._lock_q:
            self.conn.cancelHistoricalData(self.ts[q])
            self.cancelQueue(q, True)

    def reqRealTimeBars(self, contract, useRTH=False, duration=5):
        '''创建（5 秒）Real Time Bars request。

        Args:
            contract: ib.ext.Contract.Contract 实例。
            useRTH: 传给 TWS。
            duration: 传给 TWS；2016 年只有 5 可用。

        Returns:
            Queue: 客户端可等待该 queue 接收 RTVolume 实例。
        '''
        # 获取 ticker/queue，用于识别和数据传递
        tickerId, q = self.getTickerQueue()

        # 2015-09-29：duration 只支持 5 秒
        self.conn.reqRealTimeBars(
            tickerId,
            contract,
            duration,
            bytes('TRADES'),
            int(useRTH))

        return q

    def cancelRealTimeBars(self, q):
        '''取消已有 MarketData subscription。

        Args:
            q: reqMktData 返回的 Queue。
        '''
        with self._lock_q:
            tickerId = self.ts.get(q, None)
            if tickerId is not None:
                self.conn.cancelRealTimeBars(tickerId)

            self.cancelQueue(q, True)

    def reqMktData(self, contract, what=None):
        '''创建 MarketData subscription。

        Args:
            contract: ib.ext.Contract.Contract 实例。

        Returns:
            Queue: 客户端可等待该 queue 接收 RTVolume 实例。
        '''
        # 获取 ticker/queue，用于识别和数据传递
        tickerId, q = self.getTickerQueue()
        ticks = '233'  # 请求通过 tickString 传递的 RTVOLUME tick

        if contract.m_secType in ['CASH', 'CFD']:
            self.iscash[tickerId] = True
            ticks = ''  # cash market 不接收 RTVOLUME
            if what == 'ASK':
                self.iscash[tickerId] = 2

        # q.put(None)  # 用于启动 backfilling
        # cash 也可请求 233，但不会收到任何内容
        self.conn.reqMktData(tickerId, contract, bytes(ticks), False)
        return q

    def cancelMktData(self, q):
        '''取消已有 MarketData subscription。

        Args:
            q: reqMktData 返回的 Queue。
        '''
        with self._lock_q:
            tickerId = self.ts.get(q, None)
            if tickerId is not None:
                self.conn.cancelMktData(tickerId)

            self.cancelQueue(q, True)

    @ibregister
    def tickString(self, msg):
        # 接收并处理 tickString message
        if msg.tickType == 48:  # RTVolume
            try:
                rtvol = RTVolume(msg.value)
            except ValueError:  # price not in message ...
                pass
            else:
                # 无需调整时间，因为 message 中已经是 timestamp 形式
                self.qs[msg.tickerId].put(rtvol)

    @ibregister
    def tickPrice(self, msg):
        '''Cash Market 没有 "last_price"/"last_size" 概念，价格跟踪按 BID price 进行。

        为保持跨市场 interface 一致，会将只包含 price 的 RTVolume 放入客户端 queue。
        '''
        # 用于 "CASH" market
        # 曾观察到即便 "field" 为 1，price 字段也可能缺失
        tickerId = msg.tickerId
        fieldcode = self.iscash[tickerId]
        if fieldcode:
            if msg.field == fieldcode:  # Expected cash field code
                try:
                    if msg.price == -1.0:
                        # 似乎表示 stream 暂停，例如 FOREX 在 CET 23:00 - 23:15 之间
                        return
                except AttributeError:
                    pass

                try:
                    rtvol = RTVolume(price=msg.price, tmoffset=self.tmoffset)
                    # print('rtvol with datetime:', rtvol.datetime)
                except ValueError:  # price not in message ...
                    pass
                else:
                    self.qs[tickerId].put(rtvol)

    @ibregister
    def realtimeBar(self, msg):
        '''接收 x 秒 Real Time Bars（编写时仅支持 5 秒）。

        不适用于 cash market。
        '''
        # 获取 naive localtime 对象
        msg.time = datetime.utcfromtimestamp(float(msg.time))
        self.qs[msg.reqId].put(msg)

    @ibregister
    def historicalData(self, msg):
        '''接收 historical data request 的 event。'''
        # 对多层下载，需要将 queue 重新绑定到新的 tickerId（以防 tickerId 不可复用），
        # 并发起新的 reqHistData，而不是放入 None。
        tickerId = msg.reqId
        q = self.qs[tickerId]
        if msg.date.startswith('finished-'):
            self.histfmt.pop(tickerId, None)
            self.histsend.pop(tickerId, None)
            self.histtz.pop(tickerId, None)
            kargs = self.histexreq.pop(tickerId, None)
            if kargs is not None:
                self.reqHistoricalDataEx(tickerId=tickerId, **kargs)
                return

            msg.date = None
            self.cancelQueue(q)
        else:
            dtstr = msg.date  # Format when string req: YYYYMMDD[  HH:MM:SS]
            if self.histfmt[tickerId]:
                sessionend = self.histsend[tickerId]
                dt = datetime.strptime(dtstr, '%Y%m%d')
                dteos = datetime.combine(dt, sessionend)
                tz = self.histtz[tickerId]
                if tz:
                    dteostz = tz.localize(dteos)
                    dteosutc = dteostz.astimezone(UTC).replace(tzinfo=None)
                    # 例如请求 daily bars 时，当前日会带着已发生数据返回。
                    # 如果加入 session end，新 tick 因发生在结束时间之前而无法通过。
                else:
                    dteosutc = dteos

                if dteosutc <= datetime.utcnow():
                    dt = dteosutc

                msg.date = dt
            else:
                msg.date = datetime.utcfromtimestamp(long(dtstr))

        q.put(msg)

    # _durations 用于计算连接启动或连接丢失后 backfilling 所需的 historical data。
    # 使用 timedelta 作为 key，可快速找出可用 bar size。

    _durations = dict([
        # 60 seconds - 1 min
        ('60 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min')),

        # 120 seconds - 2 mins
        ('120 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins')),

        # 180 seconds - 3 mins
        ('180 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins')),

        # 300 seconds - 5 mins
        ('300 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins')),

        # 600 seconds - 10 mins
        ('600 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins')),

        # 900 seconds - 15 mins
        ('900 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins')),

        # 1200 seconds - 20 mins
        ('1200 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins')),

        # 1800 seconds - 30 mins
        ('1800 S',
         ('1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins')),

        # 3600 seconds - 1 hour
        ('3600 S',
         ('5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour')),

        # 7200 seconds - 2 hours
        ('7200 S',
         ('5 secs', '10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour', '2 hours')),

        # 10800 seconds - 3 hours
        ('10800 S',
         ('10 secs', '15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours')),

        # 14400 seconds - 4 hours
        ('14400 S',
         ('15 secs', '30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours')),

        # 28800 seconds - 8 hours
        ('28800 S',
         ('30 secs',
          '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours', '8 hours')),

        # 1 days
        ('1 D',
         ('1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
          '1 day')),

        # 2 days
        ('2 D',
         ('2 mins', '3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
          '1 day')),

        # 1 weeks
        ('1 W',
         ('3 mins', '5 mins', '10 mins', '15 mins',
          '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
          '1 day', '1 W')),

        # 2 weeks
        ('2 W',
         ('15 mins', '20 mins', '30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
          '1 day', '1 W')),

        # 1 months
        ('1 M',
         ('30 mins',
          '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
          '1 day', '1 W', '1 M')),

        # 2+ months
        ('2 M', ('1 day', '1 W', '1 M')),
        ('3 M', ('1 day', '1 W', '1 M')),
        ('4 M', ('1 day', '1 W', '1 M')),
        ('5 M', ('1 day', '1 W', '1 M')),
        ('6 M', ('1 day', '1 W', '1 M')),
        ('7 M', ('1 day', '1 W', '1 M')),
        ('8 M', ('1 day', '1 W', '1 M')),
        ('9 M', ('1 day', '1 W', '1 M')),
        ('10 M', ('1 day', '1 W', '1 M')),
        ('11 M', ('1 day', '1 W', '1 M')),

        # 1+ years
        ('1 Y',  ('1 day', '1 W', '1 M')),
    ])

    # Sizes 用于将上方 bar size 快速转换到实际 timeframe，以便与实际 data 对比
    _sizes = {
        'secs': (TimeFrame.Seconds, 1),
        'min': (TimeFrame.Minutes, 1),
        'mins': (TimeFrame.Minutes, 1),
        'hour': (TimeFrame.Minutes, 60),
        'hours': (TimeFrame.Minutes, 60),
        'day': (TimeFrame.Days, 1),
        'W': (TimeFrame.Weeks, 1),
        'M': (TimeFrame.Months, 1),
    }

    _dur2tf = {
        'S': TimeFrame.Seconds,
        'D': TimeFrame.Days,
        'W': TimeFrame.Weeks,
        'M': TimeFrame.Months,
        'Y': TimeFrame.Years,
    }

    def getdurations(self,  timeframe, compression):
        key = (timeframe, compression)
        if key not in self.revdur:
            return []

        return self.revdur[key]

    def getmaxduration(self, timeframe, compression):
        key = (timeframe, compression)
        try:
            return self.revdur[key][-1]
        except (KeyError, IndexError):
            pass

        return None

    def tfcomp_to_size(self, timeframe, compression):
        if timeframe == TimeFrame.Months:
            return '{} M'.format(compression)

        if timeframe == TimeFrame.Weeks:
            return '{} W'.format(compression)

        if timeframe == TimeFrame.Days:
            if not compression % 7:
                return '{} W'.format(compression // 7)

            return '{} day'.format(compression)

        if timeframe == TimeFrame.Minutes:
            if not compression % 60:
                hours = compression // 60
                return ('{} hour'.format(hours)) + ('s' * (hours > 1))

            return ('{} min'.format(compression)) + ('s' * (compression > 1))

        if timeframe == TimeFrame.Seconds:
            return '{} secs'.format(compression)

        # Microseconds 或 ticks
        return None

    def dt_plus_duration(self, dt, duration):
        size, dim = duration.split()
        size = int(size)
        if dim == 'S':
            return dt + timedelta(seconds=size)

        if dim == 'D':
            return dt + timedelta(days=size)

        if dim == 'W':
            return dt + timedelta(days=size * 7)

        if dim == 'M':
            month = dt.month - 1 + size  # -1 to make it 0 based, readd below
            years, month = divmod(month, 12)
            return dt.replace(year=dt.year + years, month=month + 1)

        if dim == 'Y':
            return dt.replace(year=dt.year + size)

        return dt  # could do nothing with it ... return it intact

    def calcdurations(self, dtbegin, dtend):
        '''计算两个 datetime 之间的 duration。'''
        duration = self.histduration(dtbegin, dtend)

        if duration[-1] == 'M':
            m = int(duration.split()[0])
            m1 = min(2, m)  # (2, 1) -> 1, (2, 7) -> 2. Bottomline: 1 or 2
            m2 = max(1, m1)  # m1 can only be 1 or 2
            checkdur = '{} M'.format(m2)
        elif duration[-1] == 'Y':
            checkdur = '1 Y'
        else:
            checkdur = duration

        sizes = self._durations[checkduration]
        return duration, sizes

    def calcduration(self, dtbegin, dtend):
        '''计算两个 datetime 之间的 duration，并返回单个 size。'''
        duration, sizes = self._calcdurations(dtbegin, dtend)
        return duration, sizes[0]

    def histduration(self, dt1, dt2):
        # 给定两个日期，根据 IB Historical Data API 限制表计算最小可用 duration
        #
        # Seconds: 'x S' (x: [60, 120, 180, 300, 600, 900, 1200, 1800, 3600,
        #                     7200, 10800, 14400, 28800])
        # Days: 'x D' (x: [1, 2]
        # Weeks: 'x W' (x: [1, 2])
        # Months: 'x M' (x: [1, 11])
        # Years: 'x Y' (x: [1])

        td = dt2 - dt1  # 获取 timedelta 用于计算

        # 第一阶段：seconds 数组
        tsecs = td.total_seconds()
        secs = [60, 120, 180, 300, 600, 900, 1200, 1800, 3600, 7200, 10800,
                14400, 28800]

        idxsec = bisect.bisect_left(secs, tsecs)
        if idxsec < len(secs):
            return '{} S'.format(secs[idxsec])

        tdextra = bool(td.seconds or td.microseconds)  # over days/weeks

        # 下一阶段：1 或 2 天
        days = td.days + tdextra
        if td.days <= 2:
            return '{} D'.format(days)

        # 下一阶段：1 或 2 周
        weeks, d = divmod(td.days, 7)
        weeks += bool(d or tdextra)
        if weeks <= 2:
            return '{} W'.format(weeks)

        # 获取 dt 组件引用
        y2, m2, d2 = dt2.year, dt2.month, dt2.day
        y1, m1, d1 = dt1.year, dt1.month, dt2.day

        H2, M2, S2, US2 = dt2.hour, dt2.minute, dt2.second, dt2.microsecond
        H1, M1, S1, US1 = dt1.hour, dt1.minute, dt1.second, dt1.microsecond

        # 下一阶段：1 -> 11 个月（含 11）
        months = (y2 * 12 + m2) - (y1 * 12 + m1) + (
            (d2, H2, M2, S2, US2) > (d1, H1, M1, S1, US1))
        if months <= 1:  # months <= 11
            return '1 M'  # return '{} M'.format(months)
        elif months <= 11:
            return '2 M'  # cap at 2 months to keep the table clean

        # 下一阶段：years
        # y = y2 - y1 + (m2, d2, H2, M2, S2, US2) > (m1, d1, H1, M1, S1, US1)
        # return '{} Y'.format(y)

        return '1 Y'  # 保持表简洁

    def makecontract(self, symbol, sectype, exch, curr,
                     expiry='', strike=0.0, right='', mult=1):
        '''不做检查，直接根据参数返回 contract。'''

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
        '''cancelOrder 的 proxy。'''
        self.conn.cancelOrder(orderid)

    def placeOrder(self, orderid, contract, order):
        '''placeOrder 的 proxy。'''
        self.conn.placeOrder(orderid, contract, order)

    @ibregister
    def openOrder(self, msg):
        '''接收 ``openOrder`` event。'''
        self.broker.push_orderstate(msg)

    @ibregister
    def execDetails(self, msg):
        '''接收 execDetails。'''
        self.broker.push_execution(msg.execution)

    @ibregister
    def orderStatus(self, msg):
        '''接收 ``orderStatus`` event。'''
        self.broker.push_orderstatus(msg)

    @ibregister
    def commissionReport(self, msg):
        '''接收 commissionReport event。'''
        self.broker.push_commissionreport(msg.commissionReport)

    def reqPositions(self):
        '''reqPositions 的 proxy。'''
        self.conn.reqPositions()

    @ibregister
    def position(self, msg):
        '''接收 positions event。'''
        pass  # Not implemented yet

    def reqAccountUpdates(self, subscribe=True, account=None):
        '''reqAccountUpdates 的 proxy。

        如果 ``account`` 为 ``None``，会等待 ``managedAccounts`` message 设置 account code。
        '''
        if account is None:
            self._event_managed_accounts.wait()
            account = self.managed_accounts[0]

        self.conn.reqAccountUpdates(subscribe, bytes(account))

    @ibregister
    def accountDownloadEnd(self, msg):
        # 标记 account update 结束。
        # 该 event 表示下载已结束。它只会 false 一次，可用于判断是否至少下载过一次。
        self._event_accdownload.set()
        if False:
            if self.port_update:
                self.broker.push_portupdate()

                self.port_update = False

    @ibregister
    def updatePortfolio(self, msg):
        # 锁定 position dict 访问。该方法在子线程中调用，可能随时触发。
        with self._lock_pos:
            if not self._event_accdownload.is_set():  # 1st event seen
                position = Position(msg.position, msg.averageCost)
                self.positions[msg.contract.m_conId] = position
            else:
                position = self.positions[msg.contract.m_conId]
                if not position.fix(msg.position, msg.averageCost):
                    err = ('The current calculated position and '
                           'the position reported by the broker do not match. '
                           'Operation can continue, but the trades '
                           'calculated in the strategy may be wrong')

                    self.notifs.put((err, (), {}))

                # 在 account download 结束时标记发送给 broker 的 signal
                # self.port_update = True
                self.broker.push_portupdate()

    def getposition(self, contract, clone=False):
        # 锁定 position dict 访问。该方法由主线程调用，同时后台可能有更新。
        with self._lock_pos:
            position = self.positions[contract.m_conId]
            if clone:
                return copy(position)

            return position

    @ibregister
    def updateAccountValue(self, msg):
        # 锁定 value 更新 dict。该方法在子线程中调用，可能随时触发。
        with self._lock_accupd:
            try:
                value = float(msg.value)
            except ValueError:
                value = msg.value

            self.acc_upds[msg.accountName][msg.key][msg.currency] = value

            if msg.key == 'NetLiquidation':
                # NetLiquidationByCurrency 且 currency == 'BASE' 时含义相同
                self.acc_value[msg.accountName] = value
            elif msg.key == 'TotalCashBalance' and msg.currency == 'BASE':
                self.acc_cash[msg.accountName] = value

    def get_acc_values(self, account=None):
        '''返回 TWS 在常规更新中发送的所有 account value 信息。

        至少等待 1 次成功下载。

        如果 ``account`` 为 ``None``，返回以 account 为 key 的所有 account 字典。
        如果指定 account，或系统只有 1 个 account，则返回该 account 对应的字典。
        '''
        # 至少等待 1 次 account update download 完成后，再向调用方返回 account 信息
        if self.connected():
            self._event_accdownload.wait()
        # 锁定 acc_cash 访问，避免 event 干扰
        with self._updacclock:
            if account is None:
                # 等待 managedAccount message
                if self.connected():
                    self._event_managed_accounts.wait()

                if not self.managed_accounts:
                    return self.acc_upds.copy()

                elif len(self.managed_accounts) > 1:
                    return self.acc_upds.copy()

                # 只有 1 个 account，继续向下返回单个 account
                account = self.managed_accounts[0]

            try:
                return self.acc_upds[account].copy()
            except KeyError:
                pass

            return self.acc_upds.copy()

    def get_acc_value(self, account=None):
        '''返回 TWS 在常规更新中发送的 net liquidation value。

        至少等待 1 次成功下载。

        如果 ``account`` 为 ``None``，多 account 时返回总和；如果指定 account，
        或系统只有 1 个 account，则返回该 account 对应值。
        '''
        # 至少等待 1 次 account update download 完成后，再向调用方返回 value
        if self.connected():
            self._event_accdownload.wait()
        # 锁定 acc_cash 访问，避免 event 干扰
        with self._lock_accupd:
            if account is None:
                # 等待 managedAccount message
                if self.connected():
                    self._event_managed_accounts.wait()

                if not self.managed_accounts:
                    return float()

                elif len(self.managed_accounts) > 1:
                    return sum(self.acc_value.values())

                # 只有 1 个 account，继续向下返回单个 account
                account = self.managed_accounts[0]

            try:
                return self.acc_value[account]
            except KeyError:
                pass

            return float()

    def get_acc_cash(self, account=None):
        '''返回 TWS 在常规更新中发送的 total cash value。

        至少等待 1 次成功下载。

        如果 ``account`` 为 ``None``，多 account 时返回总和；如果指定 account，
        或系统只有 1 个 account，则返回该 account 对应值。
        '''
        # 至少等待 1 次 account update download 完成后，再向调用方返回 cash
        if self.connected():
            self._event_accdownload.wait()
        # 锁定 acc_cash 访问，避免 event 干扰
        with self._lock_accupd:
            if account is None:
                # 等待 managedAccount message
                if self.connected():
                    self._event_managed_accounts.wait()

                if not self.managed_accounts:
                    return float()

                elif len(self.managed_accounts) > 1:
                    return sum(self.acc_cash.values())

                # 只有 1 个 account，继续向下返回单个 account
                account = self.managed_accounts[0]

            try:
                return self.acc_cash[account]
            except KeyError:
                pass
