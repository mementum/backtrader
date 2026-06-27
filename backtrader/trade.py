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

import itertools

from .utils import AutoOrderedDict
from .utils.date import num2date
from .utils.py3 import range


class TradeHistory(AutoOrderedDict):
    '''表示 Trade 每次 update 后的状态和事件信息。

    该对象是一个支持 ``.`` 访问语法的 dictionary。

    Attributes:
      - ``status`` (支持 ``.`` 访问的 ``dict``): 保存 update 事件后的状态，
        包含以下子属性

        - ``status`` (``int``): Trade status
        - ``dt`` (``float``): float 编码的 datetime
        - ``barlen`` (``int``): trade 已活跃的 bar 数量
        - ``size`` (``int``): Trade 当前 size
        - ``price`` (``float``): Trade 当前 price
        - ``value`` (``float``): Trade 当前货币 value
        - ``pnl`` (``float``): Trade 当前 profit and loss
        - ``pnlcomm`` (``float``): 扣除 commission 后的 profit and loss

      - ``event`` (支持 ``.`` 访问的 ``dict``): 保存事件 update 参数

        - ``order`` (``object``): 触发 ``update`` 的 order
        - ``size`` (``int``): update 的 size
        - ``price`` (``float``): update 的 price
        - ``commission`` (``float``): update 的 commission

    ---
    交互示例:

    >>> hist = TradeHistory(Trade.Open, 0.0, 3, 10, 100.0, 1000.0, 5.0, 4.0, None)
    >>> hist.status.size
    10
    >>> hist.doupdate(order=None, size=10, price=100.0, commission=1.0)
    >>> hist.event.commission
    1.0
    '''

    def __init__(self,
                 status, dt, barlen, size, price, value, pnl, pnlcomm, tz, event=None):
        '''初始化为 Trade 的当前状态。

        Args:
            status (int): Trade status。
            dt (float): float 编码的 datetime。
            barlen (int): trade 已活跃的 bar 数量。
            size (int): Trade 当前 size。
            price (float): Trade 当前 price。
            value (float): Trade 当前 value。
            pnl (float): 当前 gross pnl。
            pnlcomm (float): 扣除 commission 后的 net pnl。
            tz: 与 ``dt`` 配套使用的 timezone。
            event: 可选的 event 数据，会保存到 ``self.event``。
        '''
        super(TradeHistory, self).__init__()
        self.status.status = status
        self.status.dt = dt
        self.status.barlen = barlen
        self.status.size = size
        self.status.price = price
        self.status.value = value
        self.status.pnl = pnl
        self.status.pnlcomm = pnlcomm
        self.status.tz = tz
        if event is not None:
            self.event = event

    def __reduce__(self):
        return (self.__class__, (self.status.status, self.status.dt, self.status.barlen, self.status.size,
                                 self.status.price, self.status.value, self.status.pnl, self.status.pnlcomm,
                                 self.status.tz, self.event, ))

    def doupdate(self, order, size, price, commission):
        '''填充 history entry 中的 ``update`` 事件部分。

        Args:
            order: 触发本次 update 的 order。
            size (int): 本次 update 的 size。
            price (float): 本次 update 的 price。
            commission (float): 本次 update 产生的 commission。
        '''
        self.event.order = order
        self.event.size = size
        self.event.price = price
        self.event.commission = commission

        # 不再允许继续更新，避免误写字段
        self._close()

    def datetime(self, tz=None, naive=True):
        '''返回本次 update 事件发生时的 datetime。

        Args:
            tz: 可选 timezone。未提供时使用 history 中保存的 timezone。
            naive (bool): 是否返回 naive datetime。

        Returns:
            datetime.datetime: update 事件发生时间。
        '''
        return num2date(self.status.dt, tz or self.status.tz, naive)


