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
import datetime

import backtrader as bt
from backtrader.comminfo import CommInfoBase
from backtrader.order import Order, BuyOrder, SellOrder
from backtrader.position import Position
from backtrader.utils.py3 import string_types, integer_types

__all__ = ['BackBroker', 'BrokerBack']


class BackBroker(bt.BrokerBase):
    '''Broker 模拟器。

      该模拟器支持不同 order type，会用当前 cash 检查已提交 order 的资金需求，
      在 ``cerebro`` 每次迭代中跟踪 cash/value，并维护不同 data 上的当前 position。

      对 ``futures`` 这类 instrument，价格变化在真实 broker 中会增加/减少 cash，
      因此 *cash* 会在每次迭代中调整。

      支持的 order type:

        - ``Market``: 使用下一根 bar 的第一个 tick（即 ``open`` price）执行。

        - ``Close``: 面向 intraday，使用 session 最后一根 bar 的 close price 执行。

        - ``Limit``: 当 session 内出现给定 limit price 时执行。

        - ``Stop``: 当出现给定 stop price 时执行 ``Market`` order。

        - ``StopLimit``: 当出现给定 stop price 时触发 ``Limit`` order。

      因为 broker 由 ``Cerebro`` 实例化，通常没有必要替换 broker 实例，所以参数不是
      直接由用户控制。需要修改时有两种方式：

        1. 用期望参数手动创建该类实例，并使用 ``cerebro.broker = instance`` 将其设为
           ``run`` 执行使用的 broker。

        2. 使用 ``set_xxx`` 设置值，例如 ``cerebro.broker.set_xxx``，其中 ``xxx``
           是要设置的参数名。

        .. note::

           ``cerebro.broker`` 是由 ``Cerebro`` 的 ``getbroker`` 和 ``setbroker``
           方法支持的 *property*。

      Args:

        - ``cash``: 起始 cash。

        - ``commission``: 适用于所有资产的基础 commission scheme。

        - ``checksubmit``: 在接受 order 进入系统前检查 margin/cash。

        - ``eosbar``: 对 intraday bar，将 ``time`` 等于 session end 的 bar 视为
          session end。很多交易所会在 session end 后几分钟生成 final auction bar，
          因此默认不启用。

        - ``filler`` (default: ``None``)

          一个签名为 ``callable(order, price, ago)`` 的 callable。

            - ``order``: 正在执行的 order。可通过它访问 *data*（以及其中的
              *ohlc* 和 *volume* 值）、*execution type*、剩余 size
              （``order.executed.remsize``）等信息。

              ``Order`` 实例中可用的属性和方法请参考 ``Order`` 文档。

            - ``price``: order 将在 ``ago`` 对应 bar 上执行的 price。

            - ``ago``: 与 ``order.data`` 配合使用的索引，用于提取 *ohlc* 和
              *volume*。多数情况下为 ``0``；``Close`` order 的一个边界场景下为
              ``-1``。

              例如获取 bar volume 可写为：``volume = order.data.volume[ago]``。

          callable 必须返回 *executed size*（值需 >= 0）。

          callable 也可以是实现了上述 ``__call__`` 签名的对象。

          默认 ``None`` 时，order 会一次性完整执行。

        - ``slip_perc`` (default: ``0.0``): 以绝对百分比表示的正数，用于对
          buy/sell order 的 price 向上/向下做 slippage。

          注意：

            - ``0.01`` is ``1%``

            - ``0.001`` is ``0.1%``

        - ``slip_fixed`` (default: ``0.0``): 以价格单位表示的正数，用于对
          buy/sell order 的 price 向上/向下做 slippage。

          注意：如果 ``slip_perc`` 非 0，它会优先于该参数。

        - ``slip_open`` (default: ``False``): 对明确使用下一根 bar *opening*
          price 执行的 order 是否应用 slippage。例如 ``Market`` order 会用下一
          个可用 tick 执行，也就是该 bar 的 opening price。

          这也适用于部分其它执行类型，因为进入新 bar 时逻辑会检测 *opening*
          price 是否满足请求的 price/execution type。

        - ``slip_match`` (default: ``True``)

          如果为 ``True``，当 slippage 超出 ``high/low`` 时，broker 会把 price
          限制在 ``high/low`` 内并提供 match。

          如果为 ``False``，broker 不会用当前 price 匹配该 order，而会在下一轮
          迭代中继续尝试执行。

        - ``slip_limit`` (default: ``True``)

          ``Limit`` order 在请求了精确 match price 时，即使 ``slip_match`` 为
          ``False`` 也会被匹配。

          该选项控制这一行为。

          如果为 ``True``，``Limit`` order 会把 price 限制在 ``limit`` /
          ``high/low`` 后进行匹配。

          如果为 ``False`` 且 slippage 超过限制，则不会 match。

        - ``slip_out`` (default: ``False``)

          即使 price 落在 ``high`` - ``low`` 范围之外，也允许提供 *slippage*。

        - ``coc`` (default: ``False``)

          *Cheat-On-Close*。通过 ``set_coc`` 将其设为 ``True`` 后，``Market``
          order 可以匹配到发出 order 的同一根 bar 的 closing price。这实际上是
          *cheating*，因为该 bar 已经 *closed*，任何 order 按正常流程都应先在下一
          根 bar 的 price 上尝试匹配。

        - ``coo`` (default: ``False``)

          *Cheat-On-Open*。通过 ``set_coo`` 将其设为 ``True`` 后，可以把
          ``Market`` order 匹配到 opening price。例如使用 ``cheat`` 为 ``True``
          的 timer，因为这种 timer 会在 broker 评估前执行。

        - ``int2pnl`` (default: ``True``)

          将产生的 interest（如果有）分配给减少 position 的操作（无论 long 还是
          short）的 profit/loss。某些场景下这并不理想，因为多个 strategy 可能竞争，
          interest 会以非确定方式分配给其中任意一个。

        - ``shortcash`` (default: ``True``)

          如果为 ``True``，做空 stocklike asset 时 cash 会增加，该 asset 的计算
          value 为负。

          如果为 ``False``，cash 会作为操作成本扣除，计算 value 为正，最终总金额
          保持一致。

        - ``fundstartval`` (default: ``100.0``)

          该参数控制以类似 fund 的方式衡量 performance 时的起始 value。也就是说，
          cash 可被增加或扣除，并相应改变份额数量。performance 不按 portfolio 的
          net asset value 衡量，而按 fund value 衡量。

        - ``fundmode`` (default: ``False``)

          如果设为 ``True``，``TimeReturn`` 等 analyzer 可以基于 fund value 而不是
          total net asset value 自动计算 returns。

      Returns:
        BackBroker: 用于回测执行、资金核算和 order matching 的 broker。

    '''
    params = (
        ('cash', 10000.0),
        ('checksubmit', True),
        ('eosbar', False),
        ('filler', None),
        # slippage 选项
        ('slip_perc', 0.0),
        ('slip_fixed', 0.0),
        ('slip_open', False),
        ('slip_match', True),
        ('slip_limit', True),
        ('slip_out', False),
        ('coc', False),
        ('coo', False),
        ('int2pnl', True),
        ('shortcash', True),
        ('fundstartval', 100.0),
        ('fundmode', False),
    )

    def __init__(self):
        super(BackBroker, self).__init__()
        self._userhist = []
        self._fundhist = []
        # share_value, net asset value（净资产 value）
        self._fhistlast = [float('NaN'), float('NaN')]

    def init(self):
        super(BackBroker, self).init()
        self.startingcash = self.cash = self.p.cash
        self._value = self.cash
        self._valuemkt = 0.0  # 无 open position

        self._valuelever = 0.0  # 无 open position
        self._valuemktlever = 0.0  # 无 open position

        self._leverage = 1.0  # 初始没有 open position
        self._unrealized = 0.0  # 无 open position

        self.orders = list()  # 只会 append
        self.pending = collections.deque()  # popleft and append(right)
        self._toactivate = collections.deque()  # 下一轮需要 activate

        self.positions = collections.defaultdict(Position)
        self.d_credit = collections.defaultdict(float)  # 每个 data 的 credit
        self.notifs = collections.deque()

        self.submitted = collections.deque()

        # 按需保存依赖 order
        self._pchildren = collections.defaultdict(collections.deque)

        self._ocos = dict()
        self._ocol = collections.defaultdict(list)

        self._fundval = self.p.fundstartval
        self._fundshares = self.p.cash / self._fundval
        self._cash_addition = collections.deque()

    def get_notification(self):
        try:
            return self.notifs.popleft()
        except IndexError:
            pass

        return None

    def set_fundmode(self, fundmode, fundstartval=None):
        '''设置当前 fundmode（True 或 False）。

        如果 ``fundstartval`` 不是 ``None``，会同步设置起始 fund value。
        '''
        self.p.fundmode = fundmode
        if fundstartval is not None:
            self.set_fundstartval(fundstartval)

    def get_fundmode(self):
        '''返回当前 fundmode（True 或 False）。'''
        return self.p.fundmode

    fundmode = property(get_fundmode, set_fundmode)

    def set_fundstartval(self, fundstartval):
        '''设置 fund-like performance tracker 的起始值。'''
        self.p.fundstartval = fundstartval

    def set_int2pnl(self, int2pnl):
        '''配置是否将 interest 分配到 profit/loss。'''
        self.p.int2pnl = int2pnl

    def set_coc(self, coc):
        '''配置 Cheat-On-Close，使 Market order 可按创建 bar 的 close 执行。'''
        self.p.coc = coc

    def set_coo(self, coo):
        '''配置 Cheat-On-Open，使 Market order 可按 open 执行。'''
        self.p.coo = coo

    def set_shortcash(self, shortcash):
        '''配置 shortcash 参数。'''
        self.p.shortcash = shortcash

    def set_slippage_perc(self, perc,
                          slip_open=True, slip_limit=True,
                          slip_match=True, slip_out=False):
        '''配置基于百分比的 slippage。'''
        self.p.slip_perc = perc
        self.p.slip_fixed = 0.0
        self.p.slip_open = slip_open
        self.p.slip_limit = slip_limit
        self.p.slip_match = slip_match
        self.p.slip_out = slip_out

    def set_slippage_fixed(self, fixed,
                           slip_open=True, slip_limit=True,
                           slip_match=True, slip_out=False):
        '''配置基于固定点数的 slippage。'''
        self.p.slip_perc = 0.0
        self.p.slip_fixed = fixed
        self.p.slip_open = slip_open
        self.p.slip_limit = slip_limit
        self.p.slip_match = slip_match
        self.p.slip_out = slip_out

    def set_filler(self, filler):
        '''设置用于 volume filling execution 的 volume filler。'''
        self.p.filler = filler

    def set_checksubmit(self, checksubmit):
        '''设置 checksubmit 参数。'''
        self.p.checksubmit = checksubmit

    def set_eosbar(self, eosbar):
        '''设置 eosbar 参数（别名：``seteosbar``）。'''
        self.p.eosbar = eosbar

    seteosbar = set_eosbar

    def get_cash(self):
        '''返回当前 cash（别名：``getcash``）。'''
        return self.cash

    getcash = get_cash

    def set_cash(self, cash):
        '''设置 cash 参数（别名：``setcash``）。'''
        self.startingcash = self.cash = self.p.cash = cash
        self._value = cash

    setcash = set_cash

    def add_cash(self, cash):
        '''向系统增加/移除 cash（使用负值移除）。'''
        self._cash_addition.append(cash)

    def get_fundshares(self):
        '''返回 fund-like 模式下当前 share 数量。'''
        return self._fundshares

    fundshares = property(get_fundshares)

    def get_fundvalue(self):
        '''返回 fund-like share value。'''
        return self._fundval

    fundvalue = property(get_fundvalue)

    def cancel(self, order, bracket=False):
        try:
            self.pending.remove(order)
        except ValueError:
            # 如果列表中没有该元素，则没有取消任何内容
            return False

        order.cancel()
        self.notify(order)
        self._ococheck(order)
        if not bracket:
            self._bracketize(order, cancel=True)
        return True

    def get_value(self, datas=None, mkt=False, lever=False):
        '''返回给定 data 的 portfolio value。

        如果 ``datas`` 为 ``None``，返回总 portfolio value（别名：``getvalue``）。
        '''
        if datas is None:
            if mkt:
                return self._valuemkt if not lever else self._valuemktlever

            return self._value if not lever else self._valuelever

        return self._get_value(datas=datas, lever=lever)

    getvalue = get_value

    def get_value_lever(self, datas=None, mkt=False):
        return self.get_value(datas=datas, mkt=mkt)

    def _get_value(self, datas=None, lever=False):
        pos_value = 0.0
        pos_value_unlever = 0.0
        unrealized = 0.0

        while self._cash_addition:
            c = self._cash_addition.popleft()
            self._fundshares += c / self._fundval
            self.cash += c

        for data in datas or self.positions:
            comminfo = self.getcommissioninfo(data)
            position = self.positions[data]
            # 使用 valuesize：返回原始 value，而不是负的调整 value
            if not self.p.shortcash:
                dvalue = comminfo.getvalue(position, data.close[0])
            else:
                dvalue = comminfo.getvaluesize(position.size, data.close[0])

            dunrealized = comminfo.profitandloss(position.size, position.price,
                                                 data.close[0])
            if datas and len(datas) == 1:
                if lever and dvalue > 0:
                    dvalue -= dunrealized
                    return (dvalue / comminfo.get_leverage()) + dunrealized
                return dvalue  # 请求原始 data value，short selling 为负

            if not self.p.shortcash:
                dvalue = abs(dvalue)  # 此时 short selling 会增加 value

            pos_value += dvalue
            unrealized += dunrealized

            if dvalue > 0:  # long position - unlever
                dvalue -= dunrealized
                pos_value_unlever += (dvalue / comminfo.get_leverage())
                pos_value_unlever += dunrealized
            else:
                pos_value_unlever += dvalue

        if not self._fundhist:
            self._value = v = self.cash + pos_value_unlever
            self._fundval = self._value / self._fundshares  # update fundvalue
        else:
            # 尝试获取 value
            fval, fvalue = self._process_fund_history()

            self._value = fvalue
            self.cash = fvalue - pos_value_unlever
            self._fundval = fval
            self._fundshares = fvalue / fval
            lev = pos_value / (pos_value_unlever or 1.0)

            # 将上面计算出的值更新为历史值
            pos_value_unlever = fvalue
            pos_value = fvalue * lev

        self._valuemkt = pos_value_unlever

        self._valuelever = self.cash + pos_value
        self._valuemktlever = pos_value

        self._leverage = pos_value / (pos_value_unlever or 1.0)
        self._unrealized = unrealized

        return self._value if not lever else self._valuelever

    def get_leverage(self):
        return self._leverage

    def get_orders_open(self, safe=False):
        '''返回仍处于 open 状态的 order 可迭代对象。

        包括尚未执行或部分执行的 order。返回的 order 不应被修改。

        如需操作 order，请将 ``safe`` 参数设为 True。
        '''
        if safe:
            os = [x.clone() for x in self.pending]
        else:
            os = [x for x in self.pending]

        return os

    def getposition(self, data):
        '''返回给定 ``data`` 的当前 position 状态（``Position`` 实例）。'''
        return self.positions[data]

    def orderstatus(self, order):
        try:
            o = self.orders.index(order)
        except ValueError:
            o = order

        return o.status

    def _take_children(self, order):
        oref = order.ref
        pref = getattr(order.parent, 'ref', oref)  # parent ref or self

        if oref != pref:
            if pref not in self._pchildren:
                order.reject()  # parent 不存在，可能已被 reject
                self.notify(order)  # reject 子 order 并通知
                return None

        return pref

    def submit(self, order, check=True):
        pref = self._take_children(order)
        if pref is None:  # order has not been taken
            return order

        pc = self._pchildren[pref]
        pc.append(order)  # 存入 parent/children queue

        if order.transmit:  # 若为单 order，则发送并清空 queue
            # 若为 parent-child，则发送 parent，其他保留
            rets = [self.transmit(x, check=check) for x in pc]
            return rets[-1]  # 最后一个是触发 transmission 的 order

        return order

    def transmit(self, order, check=True):
        if check and self.p.checksubmit:
            order.submit()
            self.submitted.append(order)
            self.orders.append(order)
            self.notify(order)
        else:
            self.submit_accept(order)

        return order

    def check_submitted(self):
        cash = self.cash
        positions = dict()

        while self.submitted:
            order = self.submitted.popleft()

            if self._take_children(order) is None:  # children not taken
                continue

            comminfo = self.getcommissioninfo(order.data)

            position = positions.setdefault(
                order.data, self.positions[order.data].clone())

            # 伪执行 order，以得到执行后的剩余 cash
            cash = self._execute(order, cash=cash, position=position)

            if cash >= 0.0:
                self.submit_accept(order)
                continue

            order.margin()
            self.notify(order)
            self._ococheck(order)
            self._bracketize(order, cancel=True)

    def submit_accept(self, order):
        order.pannotated = None
        order.submit()
        order.accept()
        self.pending.append(order)
        self.notify(order)

    def _bracketize(self, order, cancel=False):
        oref = order.ref
        pref = getattr(order.parent, 'ref', oref)
        parent = oref == pref

        pc = self._pchildren[pref]  # defdict，保证存在
        if cancel or not parent:  # 取消剩余 order，或子 order 执行后取消其他 order
            while pc:
                self.cancel(pc.popleft(), bracket=True)  # 幂等

            del self._pchildren[pref]  # defdict 保证存在

        else:  # 非取消 -> parent 已执行
            pc.popleft()  # 移除 parent
            for o in pc:  # activate children
                self._toactivate.append(o)

    def _ococheck(self, order):
        # ocoref = self._ocos[order.ref] or order.ref  # parent 或自身
        parentref = self._ocos[order.ref]
        ocoref = self._ocos.get(parentref, None)
        ocol = self._ocol.pop(ocoref, None)
        if ocol:
            for i in range(len(self.pending) - 1, -1, -1):
                o = self.pending[i]
                if o is not None and o.ref in ocol:
                    del self.pending[i]
                    o.cancel()
                    self.notify(o)

    def _ocoize(self, order, oco):
        oref = order.ref
        if oco is None:
            self._ocos[oref] = oref  # 当前 order 是 parent
            self._ocol[oref].append(oref)  # 创建 ocogroup
        else:
            ocoref = self._ocos[oco.ref]  # 指向 group leader
            self._ocos[oref] = ocoref  # 指向 group leader
            self._ocol[ocoref].append(oref)  # 加入 group

    def add_order_history(self, orders, notify=True):
        oiter = iter(orders)
        o = next(oiter, None)
        self._userhist.append([o, oiter, notify])

    def set_fund_history(self, fund):
        # 可迭代对象，每项格式如下
        # [datetime, share_value, net asset value]
        fiter = iter(fund)
        f = list(next(fiter))  # 不能为空
        self._fundhist = [f, fiter]
        # self._fhistlast = f[1:]

        self.set_cash(float(f[2]))

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            parent=None, transmit=True,
            histnotify=False, _checksubmit=True,
            **kwargs):

        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid,
                         trailamount=trailamount, trailpercent=trailpercent,
                         parent=parent, transmit=transmit,
                         histnotify=histnotify)

        order.addinfo(**kwargs)
        self._ocoize(order, oco)

        return self.submit(order, check=_checksubmit)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             parent=None, transmit=True,
             histnotify=False, _checksubmit=True,
             **kwargs):

        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid,
                          trailamount=trailamount, trailpercent=trailpercent,
                          parent=parent, transmit=transmit,
                          histnotify=histnotify)

        order.addinfo(**kwargs)
        self._ocoize(order, oco)

        return self.submit(order, check=_checksubmit)

    def _execute(self, order, ago=None, price=None, cash=None, position=None,
                 dtcoc=None):
        # ago = None 用作伪执行标记
        if ago is not None and price is None:
            return  # 非伪执行且无 price，则不执行

        if self.p.filler is None or ago is None:
            # order 使用完整 size 或执行伪执行
            size = order.executed.remsize
        else:
            # execution 取决于 volume filler
            size = self.p.filler(order, price, ago)
            if not order.isbuy():
                size = -size

        # 获取 data 对应的 comminfo 对象
        comminfo = self.getcommissioninfo(order.data)

        # 检查是否需要 compensate
        if order.data._compensate is not None:
            data = order.data._compensate
            cinfocomp = self.getcommissioninfo(data)  # 用于实际 commission
        else:
            data = order.data
            cinfocomp = comminfo

        # 用 operation size 调整 position
        if ago is not None:
            # 带日期的真实执行
            position = self.positions[data]
            pprice_orig = position.price

            psize, pprice, opened, closed = position.pseudoupdate(size, price)

            # 如果部分/全部 position 已关闭，则产生 profitandloss，需要记录
            pnl = comminfo.profitandloss(-closed, pprice_orig, price)
            cash = self.cash
        else:
            pnl = 0
            if not self.p.coo:
                price = pprice_orig = order.created.price
            else:
                # 使用 cheat on open 时，Market order 应考虑 opening price，
                # 而不是创建 order 时默认的 closing price
                if order.exectype == Order.Market:
                    price = pprice_orig = order.data.open[0]
                else:
                    price = pprice_orig = order.created.price

            psize, pprice, opened, closed = position.update(size, price)

        # 可全部或部分 "Closing"，cash 可能被重新注入
        if closed:
            # 按 closed item 返回值与 acquired opened item 调整
            if self.p.shortcash:
                closedvalue = comminfo.getvaluesize(-closed, pprice_orig)
            else:
                closedvalue = comminfo.getoperationcost(closed, pprice_orig)

            closecash = closedvalue
            if closedvalue > 0:  # long position closed
                closecash /= comminfo.get_leverage()  # 按 leverage 增加 cash

            cash += closecash + pnl * comminfo.stocklike
            # 计算并扣减 commission
            closedcomm = comminfo.getcommission(closed, price)
            cash -= closedcomm

            if ago is not None:
                # cashadjust closed contracts：prev close vs exec price。
                # 该操作可注入或取出 cash。
                cash += comminfo.cashadjust(-closed,
                                            position.adjbase,
                                            price)

                # 更新系统 cash
                self.cash = cash
        else:
            closedvalue = closedcomm = 0.0

        popened = opened
        if opened:
            if self.p.shortcash:
                openedvalue = comminfo.getvaluesize(opened, price)
            else:
                openedvalue = comminfo.getoperationcost(opened, price)

            opencash = openedvalue
            if openedvalue > 0:  # 正在打开 long position
                opencash /= comminfo.get_leverage()  # 按 leverage 减少 cash

            cash -= opencash  # original behavior

            openedcomm = cinfocomp.getcommission(opened, price)
            cash -= openedcomm

            if cash < 0.0:
                # cash 不足，无法执行，置空
                opened = 0
                openedvalue = openedcomm = 0.0

            elif ago is not None:  # real execution
                if abs(psize) > abs(opened):
                    # 打开了部分 futures：将既有 futures 的 cash 调整到 operation price，
                    # 并将其作为新的 adjustment base。新 futures 已经使用该 base。
                    # 周期末会基于共同 base price，对所有 open futures 按 close price 调整。
                    adjsize = psize - opened
                    cash += comminfo.cashadjust(adjsize,
                                                position.adjbase, price)

                # 记录调整价格基准，用于 bar 末 cash adjustment
                position.adjbase = price

                # 更新系统 cash，前提是 opened 仍不为 0
                self.cash = cash
        else:
            openedvalue = openedcomm = 0.0

        if ago is None:
            # 返回伪执行后的 cash
            return cash

        execsize = closed + opened

        if execsize:
            # 向 comminfo 对象确认该操作
            comminfo.confirmexec(execsize, price)

            # 如有实际执行，执行真实 position update
            position.update(execsize, price, data.datetime.datetime())

            if closed and self.p.int2pnl:  # Assign accumulated interest data
                closedcomm += self.d_credit.pop(data, 0.0)

            # 执行并通知 order
            order.execute(dtcoc or data.datetime[ago],
                          execsize, price,
                          closed, closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          comminfo.margin, pnl,
                          psize, pprice)

            order.addcomminfo(comminfo)

            self.notify(order)
            self._ococheck(order)

        if popened and not opened:
            # opened 未执行，cash 不足
            order.margin()
            self.notify(order)
            self._ococheck(order)
            self._bracketize(order, cancel=True)

    def notify(self, order):
        self.notifs.append(order.clone())

    def _try_exec_historical(self, order):
        self._execute(order, ago=0, price=order.created.price)

    def _try_exec_market(self, order, popen, phigh, plow):
        ago = 0
        if self.p.coc and order.info.get('coc', True):
            dtcoc = order.created.dt
            exprice = order.created.pclose
        else:
            if not self.p.coo and order.data.datetime[0] <= order.created.dt:
                return    # can only execute after creation time

            dtcoc = None
            exprice = popen

        if order.isbuy():
            p = self._slip_up(phigh, exprice, doslip=self.p.slip_open)
        else:
            p = self._slip_down(plow, exprice, doslip=self.p.slip_open)

        self._execute(order, ago=0, price=p, dtcoc=dtcoc)

    def _try_exec_close(self, order, pclose):
        # 如果缺少信息判断当前 bar 是否为 closing bar（例如匹配 session end bar），
        # pannotated 可用于跟踪 closing bar。
        # 实际 matching 会在下一根 bar 进行，但使用实际 closing bar 的信息。

        dt0 = order.data.datetime[0]
        # 不使用 "len"：replay 中 close 可能在相同 len 下到达
        if dt0 > order.created.dt:  # can only execute after creation time
            # or (self.p.eosbar and dt0 == order.dteos):
            if dt0 >= order.dteos:
                # 已超过 session end，或正好处于 session end 且 eosbar 为 True
                if order.pannotated and dt0 > order.dteos:
                    ago = -1
                    execprice = order.pannotated
                else:
                    ago = 0
                    execprice = pclose

                self._execute(order, ago=ago, price=execprice)
                return

        # 如果未发生 execution，记录 closing price
        order.pannotated = pclose

    def _try_exec_limit(self, order, popen, phigh, plow, plimit):
        if order.isbuy():
            if plimit >= popen:
                # open 小于/等于请求价，以更便宜价格买入
                pmax = min(phigh, plimit)
                p = self._slip_up(pmax, popen, doslip=self.p.slip_open,
                                  lim=True)
                self._execute(order, ago=0, price=p)
            elif plimit >= plow:
                # 日内 low 低于请求价，匹配 limit price
                self._execute(order, ago=0, price=plimit)

        else:  # Sell
            if plimit <= popen:
                # open 大于/等于请求价，以更高价格卖出
                pmin = max(plow, plimit)
                p = self._slip_down(plimit, popen, doslip=self.p.slip_open,
                                    lim=True)
                self._execute(order, ago=0, price=p)
            elif plimit <= phigh:
                # 日内 high 高于请求价，匹配 limit price
                self._execute(order, ago=0, price=plimit)

    def _try_exec_stop(self, order, popen, phigh, plow, pcreated, pclose):
        if order.isbuy():
            if popen >= pcreated:
                # price 通过开盘跳空穿透，使用 open
                p = self._slip_up(phigh, popen, doslip=self.p.slip_open)
                self._execute(order, ago=0, price=p)
            elif phigh >= pcreated:
                # price 在 session 中穿透，使用 trigger price
                p = self._slip_up(phigh, pcreated)
                self._execute(order, ago=0, price=p)

        else:  # Sell
            if popen <= pcreated:
                # price 通过开盘跳空穿透，使用 open
                p = self._slip_down(plow, popen, doslip=self.p.slip_open)
                self._execute(order, ago=0, price=p)
            elif plow <= pcreated:
                # price 在 session 中穿透，使用 trigger price
                p = self._slip_down(plow, pcreated)
                self._execute(order, ago=0, price=p)

        # 未完全执行且为 trailing stop
        if order.alive() and order.exectype == Order.StopTrail:
            order.trailadjust(pclose)

    def _try_exec_stoplimit(self, order,
                            popen, phigh, plow, pclose,
                            pcreated, plimit):
        if order.isbuy():
            if popen >= pcreated:
                order.triggered = True
                self._try_exec_limit(order, popen, phigh, plow, plimit)

            elif phigh >= pcreated:
                # price 在 session 中向上穿透
                order.triggered = True
                # 可为部分情况计算 execution；datetime 固定
                if popen > pclose:
                    if plimit >= pcreated:  # limit above stop trigger
                        p = self._slip_up(phigh, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)
                    elif plimit >= pclose:
                        self._execute(order, ago=0, price=plimit)
                else:  # popen < pclose
                    if plimit >= pcreated:
                        p = self._slip_up(phigh, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)
        else:  # Sell
            if popen <= pcreated:
                # price 通过开盘跳空向下穿透
                order.triggered = True
                self._try_exec_limit(order, popen, phigh, plow, plimit)

            elif plow <= pcreated:
                # price 在 session 中向下穿透
                order.triggered = True
                # 可为部分情况计算 execution；datetime 固定
                if popen <= pclose:
                    if plimit <= pcreated:
                        p = self._slip_down(plow, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)
                    elif plimit <= pclose:
                        self._execute(order, ago=0, price=plimit)
                else:
                    # popen > pclose
                    if plimit <= pcreated:
                        p = self._slip_down(plow, pcreated, lim=True)
                        self._execute(order, ago=0, price=p)

        # 未完全执行且为 trailing stop
        if order.alive() and order.exectype == Order.StopTrailLimit:
            order.trailadjust(pclose)

    def _slip_up(self, pmax, price, doslip=True, lim=False):
        if not doslip:
            return price

        slip_perc = self.p.slip_perc
        slip_fixed = self.p.slip_fixed
        if slip_perc:
            pslip = price * (1 + slip_perc)
        elif slip_fixed:
            pslip = price + slip_fixed
        else:
            return price

        if pslip <= pmax:  # slippage 可返回 price
            return pslip
        elif self.p.slip_match or (lim and self.p.slip_limit):
            if not self.p.slip_out:
                return pmax

            return pslip  # 不存在于 bar 范围内的 price

        return None  # 无可返回 price

    def _slip_down(self, pmin, price, doslip=True, lim=False):
        if not doslip:
            return price

        slip_perc = self.p.slip_perc
        slip_fixed = self.p.slip_fixed
        if slip_perc:
            pslip = price * (1 - slip_perc)
        elif slip_fixed:
            pslip = price - slip_fixed
        else:
            return price

        if pslip >= pmin:  # slippage 可返回 price
            return pslip
        elif self.p.slip_match or (lim and self.p.slip_limit):
            if not self.p.slip_out:
                return pmin

            return pslip  # 不存在于 bar 范围内的 price

        return None  # 无可返回 price

    def _try_exec(self, order):
        data = order.data

        popen = getattr(data, 'tick_open', None)
        if popen is None:
            popen = data.open[0]
        phigh = getattr(data, 'tick_high', None)
        if phigh is None:
            phigh = data.high[0]
        plow = getattr(data, 'tick_low', None)
        if plow is None:
            plow = data.low[0]
        pclose = getattr(data, 'tick_close', None)
        if pclose is None:
            pclose = data.close[0]

        pcreated = order.created.price
        plimit = order.created.pricelimit

        if order.exectype == Order.Market:
            self._try_exec_market(order, popen, phigh, plow)

        elif order.exectype == Order.Close:
            self._try_exec_close(order, pclose)

        elif order.exectype == Order.Limit:
            self._try_exec_limit(order, popen, phigh, plow, pcreated)

        elif (order.triggered and
              order.exectype in [Order.StopLimit, Order.StopTrailLimit]):
            self._try_exec_limit(order, popen, phigh, plow, plimit)

        elif order.exectype in [Order.Stop, Order.StopTrail]:
            self._try_exec_stop(order, popen, phigh, plow, pcreated, pclose)

        elif order.exectype in [Order.StopLimit, Order.StopTrailLimit]:
            self._try_exec_stoplimit(order,
                                     popen, phigh, plow, pclose,
                                     pcreated, plimit)

        elif order.exectype == Order.Historical:
            self._try_exec_historical(order)

    def _process_fund_history(self):
        fhist = self._fundhist  # [last element, iterator]
        f, funds = fhist
        if not f:
            return self._fhistlast

        dt = f[0]  # date/datetime instance
        if isinstance(dt, string_types):
            dtfmt = '%Y-%m-%d'
            if 'T' in dt:
                dtfmt += 'T%H:%M:%S'
                if '.' in dt:
                    dtfmt += '.%f'
            dt = datetime.datetime.strptime(dt, dtfmt)
            f[0] = dt  # 更新 value

        elif isinstance(dt, datetime.datetime):
            pass
        elif isinstance(dt, datetime.date):
            dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day)
            f[0] = dt  # 更新 value

        # 无法与 strategy 同步，因为 broker 在 strategy 推进前被调用。
        # 如果可行，下面两行可完成同步。
        # st0 = self.cerebro.runningstrats[0]
        # if dt <= st0.datetime.datetime():
        if dt <= self.cerebro._dtmaster:
            self._fhistlast = f[1:]
            fhist[0] = list(next(funds, []))

        return self._fhistlast

    def _process_order_history(self):
        for uhist in self._userhist:
            uhorder, uhorders, uhnotify = uhist
            while uhorder is not None:
                uhorder = list(uhorder)  # to support assignment (if tuple)
                try:
                    dataidx = uhorder[3]  # 第 2 个字段
                except IndexError:
                    dataidx = None  # 字段不存在，使用默认值

                if dataidx is None:
                    d = self.cerebro.datas[0]
                elif isinstance(dataidx, integer_types):
                    d = self.cerebro.datas[dataidx]
                else:  # 假设为 string
                    d = self.cerebro.datasbyname[dataidx]

                if not len(d):
                    break  # 可能会像其他 data feed 一样稍后开始

                dt = uhorder[0]  # date/datetime 实例
                if isinstance(dt, string_types):
                    dtfmt = '%Y-%m-%d'
                    if 'T' in dt:
                        dtfmt += 'T%H:%M:%S'
                        if '.' in dt:
                            dtfmt += '.%f'
                    dt = datetime.datetime.strptime(dt, dtfmt)
                    uhorder[0] = dt
                elif isinstance(dt, datetime.datetime):
                    pass
                elif isinstance(dt, datetime.date):
                    dt = datetime.datetime(year=dt.year,
                                           month=dt.month,
                                           day=dt.day)
                    uhorder[0] = dt

                if dt > d.datetime.datetime():
                    break  # queue 第 1 个尚不能执行，停止处理

                size = uhorder[1]
                price = uhorder[2]
                owner = self.cerebro.runningstrats[0]
                if size > 0:
                    o = self.buy(owner=owner, data=d,
                                 size=size, price=price,
                                 exectype=Order.Historical,
                                 histnotify=uhnotify,
                                 _checksubmit=False)

                elif size < 0:
                    o = self.sell(owner=owner, data=d,
                                  size=abs(size), price=price,
                                  exectype=Order.Historical,
                                  histnotify=uhnotify,
                                  _checksubmit=False)

                # 更新到下一个潜在 order
                uhist[0] = uhorder = next(uhorders, None)

    def next(self):
        while self._toactivate:
            self._toactivate.popleft().activate()

        if self.p.checksubmit:
            self.check_submitted()

        # 扣除持仓产生的 cash
        credit = 0.0
        for data, pos in self.positions.items():
            if pos:
                comminfo = self.getcommissioninfo(data)
                dt0 = data.datetime.datetime()
                dcredit = comminfo.get_credit_interest(data, pos, dt0)
                self.d_credit[data] += dcredit
                credit += dcredit
                pos.datetime = dt0  # 标记最后一次 credit 操作

        self.cash -= credit

        self._process_order_history()

        # 遍历一次 pending queue 中的所有元素
        self.pending.append(None)
        while True:
            order = self.pending.popleft()
            if order is None:
                break

            if order.expire():
                self.notify(order)
                self._ococheck(order)
                self._bracketize(order, cancel=True)

            elif not order.active():
                self.pending.append(order)  # 尚不能处理

            else:
                self._try_exec(order)
                if order.alive():
                    self.pending.append(order)

                elif order.status == Order.Completed:
                    # bracket parent order 可能已执行
                    self._bracketize(order)

        # operation 已执行，bar 末调整 cash
        for data, pos in self.positions.items():
            # futures 每根 bar 都会改变 cash
            if pos:
                comminfo = self.getcommissioninfo(data)
                self.cash += comminfo.cashadjust(pos.size,
                                                 pos.adjbase,
                                                 data.close[0])
                # 记录最后调整价格
                pos.adjbase = data.close[0]

        self._get_value()  # 更新 value


# 别名
BrokerBack = BackBroker
