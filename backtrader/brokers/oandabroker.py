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
from copy import copy
from datetime import date, datetime, timedelta
import threading

import ib.ext.Order
import ib.opt as ibopt

from backtrader.feed import DataBase
from backtrader import (TimeFrame, num2date, date2num, BrokerBase,
                        Order, OrderBase, OrderData)
from backtrader.utils.py3 import bytes, with_metaclass, queue, MAXFLOAT
from backtrader.metabase import MetaParams
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from backtrader.stores import ibstore
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
        ibstore.IBStore.BrokerCls = cls


class OandaBroker(with_metaclass(MetaOandaBroker, BrokerBase)):
    '''Broker implementation for Interactive Brokers.

    This class maps the orders/positions from Interactive Brokers to the
    internal API of ``backtrader``.

    Notes:

      - ``tradeid`` is not really supported, because the profit and loss are
        taken directly from IB. Because (as expected) calculates it in FIFO
        manner, the pnl is not accurate for the tradeid.

      - Position

        If there is an open position for an asset at the beginning of
        operaitons or orders given by other means change a position, the trades
        calculated in the ``Strategy`` in cerebro will not reflect the reality.

        To avoid this, this broker would have to do its own position
        management which would also allow tradeid with multiple ids (profit and
        loss would also be calculated locally), but could be considered to be
        defeating the purpose of working with a live broker
    '''
    params = ()

    def __init__(self, **kwargs):
        super(OandaBroker, self).__init__()

        self.o = oandastore.OandaStore(**kwargs)

        self.orders = collections.OrderedDict()  # orders by order id
        self.notifs = queue.Queue()  # holds orders which are notified

        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0

    def start(self):
        super(OandaBroker, self).start()
        self.o.start(broker=self)
        self.startingcash = self.cash = cash = self.o.get_cash()
        self.startingvalue = self.value = cash

    def stop(self):
        super(OandaBroker, self).stop()
        self.o.stop()

    def getcash(self):
        # This call cannot block if no answer is available from ib
        self.cash = cash = self.o.get_cash()
        return cash

    def getvalue(self, datas=None):
        self.value = self.o.get_value()
        return self.value

    def getposition(self, data, clone=True):
        return self.o.getposition(data._dataname, clone=clone)

    def getcommissioninfo(self, data):
        return OandaCommInfo(mult=mult, stocklike=False)

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

    def _fill(self, oref, size, price):
        order = self.orders[oref]
        # FIXME ... execute order ... use position to get opened, closed?

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
        self.notifs.put(order.clone())

    def get_notification(self):
        try:
            return self.notifs.get(False)
        except queue.Empty:
            pass

        return None

    def next(self):
        self.notifs.put(None)  # mark notification boundary
