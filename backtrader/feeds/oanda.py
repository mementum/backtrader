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

from datetime import datetime, timedelta

from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num, num2date
from backtrader.utils.py3 import (integer_types, queue, string_types,
                                  with_metaclass)
from backtrader.metabase import MetaParams
from backtrader.stores import oandastore


class MetaOandaData(DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，随后把它注册到对应 store。'''
        # 初始化类对象
        super(MetaOandaData, cls).__init__(name, bases, dct)

        # 注册到 store，供 OandaStore 找到实际 DataCls
        oandastore.OandaStore.DataCls = cls


class OandaData(with_metaclass(MetaOandaData, DataBase)):
    '''Oanda 数据源。

    Args:
        dataname: Oanda instrument 名称，例如 ``EUR_USD``。
        qcheck: 没有收到数据时的唤醒间隔（秒），用于给 resample/replay 和 notification
            传播留出处理机会。
        historical: 为 ``True`` 时，完成首次历史数据下载后停止。会使用标准 data feed
            参数 ``fromdate`` 和 ``todate`` 作为时间范围。
        backfill_start: 启动时是否执行 backfill。会在单次请求中尽可能获取最大历史数据。
        backfill: 断线/重连后是否执行 backfill。会按缺口时长下载尽量小的数据范围。
        backfill_from: 额外的初始 backfill 数据源。该数据源耗尽后，如有需要，再从
            Oanda 拉取 backfill 数据。
        bidask: 历史/backfill 请求是否向服务器请求 bid/ask 价格；为 ``False`` 时请求
            midpoint。
        useask: 使用 bid/ask 数据时，是否使用 ask 侧价格；默认使用 bid。
        includeFirst: 直接传给 Oanda API，控制历史/backfill 请求的第一个 bar 是否返回。
        reconnect: 网络断开时是否重连。
        reconnections: 最大重连次数，``-1`` 表示无限重连。
        reconntimeout: 两次重连尝试之间等待的秒数。

    Returns:
        OandaData: 可加入 Cerebro 的 Oanda 数据源实例。

    支持的 ``timeframe`` / ``compression`` 组合如下，需符合 OANDA API Developer's
    Guide 的 granularity 定义::

        (TimeFrame.Seconds, 5): 'S5',
        (TimeFrame.Seconds, 10): 'S10',
        (TimeFrame.Seconds, 15): 'S15',
        (TimeFrame.Seconds, 30): 'S30',
        (TimeFrame.Minutes, 1): 'M1',
        (TimeFrame.Minutes, 2): 'M3',
        (TimeFrame.Minutes, 3): 'M3',
        (TimeFrame.Minutes, 4): 'M4',
        (TimeFrame.Minutes, 5): 'M5',
        (TimeFrame.Minutes, 10): 'M10',
        (TimeFrame.Minutes, 15): 'M15',
        (TimeFrame.Minutes, 30): 'M30',
        (TimeFrame.Minutes, 60): 'H1',
        (TimeFrame.Minutes, 120): 'H2',
        (TimeFrame.Minutes, 180): 'H3',
        (TimeFrame.Minutes, 240): 'H4',
        (TimeFrame.Minutes, 360): 'H6',
        (TimeFrame.Minutes, 480): 'H8',
        (TimeFrame.Days, 1): 'D',
        (TimeFrame.Weeks, 1): 'W',
        (TimeFrame.Months, 1): 'M',

    其他组合会被拒绝。

    ---
    交互界面使用示范:

    >>> data = OandaData(dataname='EUR_USD')  # doctest: +SKIP
    >>> data.p.dataname  # doctest: +SKIP
    'EUR_USD'
    '''
    params = (
        ('qcheck', 0.5),
        ('historical', False),  # 仅下载历史数据
        ('backfill_start', True),  # 启动时执行 backfill
        ('backfill', True),  # 重连时执行 backfill
        ('backfill_from', None),  # 用于 backfill 的额外数据源
        ('bidask', True),
        ('useask', False),
        ('includeFirst', True),
        ('reconnect', True),
        ('reconnections', -1),  # 无限重连
        ('reconntimeout', 5.0),
    )

    _store = oandastore.OandaStore

    # _load 中有限状态机的状态
    _ST_FROM, _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(5)

    _TOFFSET = timedelta()

    def _timeoffset(self):
        # 用于弥补未发送 notification 的时间偏移
        return self._TOFFSET

    def islive(self):
        '''返回 ``True``，通知 ``Cerebro`` 关闭 preload 和 runonce。'''
        return True

    def __init__(self, **kwargs):
        self.o = self._store(**kwargs)
        self._candleFormat = 'bidask' if self.p.bidask else 'midpoint'

    def setenvironment(self, env):
        '''接收 Cerebro 环境，并把它传给所属 store。'''
        super(OandaData, self).setenvironment(env)
        env.addstore(self.o)

    def start(self):
        '''启动 Oanda 连接，并在存在时获取真实 instrument 信息。'''
        super(OandaData, self).start()

        # 尽早创建运行期属性
        self._statelivereconn = False  # 是否在 live 状态下重连
        self._storedmsg = dict()  # 保存待处理的 live 消息（键为 None）
        self.qlive = queue.Queue()
        self._state = self._ST_OVER

        # 启动 store，并获取后续等待的数据队列
        self.o.start(data=self)

        # 检查 granularity 是否支持
        otf = self.o.get_granularity(self._timeframe, self._compression)
        if otf is None:
            self.put_notification(self.NOTSUPPORTED_TF)
            self._state = self._ST_OVER
            return

        self.contractdetails = cd = self.o.get_instrument(self.p.dataname)
        if cd is None:
            self.put_notification(self.NOTSUBSCRIBED)
            self._state = self._ST_OVER
            return

        if self.p.backfill_from is not None:
            self._state = self._ST_FROM
            self.p.backfill_from._start()
        else:
            self._start_finish()
            self._state = self._ST_START  # _load 的初始状态
            self._st_start()

        self._reconns = 0

    def _st_start(self, instart=True, tmout=None):
        if self.p.historical:
            self.put_notification(self.DELAYED)
            dtend = None
            if self.todate < float('inf'):
                dtend = num2date(self.todate)

            dtbegin = None
            if self.fromdate > float('-inf'):
                dtbegin = num2date(self.fromdate)

            self.qhist = self.o.candles(
                self.p.dataname, dtbegin, dtend,
                self._timeframe, self._compression,
                candleFormat=self._candleFormat,
                includeFirst=self.p.includeFirst)

            self._state = self._ST_HISTORBACK
            return True

        self.qlive = self.o.streaming_prices(self.p.dataname, tmout=tmout)
        if instart:
            self._statelivereconn = self.p.backfill_start
        else:
            self._statelivereconn = self.p.backfill

        if self._statelivereconn:
            self.put_notification(self.DELAYED)

        self._state = self._ST_LIVE
        if instart:
            self._reconns = self.p.reconnections

        return True  # 前面没有返回时，隐式继续

    def stop(self):
        '''停止数据源，并通知 store 停止。'''
        super(OandaData, self).stop()
        self.o.stop()

    def haslivedata(self):
        return bool(self._storedmsg or self.qlive)  # 不直接返回对象本身

    def _load(self):
        if self._state == self._ST_OVER:
            return False

        while True:
            if self._state == self._ST_LIVE:
                try:
                    msg = (self._storedmsg.pop(None, None) or
                           self.qlive.get(timeout=self._qcheck))
                except queue.Empty:
                    return None  # 表示超时

                if msg is None:  # historical/backfill 期间连接断开
                    self.put_notification(self.CONNBROKEN)
                    # 尝试重连
                    if not self.p.reconnect or self._reconns == 0:
                        # 已无法继续重连
                        self.put_notification(self.DISCONNECTED)
                        self._state = self._ST_OVER
                        return False  # 失败

                    self._reconns -= 1
                    self._st_start(instart=False, tmout=self.p.reconntimeout)
                    continue

                if 'code' in msg:
                    self.put_notification(self.CONNBROKEN)
                    code = msg['code']
                    if code not in [599, 598, 596]:
                        self.put_notification(self.DISCONNECTED)
                        self._state = self._ST_OVER
                        return False  # 失败

                    if not self.p.reconnect or self._reconns == 0:
                        # 已无法继续重连
                        self.put_notification(self.DISCONNECTED)
                        self._state = self._ST_OVER
                        return False  # 失败

                    # 可以继续重连
                    self._reconns -= 1
                    self._st_start(instart=False, tmout=self.p.reconntimeout)
                    continue

                self._reconns = self.p.reconnections

                # 按预期返回类型处理消息
                if not self._statelivereconn:
                    if self._laststatus != self.LIVE:
                        if self.qlive.qsize() <= 1:  # live 队列很短
                            self.put_notification(self.LIVE)

                    ret = self._load_tick(msg)
                    if ret:
                        return True

                    # 当前消息无法形成 bar，继续取下一条
                    continue

                # 进入重连处理流程，尝试 backfill
                self._storedmsg[None] = msg  # 保存当前消息

                # 否则执行 backfill
                if self._laststatus != self.DELAYED:
                    self.put_notification(self.DELAYED)

                dtend = None
                if len(self) > 1:
                    # len == 1 表示第一次转发
                    dtbegin = self.datetime.datetime(-1)
                elif self.fromdate > float('-inf'):
                    dtbegin = num2date(self.fromdate)
                else:  # 1st bar and no begin set
                    # 传 None 表示单次请求尽可能获取最大范围
                    dtbegin = None

                dtend = datetime.utcfromtimestamp(int(msg['time']) / 10 ** 6)

                self.qhist = self.o.candles(
                    self.p.dataname, dtbegin, dtend,
                    self._timeframe, self._compression,
                    candleFormat=self._candleFormat,
                    includeFirst=self.p.includeFirst)

                self._state = self._ST_HISTORBACK
                self._statelivereconn = False  # 不再处于 live 重连状态
                continue

            elif self._state == self._ST_HISTORBACK:
                msg = self.qhist.get()
                if msg is None:  # historical/backfill 期间连接断开
                    # 未处理该情况，直接退出
                    self.put_notification(self.DISCONNECTED)
                    self._state = self._ST_OVER
                    return False  # 错误处理取消了队列

                elif 'code' in msg:  # 错误
                    self.put_notification(self.NOTSUBSCRIBED)
                    self.put_notification(self.DISCONNECTED)
                    self._state = self._ST_OVER
                    return False

                if msg:
                    if self._load_history(msg):
                        return True  # 加载成功

                    continue  # 未加载，日期可能已经见过
                else:
                    # 历史数据结束
                    if self.p.historical:  # 仅历史模式
                        self.put_notification(self.DISCONNECTED)
                        self._state = self._ST_OVER
                        return False  # 历史数据结束

                # 还需要进入 live 模式
                self._state = self._ST_LIVE
                continue

            elif self._state == self._ST_FROM:
                if not self.p.backfill_from.next():
                    # 额外 backfill 数据源已经耗尽
                    self._state = self._ST_START
                    continue

                # 复制同名 line
                for alias in self.lines.getlinealiases():
                    lsrc = getattr(self.p.backfill_from.lines, alias)
                    ldst = getattr(self.lines, alias)

                    ldst[0] = lsrc[0]

                return True

            elif self._state == self._ST_START:
                if not self._st_start(instart=False):
                    self._state = self._ST_OVER
                    return False

    def _load_tick(self, msg):
        dtobj = datetime.utcfromtimestamp(int(msg['time']) / 10 ** 6)
        dt = date2num(dtobj)
        if dt <= self.lines.datetime[-1]:
            return False  # 时间已经处理过

        # 通用字段
        self.lines.datetime[0] = dt
        self.lines.volume[0] = 0.0
        self.lines.openinterest[0] = 0.0

        # 把价格写入 bar
        tick = float(msg['ask']) if self.p.useask else float(msg['bid'])
        self.lines.open[0] = tick
        self.lines.high[0] = tick
        self.lines.low[0] = tick
        self.lines.close[0] = tick
        self.lines.volume[0] = 0.0
        self.lines.openinterest[0] = 0.0

        return True

    def _load_history(self, msg):
        dtobj = datetime.utcfromtimestamp(int(msg['time']) / 10 ** 6)
        dt = date2num(dtobj)
        if dt <= self.lines.datetime[-1]:
            return False  # 时间已经处理过

        # 通用字段
        self.lines.datetime[0] = dt
        self.lines.volume[0] = float(msg['volume'])
        self.lines.openinterest[0] = 0.0

        # 把价格写入 bar
        if self.p.bidask:
            if not self.p.useask:
                self.lines.open[0] = float(msg['openBid'])
                self.lines.high[0] = float(msg['highBid'])
                self.lines.low[0] = float(msg['lowBid'])
                self.lines.close[0] = float(msg['closeBid'])
            else:
                self.lines.open[0] = float(msg['openAsk'])
                self.lines.high[0] = float(msg['highAsk'])
                self.lines.low[0] = float(msg['lowAsk'])
                self.lines.close[0] = float(msg['closeAsk'])
        else:
            self.lines.open[0] = float(msg['openMid'])
            self.lines.high[0] = float(msg['highMid'])
            self.lines.low[0] = float(msg['lowMid'])
            self.lines.close[0] = float(msg['closeMid'])

        return True
