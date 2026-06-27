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
import datetime
import itertools

from .utils.py3 import range, with_metaclass, iteritems

from .metabase import MetaParams
from .utils import AutoOrderedDict


class OrderExecutionBit(object):
    '''
    保存一次 order execution 的信息。一个 "bit" 不负责判断 order 是否完全或
    部分执行，它只保存执行信息。

    成员属性:

      - dt: datetime (float) 执行时间
      - size: 本次执行的数量
      - price: 执行 price
      - closed: 本次执行中用于关闭已有 position 的数量
      - opened: 本次执行中用于打开新 position 的数量
      - openedvalue: "opened" 部分的 market value
      - closedvalue: "closed" 部分的 market value
      - closedcomm: "closed" 部分的 commission
      - openedcomm: "opened" 部分的 commission

      - value: 整个 bit size 的 market value
      - comm: 整个 bit execution 的 commission
      - pnl: 该 bit 产生的 pnl（如果关闭了某些 position）

      - psize: 当前 open position size
      - pprice: 当前 open position price

    ---
    交互示例:

    >>> bit = OrderExecutionBit(size=5, price=100.0, opened=5, openedvalue=500.0)
    >>> bit.value, bit.comm, bit.pnl
    (500.0, 0.0, 0.0)
    '''

    def __init__(self,
                 dt=None, size=0, price=0.0,
                 closed=0, closedvalue=0.0, closedcomm=0.0,
                 opened=0, openedvalue=0.0, openedcomm=0.0,
                 pnl=0.0,
                 psize=0, pprice=0.0):
        '''
        创建一个 execution bit。

        Args:
            dt: 执行时间，通常是 float 编码的 datetime。
            size (int): 本次执行 size。
            price (float): 本次执行 price。
            closed (int): 本次执行中关闭已有 position 的数量。
            closedvalue (float): ``closed`` 部分的 value。
            closedcomm (float): ``closed`` 部分的 commission。
            opened (int): 本次执行中打开新 position 的数量。
            openedvalue (float): ``opened`` 部分的 value。
            openedcomm (float): ``opened`` 部分的 commission。
            pnl (float): 本次 execution bit 产生的 pnl。
            psize (int): 执行后当前 open position size。
            pprice (float): 执行后当前 open position price。
        '''

        self.dt = dt
        self.size = size
        self.price = price

        self.closed = closed
        self.opened = opened
        self.closedvalue = closedvalue
        self.openedvalue = openedvalue
        self.closedcomm = closedcomm
        self.openedcomm = openedcomm

        self.value = closedvalue + openedvalue
        self.comm = closedcomm + openedcomm
        self.pnl = pnl

        self.psize = psize
        self.pprice = pprice


