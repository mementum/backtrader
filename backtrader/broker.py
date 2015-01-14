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

AtMarket = 0
AtClose = 1
AtLimit = 2

OrderBuy = 0
OrderSell = 1


class OrderedDefaultdict(collections.OrderedDict):
    # Adapted from:
    # http://stackoverflow.com/questions/4126348/how-do-i-rewrite-this-function-to-implement-ordereddict/
    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)

    def __missing__ (self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default

    def __reduce__(self):  # optional, for pickle support
        args = (self.default_factory,) if self.default_factory else ()
        return self.__class__, args, None, None, self.iteritems()


class Order(object):

    def __init__(self, order, data, price, size, execution):
        self.order = order
        self.data = data
        self.price = price
        self.size = size
        self.execution = execution


class BuyOrder(Order):
    def __init__(self, data, price, size, execution):
        self.order = OrderBuy
        self.data = data
        self.price = price
        self.size = size
        self.execution = execution


class SellOrder(Order):
    def __init__(self, data, price, size, execution):
        self.order = OrderSell
        self.data = data
        self.price = price
        self.size = size
        self.execution = execution


class BrokerBase(object):
    AtMarket = 0
    AtClose = 1
    AtLimit = 2

    OrderBuy = 0
    OrderSell = 1

    def __init__(self, cash):
        self.cash = float(cash)
        self.profitloss = 0.0
        self.equity = 0.0
        self.position = 0
        self.price = 0.0

        self.orders = OrderedDefaultdict(collections.deque)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position

    def buy(self, price, size, execution=AtClose):
        raise NotImplementedError

    def sell(self, price, size, execution=AtClose):
        raise NotImplementedError

    def start(self):
        pass

    def stop(self):
        pass

    def next(self):
        pass


class BrokerTest(BrokerBase):

    def buy(self, data, price=None, size=1, execution=AtClose):
        if execution == AtClose:
            self._buy(data, data.close[0], size)
            return

        self.orders[data].append(BuyOrder(data, price, size, execution))

    def _buy(self, data, price, size):
        if self.position < 0:
            size = self.closeposition(price, size)
        if size:
            self.openposition(price, size)

    def sell(self, data, price=None, size=1, execution=AtClose):
        if execution == AtClose:
            self._sell(data, data.close[0], size)
            return

        self.orders[data].append(SellOrder(data, price, size, execution))

    def _sell(self, data, price, size):
        if self.position > 0:
            # Pass negative size ... we are selling
            size = self.closeposition(price, -size)
        if size:
            # Returned Remaining size (if any) is negative
            self.openposition(price, size)

    def getvalue(self, data, price):
        pos_value_on_open = self.price * abs(self.position)
        profitloss = (price - self.price) * self.position
        return self.cash + pos_value_on_open + profitloss

    def closeposition(self, price, size):
        if not self.position:
            return size

        position = self.position
        positionsign = position/abs(position)

        # number of contracts to close is the entire position or just the size
        closingabs = min(abs(position), abs(size))
        closing = positionsign * closingabs

        self.position -= closing

        profitloss = (price - self.price) * closing
        self.profitloss += profitloss

        # original position is back plus/minus profitloss
        self.cash += self.price * closingabs + profitloss

        return size + closing

    def openposition(self, price, size):
        # Calculate the new average price
        oldpos = self.price * self.position
        newpos = price * size

        self.position += size
        self.price = (oldpos + newpos) / self.position
        # print 'opening position cash, price, size', self.cash, price, size
        self.cash -= price * abs(size)

    def next(self):
        for data, orders in self.orders.iteritems():
            for i in xrange(len(orders)):
                order = orders.popleft()
                if order.execution == AtMarket: # can do
                    price = data.open[0]
                    if order.order == OrderBuy:
                        self._buy(data, price, order.size)
                    else:
                        self._sell(data, price, order.size)
                    continue
                elif order.execution == AtLimit: # FIXME
                    # put it back at the front for reprocessing and break out of loop
                    # because next orders depend on this one being executed
                    orders.appendleft(order)
                    break
                else:
                    # Don't know what to do with this order ... skip it and go to next
                    continue
                    pass


if False:
    b = BrokerTest(10000)
    data = None

    print '----------------------------------------------------------------------'
    b.buy(data, price=20.0, size=100)
    print 'position', b.position
    print 'price', b.price
    print 'cash', b.cash

    print '----------------------------------------------------------------------'
    b.buy(data, price=25.0, size=100)
    print 'position', b.position
    print 'price', b.price
    print 'cash', b.cash

    print '----------------------------------------------------------------------'
    b.sell(data, price=30.0, size=200)
    print 'position', b.position
    print 'price', b.price
    print 'cash', b.cash

    print '----------------------------------------------------------------------'
    b.sell(data, price=30.0, size=200)
    print 'position', b.position
    print 'price', b.price
    print 'cash', b.cash

    print '----------------------------------------------------------------------'
    print 'value', b.getvalue(data, price=30.0)
