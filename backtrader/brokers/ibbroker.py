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
import threading
import uuid

import ib.ext.Order
import ib.opt as ibopt

from backtrader.feed import DataBase
from backtrader import (TimeFrame, num2date, date2num, BrokerBase,
                        Order, OrderBase, OrderData)
from backtrader.utils.py3 import bytes, bstr, with_metaclass, queue, MAXFLOAT
from backtrader.metabase import MetaParams
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import ibstore
from backtrader.utils import AutoDict, AutoOrderedDict
from backtrader.comminfo import CommInfoBase

bytes = bstr  # ibpy 需要 py2/3 兼容 bytes


class IBOrderState(object):
    # 包装 OrderState 对象，并提供可打印表示
    _fields = ['status', 'initMargin', 'maintMargin', 'equityWithLoan',
               'commission', 'minCommission', 'maxCommission',
               'commissionCurrency', 'warningText']

    def __init__(self, orderstate):
        for f in self._fields:
            fname = 'm_' + f
            setattr(self, fname, getattr(orderstate, fname))

    def __str__(self):
        txt = list()
        txt.append('--- ORDERSTATE BEGIN')
        for f in self._fields:
            fname = 'm_' + f
            txt.append('{}: {}'.format(f.capitalize(), getattr(self, fname)))
        txt.append('--- ORDERSTATE END')
        return '\n'.join(txt)


class IBOrder(OrderBase, ib.ext.Order.Order):
    '''IBPy order 的子类，用于提供与内部 order 兼容所需的最小扩展功能。

    ``OrderBase`` 处理参数后，``__init__`` 会接管这些参数值，并设置
    ``ib.ext.Order.Order`` 对象中的对应字段。

    kwargs 中提供的额外参数会直接应用到 ``ib.ext.Order.Order`` 对象，可按如下方式使用::

      例如：如果 ``backtrader`` 直接支持的 order execution type 不够，
      对 *Interactive Brokers* 可通过 *kwargs* 传入::

        orderType='LIT', lmtPrice=10.0, auxPrice=9.8

      这会覆盖 ``backtrader`` 创建的设置，并生成一个 ``LIMIT IF TOUCHED`` order，
      其中 *touched* price 为 9.8，*limit* price 为 10.0。

    该用法通常通过 ``Cerebro`` 中所用 ``Strategy`` 子类的 ``Buy`` 与 ``Sell`` 方法完成。
    '''

    def __str__(self):
        '''获取基类打印内容，并追加部分 ib.Order 专属字段。'''
        basetxt = super(IBOrder, self).__str__()
        tojoin = [basetxt]
        tojoin.append('Ref: {}'.format(self.ref))
        tojoin.append('orderId: {}'.format(self.m_orderId))
        tojoin.append('Action: {}'.format(self.m_action))
        tojoin.append('Size (ib): {}'.format(self.m_totalQuantity))
        tojoin.append('Lmt Price: {}'.format(self.m_lmtPrice))
        tojoin.append('Aux Price: {}'.format(self.m_auxPrice))
        tojoin.append('OrderType: {}'.format(self.m_orderType))
        tojoin.append('Tif (Time in Force): {}'.format(self.m_tif))
        tojoin.append('GoodTillDate: {}'.format(self.m_goodTillDate))
        return '\n'.join(tojoin)

    # 将 backtrader order type 映射到 IB 专属类型
    _IBOrdTypes = {
        None: bytes('MKT'),  # default
        Order.Market: bytes('MKT'),
        Order.Limit: bytes('LMT'),
        Order.Close: bytes('MOC'),
        Order.Stop: bytes('STP'),
        Order.StopLimit: bytes('STPLMT'),
        Order.StopTrail: bytes('TRAIL'),
        Order.StopTrailLimit: bytes('TRAIL LIMIT'),
    }

    def __init__(self, action, **kwargs):

        # 标记 openOrder 中曾出现 PendingCancel/Cancelled，表示即将取消
        self._willexpire = False

        self.ordtype = self.Buy if action == 'BUY' else self.Sell

        super(IBOrder, self).__init__()
        ib.ext.Order.Order.__init__(self)  # 调用第 2 个基类

        # 填充 IB 专属参数
        self.m_orderType = self._IBOrdTypes[self.exectype]
        self.m_permid = 0

        # 'B' 或 'S' 应已足够
        self.m_action = bytes(action)

        # 设置价格
        self.m_lmtPrice = 0.0
        self.m_auxPrice = 0.0

        if self.exectype == self.Market:  # is it really needed for Market?
            pass
        elif self.exectype == self.Close:  # is it ireally needed for Close?
            pass
        elif self.exectype == self.Limit:
            self.m_lmtPrice = self.price
        elif self.exectype == self.Stop:
            self.m_auxPrice = self.price  # stop price / exec is market
        elif self.exectype == self.StopLimit:
            self.m_lmtPrice = self.pricelimit  # req limit execution
            self.m_auxPrice = self.price  # trigger price
        elif self.exectype == self.StopTrail:
            if self.trailamount is not None:
                self.m_auxPrice = self.trailamount
            elif self.trailpercent is not None:
                # 期望值为百分比格式，因此乘以 100.0
                self.m_trailingPercent = self.trailpercent * 100.0
        elif self.exectype == self.StopTrailLimit:
            self.m_trailStopPrice = self.m_lmtPrice = self.price
            # limit offset 在 TWS 中相对价格差设置
            self.m_lmtPrice = self.pricelimit
            if self.trailamount is not None:
                self.m_auxPrice = self.trailamount
            elif self.trailpercent is not None:
                # 期望值为百分比格式，因此乘以 100.0
                self.m_trailingPercent = self.trailpercent * 100.0

        self.m_totalQuantity = abs(self.size)  # IB 只接受正数

        self.m_transmit = self.transmit
        if self.parent is not None:
            self.m_parentId = self.parent.m_orderId

        # 有效期类型（Time In Force）：DAY, GTC, IOC, GTD
        if self.valid is None:
            tif = 'GTC'  # Good til cancelled
        elif isinstance(self.valid, (datetime, date)):
            tif = 'GTD'  # Good til date
            self.m_goodTillDate = bytes(self.valid.strftime('%Y%m%d %H:%M:%S'))
        elif isinstance(self.valid, (timedelta,)):
            if self.valid == self.DAY:
                tif = 'DAY'
            else:
                tif = 'GTD'  # Good til date
                valid = datetime.now() + self.valid  # .now，使用本地时间
                self.m_goodTillDate = bytes(valid.strftime('%Y%m%d %H:%M:%S'))

        elif self.valid == 0:
            tif = 'DAY'
        else:
            tif = 'GTD'  # Good til date
            valid = num2date(self.valid)
            self.m_goodTillDate = bytes(valid.strftime('%Y%m%d %H:%M:%S'))

        self.m_tif = bytes(tif)

        # OCA
        self.m_ocaType = 1  # 带 block 取消所有剩余 order

        # 将自定义参数传给 order
        for k in kwargs:
            setattr(self, (not hasattr(self, k)) * 'm_' + k, kwargs[k])