class OrderData(object):
    '''
    保存 order 在 Creation 和 Execution 阶段的实际数据。

    对 Creation 来说，它保存发出的请求；对 Execution 来说，它保存实际结果。

    成员属性:

      - exbits : 该 OrderData 对应的 OrderExecutionBits iterable

      - dt: datetime (float) 创建/执行时间
      - size: 请求/执行 size
      - price: 执行 price
        注意: 如果未给出 price，也未给出 pricelimit，order 创建时的 close
        price 会被用作参考
      - pricelimit: 保存 StopLimit 的 pricelimit（它会先触发）
      - trailamount: trailing stops 中的绝对 price 距离
      - trailpercent: trailing stops 中的百分比 price 距离

      - value: 整个 bit size 的 market value
      - comm: 整个 bit execution 的 commission
      - pnl: 该 bit 产生的 pnl（如果关闭了某些 position）
      - margin: Order 产生的 margin（如果有）

      - psize: 当前 open position size
      - pprice: 当前 open position price

    ---
    交互示例:

    >>> data = OrderData(size=0, price=0.0, remsize=10)
    >>> data.add(dt=1.0, size=5, price=100.0, opened=5, openedvalue=500.0)
    >>> data.size, data.price, data.remsize
    (5, 100.0, 5)
    >>> clone = data.clone()
    >>> len(clone.getpending())
    1
    '''
    # 根据文档，collections.deque 在两端 append 是线程安全的。这里没有 pop，
    # 因此只需要两个索引来判断哪些 exbits 是新的。在 clone (__copy__) 时，
    # 索引会更新为前一个 end 和新的 end
    # (len(exbits)
    # Example: start 0, 0 -> islice(exbits, 0, 0) -> []
    # One added -> copy -> updated 0, 1 -> islice(exbits, 0, 1) -> [1 elem]
    # Other added -> copy -> updated 1, 2 -> islice(exbits, 1, 2) -> [1 elem]
    # 在所有当前实现中，"add" 和 "__copy__" 总是在同一线程发生，因此 copy
    # 期间不会 append，可以安全查询 exbits 的 len，无需担心另一个线程 append，
    # 也不需要 lock

    def __init__(self, dt=None, size=0, price=0.0, pricelimit=0.0, remsize=0,
                 pclose=0.0, trailamount=0.0, trailpercent=0.0):
        '''
        创建 OrderData。

        Args:
            dt: 创建/执行时间，通常是 float 编码的 datetime。
            size (int): 请求或已执行 size。
            price (float): 请求或执行 price。
            pricelimit (float): StopLimit 使用的 limit price。
            remsize (int): 剩余未执行 size。
            pclose (float): order 创建时的 close price。
            trailamount (float): trailing stop 的绝对 price 距离。
            trailpercent (float): trailing stop 的百分比 price 距离。
        '''

        self.pclose = pclose
        self.exbits = collections.deque()  # 用于保存历史 execution bits
        self.p1, self.p2 = 0, 0  # pending notifications 的索引

        self.dt = dt
        self.size = size
        self.remsize = remsize
        self.price = price
        self.pricelimit = pricelimit
        self.trailamount = trailamount
        self.trailpercent = trailpercent

        if not pricelimit:
            # 未给出 pricelimit 时，使用给定 price
            self.pricelimit = self.price

        if pricelimit and not price:
            # 如果设置了 pricelimit，则必须始终设置 price
            self.price = pricelimit

        self.plimit = pricelimit

        self.value = 0.0
        self.comm = 0.0
        self.margin = None
        self.pnl = 0.0

        self.psize = 0
        self.pprice = 0

    def _getplimit(self):
        return self._plimit

    def _setplimit(self, val):
        self._plimit = val

    plimit = property(_getplimit, _setplimit)

    def __len__(self):
        return len(self.exbits)

    def __getitem__(self, key):
        return self.exbits[key]

    def add(self, dt, size, price,
            closed=0, closedvalue=0.0, closedcomm=0.0,
            opened=0, openedvalue=0.0, openedcomm=0.0,
            pnl=0.0,
            psize=0, pprice=0.0):
        '''添加一次 execution bit。

        Args:
            dt: 执行时间。
            size (int): 本次执行 size。
            price (float): 本次执行 price。
            closed (int): 本次关闭已有 position 的数量。
            closedvalue (float): ``closed`` 部分的 value。
            closedcomm (float): ``closed`` 部分的 commission。
            opened (int): 本次打开新 position 的数量。
            openedvalue (float): ``opened`` 部分的 value。
            openedcomm (float): ``opened`` 部分的 commission。
            pnl (float): 本次执行产生的 pnl。
            psize (int): 执行后的 position size。
            pprice (float): 执行后的 position price。
        '''

        self.addbit(
            OrderExecutionBit(dt, size, price,
                              closed, closedvalue, closedcomm,
                              opened, openedvalue, openedcomm, pnl,
                              psize, pprice))

    def addbit(self, exbit):
        '''保存 ExecutionBit，并基于 ExBit 重新计算自身值。

        Args:
            exbit (OrderExecutionBit): 要加入的 execution bit。
        '''
        self.exbits.append(exbit)

        self.remsize -= exbit.size

        self.dt = exbit.dt
        oldvalue = self.size * self.price
        newvalue = exbit.size * exbit.price
        self.size += exbit.size
        self.price = (oldvalue + newvalue) / self.size
        self.value += exbit.value
        self.comm += exbit.comm
        self.pnl += exbit.pnl
        self.psize = exbit.psize
        self.pprice = exbit.pprice

    def getpending(self):
        '''返回 pending execution bits。

        Returns:
            list: 当前 pending 的 execution bits。
        '''
        return list(self.iterpending())

    def iterpending(self):
        '''迭代 pending execution bits。

        Returns:
            itertools.islice: pending execution bits 的 iterator。
        '''
        return itertools.islice(self.exbits, self.p1, self.p2)

    def markpending(self):
        '''重建索引，以标记 clone 中哪些 exbits 处于 pending 状态。'''
        self.p1, self.p2 = self.p2, len(self.exbits)

    def clone(self):
        '''复制当前 OrderData，并把新增 execution bits 标记为 pending。

        Returns:
            OrderData: 当前对象的浅拷贝，带有更新后的 pending 索引。
        '''
        self.markpending()
        obj = copy(self)
        return obj


