#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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
################################################################################

import collections
import datetime


class Order(object):
    AtMarket, AtClose, AtLimit = range(3)
    OrderBuy, OrderSell = range(2)
    Pending, Completed, Partial, Cancelled, Expired = range(5)

    def __init__(self, order, data, size, price=None, how=None, valid=None):
        self.order = order
        self.data = data
        # FIXME: price can be none for "AtMarket" and "AtClose" but
        # it would be good to raise an Exception (ValueError?) if for example
        # AtLimit is passed and None is given as price
        self.price = price
        self.size = size
        self.how = how if how is not None else Order.AtMarket
        # FIXME: Set a default validity if None is given
        self.valid = valid

        self.status = Order.Pending
        self.dtcomplete = None


class BuyOrder(Order):
    def __init__(self, data, size, price=None, how=None, valid=None):
        super(BuyOrder, self).__init__(self.OrderBuy, data, size, price, how, valid)


class SellOrder(Order):
    def __init__(self, data, size, price=None, how=None, valid=None):
        super(SellOrder, self).__init__(self.OrderSell, data, size, price, how, valid)


class BrokerBack(object):
    AtMarket, AtClose, AtLimit = Order.AtMarket, Order.AtClose, Order.AtLimit

    class Position(object):
        def __init__(self):
            self.size = 0
            self.price = 0.0

        def __len__(self):
            return self.size

    def __init__(self, cash):
        self.cash = cash

        self.owner = dict()
        self.orders = collections.deque()
        self.pending = collections.deque()

        self.position = collections.defaultdict(BrokerBack.Position)

    def start(self):
        pass

    def stop(self):
        pass

    def buy(self, owner, data, size, price=None, how=None, valid=None):
        order = BuyOrder(data, size, price, how, valid)
        self.pending.append(order)
        self.owner[id(order)] = owner
        return id(order)

    def sell(self, owner, data, size, price=None, how=None, valid=None):
        order = SellOrder(data, size, price, how, valid)
        self.pending.append(order)
        self.owner[id(order)] = owner
        return id(order)

    def _buy(self, data, size, price):
        size = self.closeposition(data, size, price)
        if size:
            self.openposition(data, size, price)

    def _sell(self, data, size, price):
        # Pass negative size ... we are selling
        size = self.closeposition(data, -size, price)
        if size:
            # Returned Remaining size (if any) is negative
            self.openposition(data, size, price)

    def _execute(self, order, price):
        if order.order == Order.OrderBuy:
            self._buy(order.data, order.size, price)
        elif order.order == Order.OrderSell:
            self._sell(order.data, order.size, price)
        else:
            raise ValueError('Unknown Order type %d' % order.order)

        # Order has been completed ... change status, put into
        order.status = Order.Completed
        order.price = price
        order.dtcomplete = datetime.datetime.combine(order.data.date[0], order.data.time[0])
        self.orders.append(order)
        # We need to notify the owner
        self.owner[id(order)]._ordernotify(order)

    def getvalue(self, datas=None):
        if not datas:
            datas = self.position.iterkeys()

        profitloss = 0.0
        pos_value_on_open = 0.0
        for data in datas:
            position = self.position[data]
            price = data.close[0]

            pos_value_on_open += position.price * abs(position.size)
            profitloss += (price - position.price) * position.size

        return self.cash + pos_value_on_open + profitloss

    def getposition(self, data):
        return self.position[data]

    def closeposition(self, data, size, price):
        position = self.position[data]
        if not position.size:
            return size

        positionsign = position.size/abs(position.size)

        # number of contracts to close is the entire position or just the size
        closingabs = min(abs(position.size), abs(size))
        closing = positionsign * closingabs

        position.size -= closing

        profitloss = (price - position.price) * closing
        # position.profitloss += profitloss

        # original position is back plus/minus profitloss
        self.cash += position.price * closingabs + profitloss

        return size + closing

    def openposition(self, data, size, price):
        position = self.position[data]
        # Calculate the new average price
        oldpos = position.price * position.size
        newpos = price * size

        position.size += size
        position.price = (oldpos + newpos) / position.size

        # Reduce the available cash according to new open position
        self.cash -= price * abs(size)

    def next(self):
        for i in xrange(len(self.pending)):
            order = self.pending.popleft()
            # FIXME : Check if the order needs to expire
            if order.how == Order.AtMarket:
                # Take the fist tick of the new bar in the data -> Open
                price = order.data.open[0]
                self._execute(order, price)
            elif order.how == Order.AtClose:
                raise NotImplementedError('AtClose How not yet implemented')
            elif order.how == Order.AtLimit:
                raise NotImplementedError('AtLimit How not yet implemented')
            else:
                raise ValueError('Unknown Order Execution type %d' % order.how)
            # FIXME : If the order is not executed it must be appended to the queue