class Trade(object):
    '''跟踪一个 trade 的生命周期：size、price、commission 和 value。

    trade 从 0 开始，可以增加和减少；当 size 回到 0 时视为 closed。

    trade 可以是 long（正 size）或 short（负 size）。

    Trade 不用于表达反转，内部逻辑也不支持反转。

    成员属性:

      - ``ref``: 唯一 trade 标识符
      - ``status`` (``int``): Created、Open、Closed 之一
      - ``tradeid``: 创建 order 时传入的分组 tradeid。order 中默认值为 0
      - ``size`` (``int``): trade 当前 size
      - ``price`` (``float``): trade 当前 price
      - ``value`` (``float``): trade 当前 value
      - ``commission`` (``float``): 当前累计 commission
      - ``pnl`` (``float``): trade 当前 profit and loss（gross pnl）
      - ``pnlcomm`` (``float``): trade 当前扣除 commission 后的 profit and loss
        （net pnl）
      - ``isclosed`` (``bool``): 记录最后一次 update 是否关闭了 trade
        （将 size 设为 0）
      - ``isopen`` (``bool``): 记录是否有任何 update 打开了 trade
      - ``justopened`` (``bool``): trade 是否刚刚打开
      - ``baropen`` (``int``): 该 trade 打开时所在的 bar

      - ``dtopen`` (``float``): trade 打开时的 float 编码 datetime

        - 使用 ``open_datetime`` 获取 Python ``datetime.datetime``，或使用平台
          提供的 ``num2date`` 方法

      - ``barclose`` (``int``): 该 trade 关闭时所在的 bar

      - ``dtclose`` (``float``): trade 关闭时的 float 编码 datetime

        - 使用 ``close_datetime`` 获取 Python ``datetime.datetime``，或使用平台
          提供的 ``num2date`` 方法

      - ``barlen`` (``int``): 该 trade 保持 open 的 bar 数量
      - ``historyon`` (``bool``): 是否记录 history
      - ``history`` (``list``): 随每次 "update" 事件更新的列表，包含 update 后的
        状态和 update 使用的参数

        history 中第一个 entry 是 Opening Event，最后一个 entry 是 Closing Event

    ---
    交互示例:

    >>> trade = Trade(size=10, price=100.0, value=1000.0, commission=1.5)
    >>> trade.size, trade.price, trade.commission
    (10, 100.0, 1.5)
    >>> len(trade)
    10
    >>> bool(trade)
    True
    '''
    refbasis = itertools.count(1)

    status_names = ['Created', 'Open', 'Closed']
    Created, Open, Closed = range(3)

    def __str__(self):
        toprint = (
            'ref', 'data', 'tradeid',
            'size', 'price', 'value', 'commission', 'pnl', 'pnlcomm',
            'justopened', 'isopen', 'isclosed',
            'baropen', 'dtopen', 'barclose', 'dtclose', 'barlen',
            'historyon', 'history',
            'status')

        return '\n'.join(
            (':'.join((x, str(getattr(self, x)))) for x in toprint)
        )

    def __init__(self, data=None, tradeid=0, historyon=False,
                 size=0, price=0.0, value=0.0, commission=0.0):
        '''
        创建一个 Trade 实例。

        Args:
            data: 与 trade 关联的 data feed。
            tradeid (int): 用于分组 order/trade 的标识符。
            historyon (bool): 是否记录每次 update 的 history。
            size (int): 初始 trade size。
            price (float): 初始 trade price。
            value (float): 初始 trade value。
            commission (float): 初始累计 commission。
        '''

        self.ref = next(self.refbasis)
        self.data = data
        self.tradeid = tradeid
        self.size = size
        self.price = price
        self.value = value
        self.commission = commission

        self.pnl = 0.0
        self.pnlcomm = 0.0

        self.justopened = False
        self.isopen = False
        self.isclosed = False

        self.baropen = 0
        self.dtopen = 0.0
        self.barclose = 0
        self.dtclose = 0.0
        self.barlen = 0

        self.historyon = historyon
        self.history = list()

        self.status = self.Created

    def __len__(self):
        '''返回 trade 的绝对 size。

        Returns:
            int: ``abs(self.size)``。
        '''
        return abs(self.size)

    def __bool__(self):
        '''判断 trade size 是否非零。

        Returns:
            bool: 如果 ``size != 0`` 则返回 ``True``。
        '''
        return self.size != 0

    __nonzero__ = __bool__

    def getdataname(self):
        '''获取该 trade 引用的 data 名称。

        Returns:
            str: ``self.data._name``。
        '''
        return self.data._name

    def open_datetime(self, tz=None, naive=True):
        '''返回 trade 打开时间对应的 ``datetime.datetime``。

        Args:
            tz: 可选 timezone。
            naive (bool): 是否返回 naive datetime。

        Returns:
            datetime.datetime: trade 打开时间。
        '''
        return self.data.num2date(self.dtopen, tz=tz, naive=naive)

    def close_datetime(self, tz=None, naive=True):
        '''返回 trade 关闭时间对应的 ``datetime.datetime``。

        Args:
            tz: 可选 timezone。
            naive (bool): 是否返回 naive datetime。

        Returns:
            datetime.datetime: trade 关闭时间。
        '''
        return self.data.num2date(self.dtclose, tz=tz, naive=naive)

    def update(self, order, size, price, value, commission, pnl,
               comminfo):
        '''
        更新当前 trade。该逻辑不会检查 trade 是否反转，因为 Trade 在概念上
        不支持反转。

        如果一次 update 将 size 设为 0，``closed`` 会被置为 true。

        每个 order 可能收到两次 update：一次对应已关闭的现有 size（sell 抵消
        buy），另一次对应打开的新部分（sell 反转 buy）。

        Args:
            order: 完全或部分生成本次 update 的 order 对象。
            size (int): 用于更新 trade 的数量。如果 size 与当前 trade 同号，
                会增加 position；如果与当前 open size 异号，会减少或关闭
                position。
            price (float): 执行 price，必须为正以保持一致性。
            value (float): 未使用。新 size/price 操作产生的成本，trade 会自行
                计算 value。
            commission (float): 新 size/price 操作产生的 commission。
            pnl (float): 未使用。执行部分产生的 pnl，trade 会独立计算 pnl。
            comminfo: 用于计算 value 和 profit/loss 的 CommissionInfo 对象。

        Returns:
            None: 直接更新当前 Trade 实例。
        '''
        if not size:
            return  # 空 update，跳过后续计算

        # Commission 只能增加
        self.commission += commission

        # 更新 size，并保留旧 size 供逻辑和计算使用
        oldsize = self.size
        self.size += size  # 减仓时 size 会携带相反符号

        # 检查本次是否刚刚打开
        self.justopened = bool(not oldsize and size)

        if self.justopened:
            self.baropen = len(self.data)
            self.dtopen = 0.0 if order.p.simulated else self.data.datetime[0]
            self.long = self.size > 0

        # 任何非零 size 都表示 trade 已打开
        self.isopen = bool(self.size)

        # 更新当前 trade 长度
        self.barlen = len(self.data) - self.baropen

        # 记录 position 是否被关闭（归零）
        self.isclosed = bool(oldsize and not self.size)

        # 记录 trade 的最后一个 bar
        if self.isclosed:
            self.isopen = False
            self.barclose = len(self.data)
            self.dtclose = self.data.datetime[0]

            self.status = self.Closed
        elif self.isopen:
            self.status = self.Open

        if abs(self.size) > abs(oldsize):
            # position 增加（无论正负），更新平均 price
            self.price = (oldsize * self.price + size * price) / self.size
            pnl = 0.0

        else:  # abs(self.size) < abs(oldsize)
            # position 减少或关闭
            pnl = comminfo.profitandloss(-size, self.price, price)

        self.pnl += pnl
        self.pnlcomm = self.pnl - self.commission

        self.value = comminfo.getvaluesize(self.size, self.price)

        # 如果需要，更新 history
        if self.historyon:
            dt0 = self.data.datetime[0] if not order.p.simulated else 0.0
            histentry = TradeHistory(
                self.status, dt0, self.barlen,
                self.size, self.price, self.value,
                self.pnl, self.pnlcomm, self.data._tz)
            histentry.doupdate(order, size, price, commission)
            self.history.append(histentry)