class IBCommInfo(CommInfoBase):
    '''
    IB 会计算 commissions，但 ``Strategy`` 中的 trade 计算依赖 order 携带 CommInfo
    对象，以计算操作成本和价值。

    这些信息不是核心执行路径，但移除可能破坏既有用法，因此提供一个可近似完成计算的
    CommInfo 对象。

    margin 不是预先已知的信息（margin impact 可从 OrderState 对象获得），因此这里
    保留近似计算。
    '''

    def getvaluesize(self, size, price):
        # 实盘中 margin 接近 price
        return abs(size) * price

    def getoperationcost(self, size, price):
        '''返回一次操作需要占用的 cash 数量。'''
        # 与上方逻辑相同
        return abs(size) * price


class MetaIBBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，执行 broker 注册。'''
        # 初始化类
        super(MetaIBBroker, cls).__init__(name, bases, dct)
        ibstore.IBStore.BrokerCls = cls


class IBBroker(with_metaclass(MetaIBBroker, BrokerBase)):
    '''Interactive Brokers 的 broker 实现。

    该类将 Interactive Brokers 的 order/position 映射到 ``backtrader`` 内部 API。

    注意：

      - ``tradeid`` 并未真正支持，因为 profit/loss 直接来自 IB。IB 按 FIFO 方式计算，
        因此 pnl 对 tradeid 不精确。

      - Position

        如果操作开始时某资产已有 open position，或其他方式发出的 order 改变了
        position，``Cerebro`` 中 ``Strategy`` 计算的 trade 将无法反映真实情况。

        要避免该问题，broker 需要自行管理 position，并本地计算多 tradeid 的
        profit/loss；但这会削弱使用 live broker 的意义。
    '''
    params = ()

    def __init__(self, **kwargs):
        super(IBBroker, self).__init__()

        self.ib = ibstore.IBStore(**kwargs)

        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0

        self._lock_orders = threading.Lock()  # 控制访问
        self.orderbyid = dict()  # 按 order id 保存 order
        self.executions = dict()  # 已通知 execution
        self.ordstatus = collections.defaultdict(dict)
        self.notifs = queue.Queue()  # 保存需要通知的 order
        self.tonotify = collections.deque()  # 保存待通知 oid

    def start(self):
        super(IBBroker, self).start()
        self.ib.start(broker=self)

        if self.ib.connected():
            self.ib.reqAccountUpdates()
            self.startingcash = self.cash = self.ib.get_acc_cash()
            self.startingvalue = self.value = self.ib.get_acc_value()
        else:
            self.startingcash = self.cash = 0.0
            self.startingvalue = self.value = 0.0

    def stop(self):
        super(IBBroker, self).stop()
        self.ib.stop()

    def getcash(self):
        # 如果 IB 暂无响应，此调用不能阻塞
        self.cash = self.ib.get_acc_cash()
        return self.cash

    def getvalue(self, datas=None):
        self.value = self.ib.get_acc_value()
        return self.value

    def getposition(self, data, clone=True):
        return self.ib.getposition(data.tradecontract, clone=clone)

    def cancel(self, order):
        try:
            o = self.orderbyid[order.m_orderId]
        except (ValueError, KeyError):
            return  # 未找到，不可取消

        if order.status == Order.Cancelled:  # 已经取消
            return

        self.ib.cancelOrder(order.m_orderId)

    def orderstatus(self, order):
        try:
            o = self.orderbyid[order.m_orderId]
        except (ValueError, KeyError):
            o = order

        return o.status

    def submit(self, order):
        order.submit(self)

        # 按需设置 OCO
        if order.oco is None:  # 生成 UniqueId
            order.m_ocaGroup = bytes(uuid.uuid4())
        else:
            order.m_ocaGroup = self.orderbyid[order.oco.m_orderId].m_ocaGroup

        self.orderbyid[order.m_orderId] = order
        self.ib.placeOrder(order.m_orderId, order.data.tradecontract, order)
        self.notify(order)

        return order

    def getcommissioninfo(self, data):
        contract = data.tradecontract
        try:
            mult = float(contract.m_multiplier)
        except (ValueError, TypeError):
            mult = 1.0

        stocklike = contract.m_secType not in ('FUT', 'OPT', 'FOP',)

        return IBCommInfo(mult=mult, stocklike=stocklike)

    def _makeorder(self, action, owner, data,
                   size, price=None, plimit=None,
                   exectype=None, valid=None,
                   tradeid=0, **kwargs):

        order = IBOrder(action, owner=owner, data=data,
                        size=size, price=price, pricelimit=plimit,
                        exectype=exectype, valid=valid,
                        tradeid=tradeid,
                        m_clientId=self.ib.clientId,
                        m_orderId=self.ib.nextOrderId(),
                        **kwargs)

        order.addcomminfo(self.getcommissioninfo(data))
        return order

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0,
            **kwargs):

        order = self._makeorder(
            'BUY',
            owner, data, size, price, plimit, exectype, valid, tradeid,
            **kwargs)

        return self.submit(order)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0,
             **kwargs):

        order = self._makeorder(
            'SELL',
            owner, data, size, price, plimit, exectype, valid, tradeid,
            **kwargs)

        return self.submit(order)

    def notify(self, order):
        self.notifs.put(order.clone())

    def get_notification(self):
        try:
            return self.notifs.get(False)
        except queue.Empty:
            pass

        return None

    def next(self):
        self.notifs.put(None)  # 标记通知边界

    # msg 中的 order status
    (SUBMITTED, FILLED, CANCELLED, INACTIVE,
     PENDINGSUBMIT, PENDINGCANCEL, PRESUBMITTED) = (
        'Submitted', 'Filled', 'Cancelled', 'Inactive',
         'PendingSubmit', 'PendingCancel', 'PreSubmitted',)

    def push_orderstatus(self, msg):
        # Cancelled 以及 Filled = 0 的 Submitted 可立即推送
        try:
            order = self.orderbyid[msg.orderId]
        except KeyError:
            return  # 未找到，不是当前 order

        if msg.status == self.SUBMITTED and msg.filled == 0:
            if order.status == order.Accepted:  # 重复检测
                return

            order.accept(self)
            self.notify(order)

        elif msg.status == self.CANCELLED:
            # 重复检测
            if order.status in [order.Cancelled, order.Expired]:
                return

            if order._willexpire:
                # openOrder 曾出现 PendingCancel/Cancelled，这通常发生于 order 过期
                order.expire()
            else:
                # 纯用户取消不会出现 openOrder
                order.cancel()
            self.notify(order)

        elif msg.status == self.PENDINGCANCEL:
            # 按文档理论上不应看到该消息，但 demo 中收到过类似文档描述的 PENDINGSUBMIT
            if order.status == order.Cancelled:  # 重复检测
                return

            # 这里不处理；若未看到 CANCELLED orderStatus，会由 202 error code 处理
            # order.cancel()
            # self.notify(order)

        elif msg.status == self.INACTIVE:
            # 该状态较复杂：demo 中观察到它会导致 order rejection；但文档说明原因很多，
            # 且看起来也可能重新激活。
            if order.status == order.Rejected:  # 重复检测
                return

            order.reject(self)
            self.notify(order)

        elif msg.status in [self.SUBMITTED, self.FILLED]:
            # 这两个状态会暂存在 order 中，直到 execdetails 与 commission 都到位。
            # commission 通常最后到达。
            self.ordstatus[msg.orderId][msg.filled] = msg

        elif msg.status in [self.PENDINGSUBMIT, self.PRESUBMITTED]:
            # 文档说这些状态只能由程序员设置，但 demo account 曾随机带着 "filled" 返回它们
            if msg.filled:
                self.ordstatus[msg.orderId][msg.filled] = msg
        else:  # 未知状态
            pass

    def push_execution(self, ex):
        self.executions[ex.m_execId] = ex

    def push_commissionreport(self, cr):
        with self._lock_orders:
            ex = self.executions.pop(cr.m_execId)
            oid = ex.m_orderId
            order = self.orderbyid[oid]
            ostatus = self.ordstatus[oid].pop(ex.m_cumQty)

            position = self.getposition(order.data, clone=False)
            pprice_orig = position.price
            size = ex.m_shares if ex.m_side[0] == 'B' else -ex.m_shares
            price = ex.m_price
            # 是否应使用 pseudoupdate，并让 updateportfolio 做真实更新？
            psize, pprice, opened, closed = position.update(size, price)

            # 在 closed/opened 之间拆分 commission
            comm = cr.m_commission
            closedcomm = comm * closed / size
            openedcomm = comm - closedcomm

            comminfo = order.comminfo
            closedvalue = comminfo.getoperationcost(closed, pprice_orig)
            openedvalue = comminfo.getoperationcost(opened, price)

            # m_pnl 默认值为 MAXFLOAT
            pnl = cr.m_realizedPNL if closed else 0.0

            # 内部 broker 计算应得到相同结果
            # pnl = comminfo.profitandloss(-closed, pprice_orig, price)

            # 使用 execution 对象提供的真实时间。
            # TWS 报告使用实际本地时间，而不是 data 的 timezone。
            dt = date2num(datetime.strptime(ex.m_time, '%Y%m%d  %H:%M:%S'))

            # 需要模拟 margin，但实际由真实 broker 控制，因此这里不起决定作用。
            # 使用当前 item price 作为 margin。
            margin = order.data.close[0]

            order.execute(dt, size, price,
                          closed, closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          margin, pnl,
                          psize, pprice)

            if ostatus.status == self.FILLED:
                order.completed()
                self.ordstatus.pop(oid)  # 没有剩余内容需要报告
            else:
                order.partial()

            if oid not in self.tonotify:  # 需要锁
                self.tonotify.append(oid)

    def push_portupdate(self):
        # IBStore 收到 Portfolio update 时会调用该方法。如果一个 order 的 execution
        # 被拆成多笔，updatePortfolio 消息会穿插到达；这里将其作为 strategy 可被通知的信号。
        with self._lock_orders:
            while self.tonotify:
                oid = self.tonotify.popleft()
                order = self.orderbyid[oid]
                self.notify(order)

    def push_ordererror(self, msg):
        with self._lock_orders:
            try:
                order = self.orderbyid[msg.id]
            except (KeyError, AttributeError):
                return  # error 中没有 order 或 id

            if msg.errorCode == 202:
                if not order.alive():
                    return
                order.cancel()

            elif msg.errorCode == 201:  # rejected
                if order.status == order.Rejected:
                    return
                order.reject()

            else:
                order.reject()  # 其他情况默认 reject

            self.notify(order)

    def push_orderstate(self, msg):
        with self._lock_orders:
            try:
                order = self.orderbyid[msg.orderId]
            except (KeyError, AttributeError):
                return  # error 中没有 order 或 id

            if msg.orderState.m_status in ['PendingCancel', 'Cancelled',
                                           'Canceled']:
                # 这很可能来自 expiration
                order._willexpire = True
