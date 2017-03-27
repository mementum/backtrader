#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
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

from backtrader.feed import DataBase
from backtrader import (TimeFrame, num2date, date2num, BrokerBase,
                        Order, BuyOrder, SellOrder, OrderBase, OrderData)
from backtrader.utils.py3 import bytes, with_metaclass, MAXFLOAT
from backtrader.metabase import MetaParams
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import oandastore
from backtrader.utils import AutoDict, AutoOrderedDict
from backtrader.comminfo import CommInfoBase


class OandaCommInfo(CommInfoBase):
    def getvaluesize(self, size, price):
        # In real life the margin approaches the price
        return abs(size) * price

    def getoperationcost(self, size, price):
        '''Returns the needed amount of cash an operation would cost'''
        # Same reasoning as above
        return abs(size) * price


class MetaOandaBroker(MetaParams):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaOandaBroker, cls).__init__(name, bases, dct)
        oandastore.OandaStore.BrokerCls = cls


class OandaBroker(with_metaclass(MetaOandaBroker, BrokerBase)):
    '''Broker implementation for Oanda.

    This class maps the orders/positions from Oanda to the
    internal API of ``backtrader``.

    Params:

      - ``use_positions`` (default:``True``): When connecting to the broker
        provider use the existing positions to kickstart the broker.

        Set to ``False`` during instantiation to disregard any existing
        position
    '''
    params = (
        ('use_positions', True),
    )

    def __init__(self, **kwargs):
        super(OandaBroker, self).__init__()

        self.o = oandastore.OandaStore(**kwargs)

        self.orders = collections.OrderedDict()  # orders by order id
        self.notifs = collections.deque()  # holds orders which are notified

        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0
        self.positions = collections.defaultdict(Position)
        self.addcommissioninfo(self, OandaCommInfo(mult=1.0, stocklike=False))

    def start(self):
        super(OandaBroker, self).start()
        self.addcommissioninfo(self, OandaCommInfo(mult=1.0, stocklike=False))
        self.o.start(broker=self)
        self.startingcash = self.cash = cash = self.o.get_cash()
        self.startingvalue = self.value = self.o.get_value()

        if self.p.use_positions:
            for p in self.o.get_positions():
                print('position for instrument:', p['instrument'])
                is_sell = p['side'] == 'sell'
                size = p['units']
                if is_sell:
                    size = -size
                price = p['avgPrice']
                self.positions[p['instrument']] = Position(size, price)

    def data_started(self, data):
        pos = self.getposition(data)

        if pos.size < 0:
            order = SellOrder(data=data,
                              size=pos.size, price=pos.price,
                              exectype=Order.Market,
                              simulated=True)

            order.addcomminfo(self.getcommissioninfo(data))
            order.execute(0, pos.size, pos.price,
                          0, 0.0, 0.0,
                          pos.size, 0.0, 0.0,
                          0.0, 0.0,
                          pos.size, pos.price)

            order.completed()
            self.notify.order(order)

        elif pos.size > 0:
            order = BuyOrder(data=data,
                             size=pos.size, price=pos.price,
                             exectype=Order.Market,
                             simulated=True)

            order.addcomminfo(self.getcommissioninfo(data))
            order.execute(0, pos.size, pos.price,
                          0, 0.0, 0.0,
                          pos.size, 0.0, 0.0,
                          0.0, 0.0,
                          pos.size, pos.price)

            order.completed()
            self.notify(order)

    def stop(self):
        super(OandaBroker, self).stop()
        self.o.stop()

    def getcash(self):
        # This call cannot block if no answer is available from oanda
        self.cash = cash = self.o.get_cash()
        return cash

    def getvalue(self, datas=None):
        self.value = self.o.get_value()
        return self.value

    def getposition(self, data, clone=True):
        # return self.o.getposition(data._dataname, clone=clone)
        pos = self.positions[data._dataname]
        if clone:
            pos = pos.clone()

        return pos

    def orderstatus(self, order):
        o = self.orders[order.ref]
        return o.status

    def _submit(self, oref):
        order = self.orders[oref]
        order.submit(self)
        self.notify(order)

    def _reject(self, oref):
        order = self.orders[oref]
        order.reject(self)
        self.notify(order)

    def _accept(self, oref):
        order = self.orders[oref]
        order.accept()
        self.notify(order)

    def _cancel(self, oref):
        order = self.orders[oref]
        order.cancel(self)
        self.notify(order)

    def _expire(self, oref):
        order = self.orders[oref]
        order.expire(self)
        self.notify(order)

    def _fill(self, oref, size, price, **kwargs):
        order = self.orders[oref]

        data = order.data
        pos = self.getposition(data, clone=False)
        psize, pprice, opened, closed = pos.update(size, price)

        comminfo = self.getcommissioninfo(data)

        closedvalue = closedcomm = 0.0
        openedvalue = openedcomm = 0.0
        margin = pnl = 0.0

        order.execute(data.datetime[0], size, price,
                      closed, closedvalue, closedcomm,
                      opened, openedvalue, openedcomm,
                      margin, pnl,
                      psize, pprice)

        if order.executed.remsize:
            order.partial()
        else:
            order.completed()

        self.notify(order)

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0,
            **kwargs):

        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        self.orders[order.ref] = order
        return self.o.order_create(order)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0,
             **kwargs):

        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)
        order.addcomminfo(self.getcommissioninfo(data))
        self.orders[order.ref] = order
        return self.o.order_create(order)

    def cancel(self, order):
        o = self.orders[order.ref]
        if order.status == Order.Cancelled:  # already cancelled
            return

        return self.o.order_cancel(order)

    def notify(self, order):
        self.notifs.append(order.clone())

    def get_notification(self):
        if not self.notifs:
            return None

        return self.notifs.popleft()

    def next(self):
        self.notifs.append(None)  # mark notification boundary