class OrderBase(with_metaclass(MetaParams, object)):
    params = (
        ('owner', None), ('data', None),
        ('size', None), ('price', None), ('pricelimit', None),
        ('exectype', None), ('valid', None), ('tradeid', 0), ('oco', None),
        ('trailamount', None), ('trailpercent', None),
        ('parent', None), ('transmit', True),
        ('simulated', False),
        # To support historical order evaluation
        ('histnotify', False),
    )

    DAY = datetime.timedelta()  # constant for DAY order identification

    # Time Restrictions for orders
    T_Close, T_Day, T_Date, T_None = range(4)

    # Volume Restrictions for orders
    V_None = range(1)

    (Market, Close, Limit, Stop, StopLimit, StopTrail, StopTrailLimit,
     Historical) = range(8)
    ExecTypes = ['Market', 'Close', 'Limit', 'Stop', 'StopLimit', 'StopTrail',
                 'StopTrailLimit', 'Historical']

    OrdTypes = ['Buy', 'Sell']
    Buy, Sell = range(2)

    Created, Submitted, Accepted, Partial, Completed, \
        Canceled, Expired, Margin, Rejected = range(9)

    Cancelled = Canceled  # alias

    Status = [
        'Created', 'Submitted', 'Accepted', 'Partial', 'Completed',
        'Canceled', 'Expired', 'Margin', 'Rejected',
    ]

    refbasis = itertools.count(1)  # for a unique identifier per order

    def _getplimit(self):
        return self._plimit

    def _setplimit(self, val):
        self._plimit = val

    plimit = property(_getplimit, _setplimit)

    def __getattr__(self, name):
        # Return attr from params if not found in order
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            setattr(self.params, name, value)
        else:
            super(Order, self).__setattribute__(name, value)

    def __str__(self):
        tojoin = list()
        tojoin.append('Ref: {}'.format(self.ref))
        tojoin.append('OrdType: {}'.format(self.ordtype))
        tojoin.append('OrdType: {}'.format(self.ordtypename()))
        tojoin.append('Status: {}'.format(self.status))
        tojoin.append('Status: {}'.format(self.getstatusname()))
        tojoin.append('Size: {}'.format(self.size))
        tojoin.append('Price: {}'.format(self.price))
        tojoin.append('Price Limit: {}'.format(self.pricelimit))
        tojoin.append('TrailAmount: {}'.format(self.trailamount))
        tojoin.append('TrailPercent: {}'.format(self.trailpercent))
        tojoin.append('ExecType: {}'.format(self.exectype))
        tojoin.append('ExecType: {}'.format(self.getordername()))
        tojoin.append('CommInfo: {}'.format(self.comminfo))
        tojoin.append('End of Session: {}'.format(self.dteos))
        tojoin.append('Info: {}'.format(self.info))
        tojoin.append('Broker: {}'.format(self.broker))
        tojoin.append('Alive: {}'.format(self.alive()))

        return '\n'.join(tojoin)

    def __init__(self):
        self.ref = next(self.refbasis)
        self.broker = None
        self.info = AutoOrderedDict()
        self.comminfo = None
        self.triggered = False

        self._active = self.parent is None
        self.status = Order.Created

        self.plimit = self.p.pricelimit  # alias via property

        if self.exectype is None:
            self.exectype = Order.Market

        if not self.isbuy():
            self.size = -self.size

        # Set a reference price if price is not set using
        # the close price
        pclose = self.data.close[0] if not self.p.simulated else self.price
        price = pclose if not self.price and not self.pricelimit else self.price

        dcreated = self.data.datetime[0] if not self.p.simulated else 0.0
        self.created = OrderData(dt=dcreated,
                                 size=self.size,
                                 price=price,
                                 pricelimit=self.pricelimit,
                                 pclose=pclose,
                                 trailamount=self.trailamount,
                                 trailpercent=self.trailpercent)

        # Adjust price in case a trailing limit is wished
        if self.exectype in [Order.StopTrail, Order.StopTrailLimit]:
            self._limitoffset = self.created.price - self.created.pricelimit
            price = self.created.price
            self.created.price = float('inf' * self.isbuy() or '-inf')
            self.trailadjust(price)
        else:
            self._limitoffset = 0.0

        self.executed = OrderData(remsize=self.size)
        self.position = 0

        if isinstance(self.valid, datetime.date):
            # comparison will later be done against the raw datetime[0] value
            self.valid = self.data.date2num(self.valid)
        elif isinstance(self.valid, datetime.timedelta):
            # offset with regards to now ... get utcnow + offset
            # when reading with date2num ... it will be automatically localized
            if self.valid == self.DAY:
                valid = datetime.datetime.combine(
                    self.data.datetime.date(), datetime.time(23, 59, 59, 9999))
            else:
                valid = self.data.datetime.datetime() + self.valid

            self.valid = self.data.date2num(valid)

        elif self.valid is not None:
            if not self.valid:  # avoid comparing None and 0
                valid = datetime.datetime.combine(
                    self.data.datetime.date(), datetime.time(23, 59, 59, 9999))
            else:  # assume float
                valid = self.data.datetime[0] + self.valid

        if not self.p.simulated:
            # provisional end-of-session
            # get next session end
            dtime = self.data.datetime.datetime(0)
            session = self.data.p.sessionend
            dteos = dtime.replace(hour=session.hour, minute=session.minute,
                                  second=session.second,
                                  microsecond=session.microsecond)

            if dteos < dtime:
                # eos before current time ... no ... must be at least next day
                dteos += datetime.timedelta(days=1)

            self.dteos = self.data.date2num(dteos)
        else:
            self.dteos = 0.0

    def clone(self):
        '''复制当前 order。

        Returns:
            OrderBase: 当前 order 的浅拷贝，其中 ``executed`` 会使用自身的
            ``clone`` 结果替换，以保留 pending execution bits。
        '''
        # status、triggered 和 executed 是 order 中仅有的可变部分。
        # status 和 triggered 已由 copy 覆盖，executed 需要替换为自身的智能 clone
        obj = copy(self)
        obj.executed = self.executed.clone()
        return obj  # status 可能在下一步变成 completed

    def getstatusname(self, status=None):
        '''返回给定 status 的名称，或当前 order 的 status 名称。

        Args:
            status (int): 可选 status。未提供时使用当前 order status。

        Returns:
            str: status 名称。
        '''
        return self.Status[self.status if status is None else status]

    def getordername(self, exectype=None):
        '''返回给定 exectype 的名称，或当前 order 的 exectype 名称。

        Args:
            exectype (int): 可选 execution type。未提供时使用当前 order exectype。

        Returns:
            str: execution type 名称。
        '''
        return self.ExecTypes[self.exectype if exectype is None else exectype]

    @classmethod
    def ExecType(cls, exectype):
        return getattr(cls, exectype)

    def ordtypename(self, ordtype=None):
        '''返回给定 ordtype 的名称，或当前 order 的 ordtype 名称。

        Args:
            ordtype (int): 可选 order type。未提供时使用当前 order ordtype。

        Returns:
            str: order type 名称。
        '''
        return self.OrdTypes[self.ordtype if ordtype is None else ordtype]

    def active(self):
        return self._active

    def activate(self):
        self._active = True

    def alive(self):
        '''判断 order 是否仍处于可执行状态。

        Returns:
            bool: 如果 order status 为 Created、Submitted、Partial 或 Accepted，
            返回 ``True``。
        '''
        return self.status in [Order.Created, Order.Submitted,
                               Order.Partial, Order.Accepted]

    def addcomminfo(self, comminfo):
        '''保存与资产关联的 CommInfo scheme。

        Args:
            comminfo: 要关联到 order 的 CommInfo 对象。
        '''
        self.comminfo = comminfo

    def addinfo(self, **kwargs):
        '''将 ``kwargs`` 中的 key/value 加入内部 info dictionary。

        Args:
            **kwargs: 要保存在 order 中的自定义信息。
        '''
        for key, val in iteritems(kwargs):
            self.info[key] = val

    def __eq__(self, other):
        return other is not None and self.ref == other.ref

    def __ne__(self, other):
        return self.ref != other.ref

    def isbuy(self):
        '''判断 order 是否为 Buy order。

        Returns:
            bool: 如果 order 是 Buy order，返回 ``True``。
        '''
        return self.ordtype == self.Buy

    def issell(self):
        '''判断 order 是否为 Sell order。

        Returns:
            bool: 如果 order 是 Sell order，返回 ``True``。
        '''
        return self.ordtype == self.Sell

    def setposition(self, position):
        '''接收并保存该资产的当前 position。

        Args:
            position: 当前资产 position。
        '''
        self.position = position

    def submit(self, broker=None):
        '''将 order 标记为 submitted，并保存提交到的 broker。

        Args:
            broker: 接收该 order 的 broker。
        '''
        self.status = Order.Submitted
        self.broker = broker
        self.plen = len(self.data)

    def accept(self, broker=None):
        '''将 order 标记为 accepted。

        Args:
            broker: accept 该 order 的 broker。
        '''
        self.status = Order.Accepted
        self.broker = broker

    def brokerstatus(self):
        '''尝试从 order 所属 broker 获取 status。

        Returns:
            int: broker 返回的 order status；如果未关联 broker，则返回最后已知
            status。
        '''
        if self.broker:
            return self.broker.orderstatus(self)

        return self.status

    def reject(self, broker=None):
        '''将 order 标记为 rejected。

        Args:
            broker: reject 该 order 的 broker。

        Returns:
            bool: 如果本次成功标记为 rejected，返回 ``True``；如果已经是
            rejected，返回 ``False``。
        '''
        if self.status == Order.Rejected:
            return False

        self.status = Order.Rejected
        self.broker = broker
        if not self.p.simulated:
            self.executed.dt = self.data.datetime[0]
        return True

    def cancel(self):
        '''将 order 标记为 cancelled。'''
        self.status = Order.Canceled
        if not self.p.simulated:
            self.executed.dt = self.data.datetime[0]

    def margin(self):
        '''将 order 标记为遇到 margin call。'''
        self.status = Order.Margin
        if not self.p.simulated:
            self.executed.dt = self.data.datetime[0]

    def completed(self):
        '''将 order 标记为完全成交。'''
        self.status = self.Completed

    def partial(self):
        '''将 order 标记为部分成交。'''
        self.status = self.Partial

    def execute(self, dt, size, price,
                closed, closedvalue, closedcomm,
                opened, openedvalue, openedcomm,
                margin, pnl,
                psize, pprice):

        '''接收并保存 data execution 输入。

        Args:
            dt: 执行时间。
            size (int): 执行 size。
            price (float): 执行 price。
            closed (int): 用于关闭已有 position 的数量。
            closedvalue (float): ``closed`` 部分的 value。
            closedcomm (float): ``closed`` 部分的 commission。
            opened (int): 用于打开新 position 的数量。
            openedvalue (float): ``opened`` 部分的 value。
            openedcomm (float): ``opened`` 部分的 commission。
            margin (float): 本次执行产生的 margin。
            pnl (float): 本次执行产生的 pnl。
            psize (int): 执行后 position size。
            pprice (float): 执行后 position price。
        '''
        if not size:
            return

        self.executed.add(dt, size, price,
                          closed, closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          pnl, psize, pprice)

        self.executed.margin = margin

    def expire(self):
        '''将 order 标记为 expired。

        Returns:
            bool: 如果成功标记为 expired，返回 ``True``。
        '''
        self.status = self.Expired
        return True

    def trailadjust(self, price):
        pass  # generic interface


