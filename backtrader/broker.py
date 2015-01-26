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

import metabase


class OrderData(object):
    def __init__(self, dt=None, size=0, price=None, remsize=0):
        self.dt = dt
        self.size = size
        self.remsize = remsize
        self.price = price


class Order(object):
    __metaclass__ = metabase.MetaParams

    Market, Close, Limit, Stop, StopLimit = range(5)
    Buy, Sell = range(2)
    Submitted, Accepted, Partial, Completed, Canceled, Expired, Margin = range(7)

    params = (
        ('owner', None), ('data', None), ('size', None), ('price', None),
        ('exectype', None), ('valid', None),
    )

    def __getattr__(self, name):
        # dig into self.params if not found as attribute, mostly for external access
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            raise AttributeError

        super(CommissionInfo, self).__setattribute__(name, value)

    def __init__(self):
        if self.params.exectype is None:
            self.params.exectype = Order.Market

        self.status = Order.Submitted
        self.created = OrderData(self.data.datetime[0], self.params.size, self.params.price)
        self.executed = OrderData(remsize=self.params.size)

    def accept(self):
        self.status = Order.Accepted

    def cancel(self):
        self.status = Order.Canceled
        self.executed = self.data.datetime[0]

    def execute(self, size, price, dtindex=0):
        if not size:
            return

        self.executed.dt = self.data.datetime[dtindex]

        oldexec = self.executed.size * (self.executed.price or 0.0)
        newexec = price * size
        self.executed.size += size
        self.executed.price = (oldexec + newexec) / self.executed.size
        self.executed.remsize -= size

        self.status = Order.Partial if self.executed.remsize else Order.Completed

    def expire(self):
        if self.valid and self.data.datetime[0] > self.valid:
            self.status = Order.Expired
            self.executed = self.data.datetime[0]
            return True

        return False

    def margin(self):
        self.status = Order.Margin
        self.executed.dt = self.data.datetime[0]

    def alive(self):
        return self.status in [Order.Partial, Order.Accepted]


class BuyOrder(Order):
    ordtype = Order.Buy


class SellOrder(Order):
    ordtype = Order.Sell


class CommisionInfo(object):
    __metaclass__ = metabase.MetaParams

    params = (('comission', 0.0), ('mult', 1.0), ('margin', None),)

    def __getattr__(self, name):
        # dig into self.params if not found as attribute, mostly for external access
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            raise AttributeError

        super(CommissionInfo, self).__setattribute__(name, value)

    def checkmargin(self, size, price, cash):
        return cash >= (size * (self.params.margin or price))

    def getcomission(self, order):
        price = order.price if self.params.margin else 1.0
        return order.size * self.params.commission * price

    def profitandloss(self, position, price):
        return position.size * (position.price - price) * self.params.mult

    def mustcheckmargin(self):
        return self.params.margin is not None

    def cashadjust(self, size, price, newprice):
        if self.params.margin is None:
            # No margin, no need to adjust -> stock
            return 0.0

        return size * (newprice - price) * self.params.mult


class BrokerBack(object):
    __metaclass__ = metabase.MetaParams

    Market, Close, Limit = Order.Market, Order.Close, Order.Limit

    params = (('cash', 100.0), ('commission', CommisionInfo()),)

    class Position(object):
        def __init__(self):
            self.size = 0
            self.price = 0.0

        def __len__(self):
            return self.size

    def __init__(self):

        self.orders = list() # will only be appending
        self.pending = collections.deque()

        self.position = collections.defaultdict(BrokerBack.Position)
        self.comminfo = dict({None: self.params.commission})

    def getcommissioninfo(self, data):
        if data._name in self.comminfo:
            return self.comminfo[data._name]

        return self.comminfo[None]

    def setcommissioninfo(self, commission=0.0, margin=None, mult=1.0, name=None):
        self.comminfo[name] = CommissionInfo(comission=commission, margin=margin, mult=mult)

    def addcommissioninfo(self, comminfo, name=None):
        self.comminfo[name] = comminfo

    def start(self):
        pass

    def stop(self):
        pass

    def cancel(self, order):
        try:
            self.pending.remove(order)
            order.cancel()
        except ValueError:
            pass

        # We need to notify the owner even if nothing happened, because a notification is awaited
        self.notify(order)
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

    def submit(self, order):
        # FIXME: When an order is submitted, a margin check requirement has to be done before it
        # can be accepted. This implies going over the entire list of pending orders for all datas
        # and existing positions, simulating order execution and ending up with a "cash" figure
        # that can be used to check the margin requirement of the order. If not met, the order can
        # be immediately rejected
        order.accept()
        self.orders.append(order)
        self.pending.append(order)
        return order

    def buy(self, owner, data, size, price=None, exectype=None, valid=None):
        order = BuyOrder(owner=owner, data=data, size=size, price=price, exectype=exectype, valid=valid)
        return self.submit(order)

    def sell(self, owner, data, size, price=None, exectype=None, valid=None):
        order = SellOrder(owner=owner, data=data, size=size, price=price, exectype=exectype, valid=valid)
        return self.submit(order)

    def _execute(self, order, price, dtindex=0):
        size = order.executed.remsize * (1 if isinstance(order, BuyOrder) else -1)
        # closing a position may return cash to meet margin requirements
        remsize = self.closeposition(order.data, size, price)
        order.execute(abs(size) - abs(remsize), price, dtindex)

        if remsize:
            # if still opening a position check the margin/cash requirements
            comminfo = self.getcommissioninfo(order.data)
            if not comminfo.checkmargin(size, price, self.params.cash):
                order.margin()
                return

            # Returned remaining size has the right sign already
            self.openposition(order.data, remsize, price)
            order.execute(remsize, price, dtindex)

        # We need to notify the owner
        order.owner._ordernotify(order)

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

    def notify(self, order):
        order.owner._ordernotify(order)

    def next(self):
        # Iterate once over all elements of the pending queue
        for i in xrange(len(self.pending)):
            order = self.pending.popleft()

            if order.expire():
                self.notify(order)
                continue

            # get the position on order data
            position = self.position[order.data]
            # get the commissioninfo for this object
            comminfo = self.getcommissioninfo(order.data)

            # futures change cash in the broker in every bar to ensure margin requirements are met
            self.params.cash += comminfo.cashadjust(position.size, order.data.close[1], order.data.close[0])

            if order.exectype == Order.Market:
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

                if isinstance(order, BuyOrder):
                    if popen <= plimit:
                        self._execute(order, popen)
                    elif plow <= plimit <= phigh:
                        self._execute(order, plimit)

                else: # Sell
                    if popen >= plimit:
                        self._execute(order, popen)
                    elif plow <= plimit <= phigh:
                        self._execute(order, plimit)


            if order.alive():
                self.pending.append(order)
