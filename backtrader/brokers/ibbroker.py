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
import copy

import ib.ext.Order
import ib.opt as ibopt

from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num, BrokerBase, Order, OrderData
from backtrader.utils.py3 import bytes, with_metaclass, queue
from backtrader.metabase import MetaParams
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import ibstore
from backtrader.utils import AutoOrderedDict


class _ExecInfo(object):

    # ('execution', 'orderstate', 'orderstatus', 'comissionreport'))
    # OrderState doesn't help due to the repetition and overlapping
    # informations
    _dfields = {n: i for i, n in enumerate(
        ('execution', 'orderstatus', 'comissionreport'))
    }

    def __init__(self):
        self.clear()

    def __bool__(self):
        return all(self._fields)  # any None will force a False

    __nonzero__ = __bool__

    def clear(self):
        self._fields = [None] * len(self._dfields)

    def __len__(self):
        return len(self._dfields)

    def __getitem__(self, key):
        return self._fields[key]

    def __setitem__(self, key, val):
        self._fields[key] = val

    def __iter__(self):
        return iter(self._fields)

    def full(self):
        return bool(self)

    def __setattr__(self, name, val):
        if name.startswith('_'):
            super(_ExecInfo, self).__setattr__(name, val)
        else:
            self._fields[self._dfields[name]] = val

    def __getattr__(self, name):
        return self._fields[self._dfields[name]]


class IBOrder(ib.ext.Order.Order):

    def __init__(self, *args, **kwargs):
        super(IBOrder, self).__init__(*args, **kwargs)
        self.info = AutoOrderedDict()

        self.ostatus = collections.OrderedDict()
        self.execs = collections.OrderedDict()

    def addinfo(self, **kwargs):
        '''Add the keys, values of kwargs to the internal info dictionary to
        hold custom information in the order'''
        for key, val in iteritems(kwargs):
            self.info[key] = val

    # Subclass to provide the needed methods used inside the platform
    def isbuy(self):
        return self.m_action == 'BUY'

    def issell(self):
        return self.m_action == 'SELL'

    def alive(self):
        return self.status in [Order.Created, Order.Submitted,
                               Order.Partial, Order.Accepted]

    def getstatusname(self, status):
        Status = [
            'Created', 'Submitted', 'Accepted', 'Partial',
            'Completed', 'Canceled', 'Expired', 'Margin'
        ]
        return Status[status]

    def clone(self):
        obj = copy.copy(self)
        obj.executed = copy.deepcopy(self.executed)
        return obj


class MetaIBBroker(MetaParams):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaIBBroker, cls).__init__(name, bases, dct)

        ibstore.IBStore.BrokerCls = cls