class Order(OrderBase):
    '''
    保存 order 创建/执行数据以及 order type 的类。

    order 可能有以下 status:

      - Submitted: 已发送给 broker，等待确认
      - Accepted: 已被 broker 接受
      - Partial: 部分成交
      - Completed: 完全成交
      - Canceled/Cancelled: 被用户取消
      - Expired: 已过期
      - Margin: cash 不足，无法执行 order
      - Rejected: 被 broker 拒绝

        这可能发生在 order 提交期间（因此 order 不会进入 Accepted status），也
        可能发生在每个新 bar price 执行前，因为 cash 已被其他来源占用
        （future-like instruments 可能降低了 cash，或其他 orders 已经执行）。

    成员属性:

      - ref: 唯一 order 标识符
      - created: 保存 creation data 的 OrderData
      - executed: 保存 execution data 的 OrderData

      - info: 通过 :func:`addinfo` 方法传入的自定义信息。它以 OrderedDict
        子类形式保存，因此 key 也可以用 ``.`` 访问语法指定

    用户方法:

      - isbuy(): 返回 bool，表示 order 是否 buy
      - issell(): 返回 bool，表示 order 是否 sell
      - alive(): 返回 bool，表示 order 是否处于 Partial 或 Accepted status
    '''

    def execute(self, dt, size, price,
                closed, closedvalue, closedcomm,
                opened, openedvalue, openedcomm,
                margin, pnl,
                psize, pprice):

        super(Order, self).execute(dt, size, price,
                                   closed, closedvalue, closedcomm,
                                   opened, openedvalue, openedcomm,
                                   margin, pnl, psize, pprice)

        if self.executed.remsize:
            self.status = Order.Partial
        else:
            self.status = Order.Completed

        # self.comminfo = None

    def expire(self):
        if self.exectype == Order.Market:
            return False  # will be executed yes or yes

        if self.valid and self.data.datetime[0] > self.valid:
            self.status = Order.Expired
            self.executed.dt = self.data.datetime[0]
            return True

        return False

    def trailadjust(self, price):
        if self.trailamount:
            pamount = self.trailamount
        elif self.trailpercent:
            pamount = price * self.trailpercent
        else:
            pamount = 0.0

        # Stop sell is below (-), stop buy is above, move only if needed
        if self.isbuy():
            price += pamount
            if price < self.created.price:
                self.created.price = price
                if self.exectype == Order.StopTrailLimit:
                    self.created.pricelimit = price - self._limitoffset
        else:
            price -= pamount
            if price > self.created.price:
                self.created.price = price
                if self.exectype == Order.StopTrailLimit:
                    # limitoffset is negative when pricelimit was greater
                    # the - allows increasing the price limit if stop increases
                    self.created.pricelimit = price - self._limitoffset


class BuyOrder(Order):
    ordtype = Order.Buy


class StopBuyOrder(BuyOrder):
    pass


class StopLimitBuyOrder(BuyOrder):
    pass


class SellOrder(Order):
    ordtype = Order.Sell


class StopSellOrder(SellOrder):
    pass


class StopLimitSellOrder(SellOrder):
    pass
