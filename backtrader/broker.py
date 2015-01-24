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

from parameters import Params

class OrderData(object):
    def __init__(self, dt=None, size=0, price=None):
        self.dt = dt
        self.size = size
        self.price = price


class Order(object):
    Market, Close, Limit = range(3)
    Buy, Sell = range(2)
    Pending, Completed, Partial, Cancelled, Expired = range(5)

    def __init__(self, ordtype, data, size, price=None, exectype=None, valid=None):
        self.ordtype = ordtype
        self.data = data

        self.status = Order.Pending
        self.exectype = exectype if exectype is not None else Order.Market
        self.valid = valid

        self.created = OrderData(data.datetime[0], size, price)
        self.executed = OrderData()

    def cancel(self):
        self.status = Order.Cancelled
        self.executed = OrderData(self.data.datetime[0], 0, None)

    def execute(self, size, price, dtindex=0):
        self.status = Order.Completed
        self.executed = OrderData(self.data.datetime[dtindex], size, price)

    def expire(self):
        self.status = Order.Expired
        self.executed = OrderData(self.data.datetime[0], 0, None)


class BuyOrder(Order):
    def __init__(self, data, size, price=None, exectype=None, valid=None):
        super(BuyOrder, self).__init__(Order.Buy, data, size, price, exectype, valid)


class SellOrder(Order):
    def __init__(self, data, size, price=None, exectype=None, valid=None):
        super(SellOrder, self).__init__(Order.Sell, data, size, price, exectype, valid)


class MetaBrokerBack(type):
    def __new__(meta, name, bases, dct):
        # Remove params from class definition to avod inheritance (and hence "repetition")
        newparams = dct.pop('params', ())

        # Create the new class - this pulls predefined "params"
        cls = super(MetaBrokerBack, meta).__new__(meta, name, bases, dct)

        # Pulls the param class out of it - default is the empty class
        params = getattr(cls, 'params', Params)

        # Subclass and store the existing params with the (extended if any) newly defined params
        cls.params = params._derive(name, newparams)

        # The "extparams" end up in the middle (baseparams + extparams + newparams) which makes sense
        return cls

    def __call__(cls, *args, **kwargs):
        obj = cls.__new__(cls, *args, **kwargs)
        obj.params = cls.params()
        for kname in kwargs.keys():
            if hasattr(obj.params, kname):
                setattr(obj.params, kname, kwargs.pop(kname))
        obj.__init__(*args, **kwargs)
        return obj


class BrokerBack(object):
    __metaclass__ = MetaBrokerBack

    Market, Close, Limit = Order.Market, Order.Close, Order.Limit

    params = (('cash', 100.0),)

    class Position(object):
        def __init__(self):
            self.size = 0
            self.price = 0.0

        def __len__(self):
            return self.size

    def __init__(self):

        self.owner = dict()
        self.orders = list() # will only be appending
        self.pending = collections.deque()

        self.position = collections.defaultdict(BrokerBack.Position)

    def start(self):
        pass

    def stop(self):
        pass

    def cancel(self, orderid):
        orders = filter(lambda x: id(x) == orderid, self.pending)
        for order in orders:
            # If the filtered list contains something is a single entry. we can safely return
            order.cancel()
            self.pending.remove(order)
            # We need to notify the owner
            self.owner[id(order)]._ordernotify(order)
            return True

        # If the list had no elements we didn't cancel anything
        return False

    def getvalue(self, datas=None):
        if not datas:
            datas = self.position.iterkeys()

        pos_value = 0.0
        for data in datas:
            position = self.position[data]
            pos_value += abs(position.size) * data.close[0]

        return self.params.cash + pos_value

    def getposition(self, data):
        return self.position[data]

    def submit(self, owner, order):
        self.orders.append(order)
        self.pending.append(order)
        self.owner[id(order)] = owner
        return id(order)

    def buy(self, owner, data, size, price=None, exectype=None, valid=None):
        return self.submit(owner, BuyOrder(data, size, price, exectype, valid))

    def sell(self, owner, data, size, price=None, exectype=None, valid=None):
        return self.submit(owner, SellOrder(data, size, price, exectype, valid))

    def _execute(self, order, price, dtindex=0):
        size = order.created.size * (1 if order.ordtype == Order.Buy else -1)
        size = self.closeposition(order.data, size, price)
        if size:
            # Returned remaining size has the right sign already
            self.openposition(order.data, size, price)

        order.execute(size, price, dtindex)

        # We need to notify the owner
        self.owner[id(order)]._ordernotify(order)

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
        self.params.cash += position.price * closingabs + profitloss

        return size + closing

    def openposition(self, data, size, price):
        position = self.position[data]
        # Calculate the new average price
        oldpos = position.price * position.size
        newpos = price * size

        position.size += size
        position.price = (oldpos + newpos) / position.size

        # Reduce the available cash according to new open position
        self.params.cash -= price * abs(size)

    def next(self):
        # Iterate once over all elements of the pending queue
        for i in xrange(len(self.pending)):
            order = self.pending.popleft()

            if order.valid and order.data.datetime[0] > order.valid:
                order.expire()
                # We need to notify the owner
                self.owner[id(order)]._ordernotify(order)
                continue

            if order.exectype == Order.Market:
                # Take the fist tick of the new bar -> Open
                self._execute(order, price=order.data.open[0])
            elif order.exectype == Order.Close:
                # execute with the price of the closed bar
                if order.data.datetime[0].time() != order.data.datetime[1].time():
                    # intraday: time changes in between bars
                    self._execute(order, price=order.data.close[1], dtindex=1)
                elif order.data.datetime[0].date() != order.data.datetime[1].date():
                    # daily: time is equal, date changes
                    self._execute(order, price=order.data.close[1], dtindex=1)

            elif order.exectype == Order.Limit:
                plow = order.data.low[0]
                phigh = order.data.high[0]
                popen = order.data.close[0]
                plimit = order.created.price

                if order.ordtype == Order.Buy:
                    if popen <= plimit:
                        self._execute(order, popen)
                    elif plow <= plimit <= phigh:
                        self._execute(order, plimit)

                else: # Sell
                    if popen >= plimit:
                        self._execute(order, popen)
                    elif plow <= plimit <= phigh:
                        self._execute(order, plimit)

            if order.status != Order.Completed:
                self.pending.append(order)
