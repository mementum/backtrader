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
from datetime import date, datetime, timedelta
import threading

from backtrader import BrokerBase, Order, BuyOrder, SellOrder
from backtrader.comminfo import CommInfoBase
from backtrader.feed import DataBase
from backtrader.metabase import MetaParams
from backtrader.position import Position
from backtrader.utils.py3 import with_metaclass

from backtrader.stores import vcstore


class VCCommInfo(CommInfoBase):
    '''
    VisualChart 不通过 Trader interface 提供 commission，但 ``Strategy`` 中的
    trade 计算依赖 order 携带 CommInfo 对象，以计算操作成本和价值。

    这些信息不是核心执行路径，但移除可能破坏既有用法，因此提供一个可近似完成计算的
    CommInfo 对象。

    margin 不是预先已知的信息，因此这里保留近似计算。
    '''

    def getvaluesize(self, size, price):
        # 实盘中 margin 接近 price
        return abs(size) * price

    def getoperationcost(self, size, price):
        '''返回一次操作需要占用的 cash 数量。'''
        # 与上方逻辑相同
        return abs(size) * price


class MetaVCBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，执行 broker 注册。'''
        # 初始化类
        super(MetaVCBroker, cls).__init__(name, bases, dct)
        vcstore.VCStore.BrokerCls = cls


class VCBroker(with_metaclass(MetaVCBroker, BrokerBase)):
    '''VisualChart 的 broker 实现。

    该类将 VisualChart 的 order/position 映射到 ``backtrader`` 内部 API。

    Args:
        account: VisualChart 可同时支持多个 broker account。默认 ``None`` 时使用
            ComTrader ``Accounts`` collection 中的第 1 个 account；如果传入 account
            名称，则在 collection 中查找并使用。
        commission: commission scheme。未传入时会自动生成一个近似对象。

    Returns:
        VCBroker: 用于连接 VisualChart store 并处理 order/position 的 broker。

    注意：
      - Position

        VisualChart 通过 ComTrader interface 报告 "OpenPositions" 更新，但只在
        position 有 size 时报告。position 回到 ZERO 时表现为该 position 缺失，
        因此需要像模拟 broker 一样通过执行事件维护 position accounting。

      - Commission

        VisualChart 的 ComTrader interface 不报告 commissions。若需要精确 commission，
        需要通过 ``commission`` 参数传入合适的 commission scheme。

      - Expiration Timing

        ComTrader interface（或 comtypes 模块）会丢弃 ``datetime`` 对象中的
        ``time`` 信息，因此 expiration date 总是完整日期。

      - Expiration Reporting

        当前没有启发式逻辑判断 cancelled order 是否因 expiration 被取消，因此 expired
        order 会按 cancelled 报告。
    '''
    params = (
        ('account', None),
        ('commission', None),
    )

    def __init__(self, **kwargs):
        super(VCBroker, self).__init__()

        self.store = vcstore.VCStore(**kwargs)

        # Account 数据
        self._acc_name = None
        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0

        # Position accounting
        self._lock_pos = threading.Lock()  # 同步 account 更新
        self.positions = collections.defaultdict(Position)  # 实际 position

        # Order 存储
        self._lock_orders = threading.Lock()  # 控制访问
        self.orderbyid = dict()  # 按 order id 保存 order

        # 通知
        self.notifs = collections.deque()

        # order 映射所需的取值字典
        self._otypes = {
            Order.Market: self.store.vcctmod.OT_Market,
            Order.Close: self.store.vcctmod.OT_Market,
            Order.Limit: self.store.vcctmod.OT_Limit,
            Order.Stop: self.store.vcctmod.OT_StopMarket,
            Order.StopLimit: self.store.vcctmod.OT_StopLimit,
        }

        self._osides = {
            Order.Buy: self.store.vcctmod.OS_Buy,
            Order.Sell: self.store.vcctmod.OS_Sell,
        }

        self._otrestriction = {
            Order.T_None: self.store.vcctmod.TR_NoRestriction,
            Order.T_Date: self.store.vcctmod.TR_Date,
            Order.T_Close: self.store.vcctmod.TR_CloseAuction,
            Order.T_Day: self.store.vcctmod.TR_Session,
        }

        self._ovrestriction = {
            Order.V_None: self.store.vcctmod.VR_NoRestriction,
        }

        self._futlikes = (
            self.store.vcdsmod.IT_Future, self.store.vcdsmod.IT_Option,
            self.store.vcdsmod.IT_Fund,
        )

    def start(self):
        super(VCBroker, self).start()
        self.store.start(broker=self)

    def stop(self):
        super(VCBroker, self).stop()
        self.store.stop()

    def getcash(self):
        # 如果 VisualChart 暂无响应，此调用不能阻塞
        return self.cash

    def getvalue(self, datas=None):
        return self.value

    def get_notification(self):
        return self.notifs.popleft()  # 至少存在一个 None

    def notify(self, order):
        self.notifs.append(order.clone())

    def next(self):
        self.notifs.append(None)  # 标记通知边界

    def getposition(self, data, clone=True):
        with self._lock_pos:
            pos = self.positions[data._tradename]
            if clone:
                return pos.clone()

        return pos

    def getcommissioninfo(self, data):
        if data._tradename in self.comminfo:
            return self.comminfo[data._tradename]

        comminfo = self.comminfo[None]
        if comminfo is not None:
            return comminfo

        stocklike = data._syminfo.Type in self._futlikes

        return VCCommInfo(mult=data._syminfo.PointValue, stocklike=stocklike)

    def _makeorder(self, ordtype, owner, data,
                   size, price=None, plimit=None,
                   exectype=None, valid=None,
                   tradeid=0, **kwargs):

        order = self.store.vcctmod.Order()
        order.Account = self._acc_name
        order.SymbolCode = data._tradename
        order.OrderType = self._otypes[exectype]
        order.OrderSide = self._osides[ordtype]

        order.VolumeRestriction = self._ovrestriction[Order.V_None]
        order.HideVolume = 0
        order.MinVolume = 0

        # order.UserName = 'danjrod'  # str(tradeid)
        # order.OrderId = 'a' * 50  # str(tradeid)
        order.UserOrderId = ''
        if tradeid:
            order.ExtendedInfo = 'TradeId {}'.format(tradeid)
        else:
            order.ExtendedInfo = ''

        order.Volume = abs(size)

        order.StopPrice = 0.0
        order.Price = 0.0
        if exectype == Order.Market:
            pass
        elif exectype == Order.Limit:
            order.Price = price or plimit  # cover naming confusion cases
        elif exectype == Order.Close:
            pass
        elif exectype == Order.Stop:
            order.StopPrice = price
        elif exectype == Order.StopLimit:
            order.StopPrice = price
            order.Price = plimit

        order.ValidDate = None
        if exectype == Order.Close:
            order.TimeRestriction = self._otrestriction[Order.T_Close]
        else:
            if valid is None:
                order.TimeRestriction = self._otrestriction[Order.T_None]
            elif isinstance(valid, (datetime, date)):
                order.TimeRestriction = self._otrestriction[Order.T_Date]
                order.ValidDate = valid
            elif isinstance(valid, (timedelta,)):
                if valid == Order.DAY:
                    order.TimeRestriction = self._otrestriction[Order.T_Day]
                else:
                    order.TimeRestriction = self._otrestriction[Order.T_Date]
                    order.ValidDate = datetime.now() + valid

            elif not self.valid:  # DAY
                order.TimeRestriction = self._otrestriction[Order.T_Day]

        # 支持自定义用户参数
        for k in kwargs:
            if hasattr(order, k):
                setattr(order, k, kwargs[k])

        return order

    def submit(self, order, vcorder):
        order.submit(self)

        vco = vcorder
        oid = self.store.vcct.SendOrder(
            vco.Account, vco.SymbolCode,
            vco.OrderType, vco.OrderSide, vco.Volume, vco.Price, vco.StopPrice,
            vco.VolumeRestriction, vco.TimeRestriction,
            ValidDate=vco.ValidDate
        )

        order.vcorder = oid
        order.addcomminfo(self.getcommissioninfo(order.data))

        with self._lock_orders:
            self.orderbyid[oid] = order
        self.notify(order)
        return order

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0,
            **kwargs):

        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)

        vcorder = self._makeorder(order.ordtype, owner, data, size, price,
                                  plimit, exectype, valid, tradeid,
                                  **kwargs)

        return self.submit(order, vcorder)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0,
             **kwargs):

        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)

        vcorder = self._makeorder(order.ordtype, owner, data, size, price,
                                  plimit, exectype, valid, tradeid,
                                  **kwargs)

        return self.submit(order, vcorder)

    #
    # COM Events 实现
    #
    def __call__(self, trader):
        # 在子线程中调用以启动流程；该线程中只能使用传入的 trader
        self.trader = trader

        for acc in trader.Accounts:
            if self.p.account is None or self.p.account == acc.Account:
                self.startingcash = self.cash = acc.Balance.Cash
                self.startingvalue = self.value = acc.Balance.NetWorth
                self._acc_name = acc.Account
                break  # 找到 account

        return self

    def OnChangedBalance(self, Account):
        if self._acc_name is None or self._acc_name != Account:
            return  # 跳过其他 account 的通知

        for acc in self.trader.Accounts:
            if acc.Account == Account:
                # 更新 store 值
                self.cash = acc.Balance.Cash
                self.value = acc.Balance.NetWorth
                break

    def OnModifiedOrder(self, Order):
        # 当前不预期该事件；除非 backtrader 开始实现 modify order 方法
        pass

    def OnCancelledOrder(self, Order):
        with self._lock_orders:
            try:
                border = self.orderbyid[Order.OrderId]
            except KeyError:
                return  # 可能是外部 order

        border.cancel()
        self.notify(border)

    def OnTotalExecutedOrder(self, Order):
        self.OnExecutedOrder(Order, partial=False)

    def OnPartialExecutedOrder(self, Order):
        self.OnExecutedOrder(Order, partial=True)

    def OnExecutedOrder(self, Order, partial):
        with self._lock_orders:
            try:
                border = self.orderbyid[Order.OrderId]
            except KeyError:
                return  # 可能是外部 order

        price = Order.Price
        size = Order.Volume
        if border.issell():
            size *= -1

        # 找到 position 并进行真实更新，accounting 在这里发生
        position = self.getposition(border.data, clone=False)
        pprice_orig = position.price
        psize, pprice, opened, closed = position.update(size, price)

        comminfo = border.comminfo
        closedvalue = comminfo.getoperationcost(closed, pprice_orig)
        closedcomm = comminfo.getcommission(closed, price)

        openedvalue = comminfo.getoperationcost(opened, price)
        openedcomm = comminfo.getcommission(opened, price)

        pnl = comminfo.profitandloss(-closed, pprice_orig, price)
        margin = comminfo.getvaluesize(size, price)

        # 注意：Trader interface 无 commission 信息
        # 待确认：是否使用报告时间，而不是最后一个 data 时间？
        border.execute(border.data.datetime[0],
                       size, price,
                       closed, closedvalue, closedcomm,
                       opened, openedvalue, openedcomm,
                       margin, pnl,
                       psize, pprice)  # pnl

        if partial:
            border.partial()
        else:
            border.completed()

        self.notify(border)

    def OnOrderInMarket(self, Order):
        # order 已进入市场，因此视为 accepted
        with self._lock_orders:
            try:
                border = self.orderbyid[Order.OrderId]
            except KeyError:
                return  # 可能是外部 order

        border.accept()
        self.notify(border)

    def OnNewOrderLocation(self, Order):
        # 可用于 "submitted"，但当前 status 是手动设置的
        pass

    def OnChangedOpenPositions(self, Account):
        # 如果该事件报告 position 回到 0 会很有用；但实际报告中缺少该 position，
        # 对 accounting 无帮助。因此 accounting 委托给 order execution 接收逻辑。
        pass

    def OnNewClosedOperations(self, Account):
        # 尚未观察到该 callback
        pass

    def OnServerShutDown(self):
        pass

    def OnInternalEvent(self, p1, p2, p3):
        pass