class IBBroker(with_metaclass(MetaIBBroker, BrokerBase)):
    '''Broker implementation for Interactive Brokers.

    This class maps the orders/positions from Interactive Brokers to the
    internal API of ``backtrader``.

    Params:

      - ``comission`` (default: CommInfoBase(percabs=True))
        The user's commission in Interactive Brokers is not known so a
        commission scheme with null comissions is applied (the system needs
        one)

        It can be replaced by the end user during instantiation or later with
        the methods:

          - addcommission
          - setcomission

    Differences:

      - ``commissions`` and ``positions``: order status updates (including
        execution) from ib don't carry commission information or profit and
        loss. Accumulated profit and loss is sent back portfolio
        updates. ``backtrader`` tries to keep positions in sync by checking
        each order status updates.

        This would affect the calculations for "trades"
    '''
    params = ()

    def __init__(self, **kwargs):
        super(IBBroker, self).__init__()

        self.ib = ibstore.IBStore(**kwargs)

        self.orderbyid = collections.OrderedDict()
        self.executions = dict()
        self.notifs = queue.Queue()

    def start(self):
        super(IBBroker, self).start()
        self.ib.start(broker=self)

        if self.ib.connected():
            self.ib.reqAccountUpdates()
            self.startingcash = self.cash = self.ib.get_acc_cash()
            self.startingvalue = self.value = self.ib.get_acc_value()

    def stop(self):
        super(IBBroker, self).stop()
        self.ib.disconnect()

    def getcash(self):
        self.cash = self.ib.get_acc_cash()
        return self.cash

    def getvalue(self, datas=None):
        self.value = self.ib.get_acc_value()
        return self.value

    def getposition(self, data):
        return self.ib.getposition(data.contract)

    def cancel(self, order):
        try:
            o = self.orderbyid[order.m_orderId]
        except (ValueError, KeyError):
            return  # not found ... not cancellable

        if order.status == Order.Cancelled:  # already cancelled
            return

        self.ib.cancelOrder(order.m_orderId)

    def orderstatus(self, order):
        try:
            o = self.orderbyid[order.m_orderId]
        except (ValueError, KeyError):
            o = order

        return o.status

    def submit(self, order):
        order.plen = len(order.data)
        order.status = Order.Created

        self.orderbyid[order.m_orderId] = order
        self.ib.placeOrder(order.m_orderId, order.data.contract, order)
        self.notify(order)

        return order

    _OrdTypes = {
        None: bytes('MKT'),  # default
        Order.Market: bytes('MKT'),
        Order.Limit: bytes('LMT'),
        Order.Close: bytes('MOC'),
        Order.Stop: bytes('STP'),
        Order.StopLimit: bytes('STPLMT'),
    }

    def _makeorder(self,
                   owner, data, size, price=None, plimit=None, exectype=None,
                   valid=None, tradeid=0, **kwargs):

        order = IBOrder()

        # Keep some data as attributes
        order.data = data
        order.owner = owner
        order.tradeid = owner
        order.comminfo = self.getcommissioninfo(data)

        if exectype == Order.Market and price is None:
            price = data.close[0]

        order.created = OrderData(dt=data.datetime[0],
                                  size=size,
                                  price=price,
                                  pricelimit=plimit)

        order.executed = OrderData(remsize=size)

        # Ids
        order.m_orderId = self.ib.nextOrderId()
        order.ref = order.m_orderId  # internal backtraderfield

        order.m_clientId = self.ib.clientId
        order.m_permid = 0

        order.m_lmtPrice = 0.0
        order.m_auxPrice = 0.0

        if exectype == Order.Market:  # is it really needed for Market?
            order.m_lmtPrice = price
            order.m_auxPrice = price
        elif exectype == Order.Close:  # is it ireally needed for Close?
            order.m_lmtPrice = price
            order.m_auxPrice = price
        elif exectype == Order.Limit:
            order.m_lmtPrice = price
        elif exectype == Order.Stop:
            order.m_auxPrice = price  # stop price / exec is market
        elif exectype == Order.StopLimit:
            order.m_lmtPrice = plimit  # req limit execution
            order.m_auxPrice = price  # trigger price

        order.m_orderType = self._OrdTypes[exectype]

        order.m_totalQuantity = size

        # Time In Force: DAY, GTC, IOC, GTD
        order.m_tif = bytes('DAY')

        order.m_transmit = True

        # pass any customer arguments to the order
        for k in kwargs:
            setattr(order, 'm_' + k, kwargs[k])

        return order

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0,
            **kwargs):

        order = self._makeorder(
            owner, data, size, price, plimit, exectype, valid, tradeid,
            **kwargs)
        order.m_action = bytes('BUY')

        return self.submit(order)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0,
             **kwargs):

        order = self._makeorder(
            owner, data, size, price, plimit, exectype, valid, tradeid,
            **kwargs)
        order.m_action = bytes('SELL')

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
        while True:
            msg = self.ib.get_orderstatus()
            if msg is None:
                break
            self._next_orderstatus(msg)

    def _next_orderstatus(self, msg):
        try:
            order = self.orderbyid[msg.orderId]
        except KeyError:
            return

        # Order statuses in msg
        SUBMITTED, FILLED, CANCELLED = 'Submitted', 'Filled', 'Cancelled'

        if msg.status == SUBMITTED and msg.filled == 0:
            if order.status == Order.Submitted:  # duplicate detection
                return

            order.status = Order.Accepted
            self.notify(order)

        elif msg.status == CANCELLED:
            if order.status == Order.Cancelled:  # duplicate detection
                return

            order.status = Order.Cancelled
            self.notify(order)

        elif msg.status == SUBMITTED:  # filled != 0
            if order.status == Order.Partial and \
               order.executed.remsize == msg.remaining:
                    return  # duplicate detected

            # FIXME: Await commissionreport

            self._order_execute(msg, order)
            order.status = Order.Partial

        elif msg.status == FILLED:
            if order.status == Order.Completed:  # duplicate detection
                return

            self._order_execute(msg, order)
            order.status = Order.Completed

        self.notify(order)

    def _order_execute(self, msg, order):
        comminfo = order.comminfo
        position = self.getposition(order.data)

        signsize = -1 if order.m_action == 'SELL' else 1

        exsize = order.executed.remsize - msg.remaining
        exprice = msg.lastFillPrice

        psize, pprice = position.size, position.price
        pprice_orig = position.price_orig
        opened, closed = position.upopened, position.upclosed

        pnl = comminfo.profitandloss(-closed, pprice_orig, exprice)

        if closed:
            closedvalue = comminfo.getoperationcost(closed, pprice_orig)
            closedcomm = comminfo.getcommission(closed, exprice)
        else:
            closedvalue = closedcomm = 0.0

        if opened:
            openedvalue = comminfo.getoperationcost(opened, exprice)
            openedcomm = comminfo.getcommission(opened, exprice)
        else:
            openedvalue = openedcomm = 0.0

        order.executed.add(order.data.datetime[0],
                           exsize, exprice,
                           closed, closedvalue, closedcomm,
                           opened, openedvalue, openedcomm,
                           pnl, psize, pprice)

        order.executed.margin = comminfo.margin

        # order.executed.size = msg.filled
        # order.executed.remsize = msg.remaining
        # order.executed.price = msg.avgFillPrice

    # Order statuses in msg
    SUBMITTED, FILLED, CANCELLED = 'Submitted', 'Filled', 'Cancelled'

    def push_orderstatus(self, msg):
        # Cancelled and Submitted with Filled = 0 can be pushed immediately
        try:
            order = self.orderbyid[msg.orderId]
        except KeyError:
            return

        if msg.status == SUBMITTED and msg.filled == 0:
            if order.status == Order.Accepted:  # duplicate detection
                return

            order.status = Order.Accepted
            self.notify(order)

        elif msg.status == CANCELLED:
            if order.status == Order.Cancelled:  # duplicate detection
                return

            order.status = Order.Cancelled
            self.notify(order)

        elif msg.status in [self.SUBMITTED, self.FILLED]:
            # These two are kept inside the order until execdetails and
            # commission are all in place - commission is the last to come
            order.ostatus[msg.filled] = msg
        else:  # Unknown status ...
            pass

    def push_execution(self, ex):
        self.executions[ex.m_execId] = ex

    def push_commissionreport(self, cr):
        ex = self.executions[cr.m_execId]
        order = self.orderbyid[ex.m_orderId]
        ostatus = order.ostatus[ex.m_cumQty]  # orderstatus.filled

        pos = self.getposition(order.data)
        psize, pprice, opened, closed = pos.update(ex.m_shares, ex.m_price)
