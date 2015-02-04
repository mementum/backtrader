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
    def __init__(self, dt=None, size=0, price=None, pricelimit=None, remsize=0):
        self.dt = dt
        self.size = size
        self.remsize = remsize
        self.price = price
        if not pricelimit:
            # if no pricelimit is given, use the given price
            self.pricelimit = self.price

        if pricelimit and not price:
            # price must always be set if pricelimit is set ...
            self.price = pricelimit


class Order(object):
    __metaclass__ = metabase.MetaParams

    Market, Close, Limit, Stop, StopLimit = range(5)
    Buy, Sell, Stop, StopLimit = range(4)
    Submitted, Accepted, Partial, Completed, Canceled, Expired, Margin = range(7)

    params = (
        ('owner', None), ('data', None), ('size', None), ('price', None), ('pricelimit', None),
        ('exectype', None), ('valid', None), ('triggered', True),
    )

    def __getattr__(self, name):
        # dig into self.params if not found as attribute, mostly for external access
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            raise AttributeError

        super(Order, self).__setattribute__(name, value)

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

    def execute(self, size, price, dt):
        if not size:
            return

        self.executed.dt = dt

        oldexec = self.executed.size * (self.executed.price or 0.0)
        newexec = price * size
        self.executed.size += size
        self.executed.price = (oldexec + newexec) / self.executed.size
        self.executed.remsize -= size

        self.status = Order.Partial if self.executed.remsize else Order.Completed

    def expire(self):
        if self.params.exectype == Order.Market:
            return False # will be executed yes or yes

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


class StopBuyOrder(BuyOrder):
    pass


class StopLimitBuyOrder(BuyOrder):
    def __init__(self):
        super(StopLimitBuyOrder, self).__init__()
        self.params.triggered = False


class SellOrder(Order):
    ordtype = Order.Sell


class StopSellOrder(SellOrder):
    pass


class StopLimitBuyOrder(SellOrder):
    def __init__(self):
        super(StopLimitSellOrder, self).__init__()
        self.params.triggered = False


class CommissionInfo(object):
    __metaclass__ = metabase.MetaParams

    params = (('commission', 0.0), ('mult', 1.0), ('margin', None),)

    def __getattr__(self, name):
        # dig into self.params if not found as attribute, mostly for external access
        return getattr(self.params, name)

    def __setattribute__(self, name, value):
        if hasattr(self.params, name):
            raise AttributeError

        super(CommissionInfo, self).__setattribute__(name, value)

    def checkmargin(self, size, price, cash):
        return cash >= (size * (self.params.margin or price))

    def getcomm_pricesize(self, size, price):
        price = price if not self.params.margin else 1.0
        return size * self.params.commission * price

    def getcommission(self, order):
        price = order.price if not self.params.margin else 1.0
        return order.size * self.params.commission * price

    def profitandloss(self, position, price):
        return position.size * (position.price - price) * self.params.mult

    def mustcheckmargin(self):
        return self.params.margin is not None

    def cashadjust(self, size, price, newprice):
        if not self.params.margin:
            # No margin, no need to adjust -> stock like assume
            return 0.0

        return size * (newprice - price) * self.params.mult


class BrokerBack(object):
    __metaclass__ = metabase.MetaParams

    Market, Close, Limit = Order.Market, Order.Close, Order.Limit

    params = (('cash', 100.0), ('commission', CommissionInfo()),)

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
        self.comminfo[name] = CommissionInfo(commission=commission, margin=margin, mult=mult)

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

    def _execute(self, order, dt, price):
        size = order.executed.remsize * (1 if isinstance(order, BuyOrder) else -1)
        # closing a position may return cash to meet margin requirements
        remsize = self.closeposition(order.data, size, price)
        order.execute(abs(size) - abs(remsize), price, dt)

        if remsize:
            # if still opening a position check the margin/cash requirements
            comminfo = self.getcommissioninfo(order.data)
            if not comminfo.checkmargin(size, price, self.params.cash):
                order.margin()
                return

            # Returned remaining size has the right sign already
            self.openposition(order.data, remsize, price)
            order.execute(abs(remsize), price, dt)

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

            plow = order.data.low[0]
            phigh = order.data.high[0]
            popen = order.data.open[0]
            pclose = order.data.close[0]
            pclose1 = order.data.close[1]
            pcreated = order.created.price
            plimit = order.created.pricelimit

            if order.exectype == Order.Market:
                self._execute(order, order.data.datetime[0], price=popen)

            elif order.exectype == Order.Close:
                # execute with the price of the closed bar
                if order.data.datetime[0].time() != order.data.datetime[1].time():
                    # intraday: time changes in between bars
                    self._execute(order, order.data.datetime[1], price=pclose1)
                elif order.data.datetime[0].date() != order.data.datetime[1].date():
                    # daily: time is equal, date changes
                    self._execute(order, order.data.datetime[1], price=pclose1)

            elif order.exectype == Order.Limit or \
                (order.exectype == Order.StopLimit and order.triggered):

                if isinstance(order, BuyOrder):
                    if plimit >= popen: # open smaller/equal than requested - buy cheaper
                        self._execute(order, order.data.datetime[0], price=popen)
                    elif plimit >= plow: # day low below req price ... match limit price
                        self._execute(order, order.data.datetime[0], price=plimit)

                else: # Sell
                    if plimit <= popen: # open greater/equal than requested - sell more expensive
                        self._execute(order, order.data.datetime[0], price=popen)
                    elif plimit <= phigh: # day high above req price ... match limit price
                        self._execute(order, order.data.datetime[0], price=plimit)

            elif order.exectype == Order.Stop:
                if isinstance(order, BuyOrder):
                    if popen >= pcreated:
                        # price penetrated with an open gap - use open
                        self._execute(order, order.data.datetime[0], price=popen)
                    elif phigh >= pcreated:
                        # price penetrated during the session - use trigger price
                        self._execute(order, order.data.datetime[0], price=pcreated)

                else: # Sell
                    if popen <= pcreated:
                        # price penetrated with an open gap - use open
                        self._execute(order, order.data.datetime[0], price=popen)
                    elif plow <= pcreated:
                        # price penetrated during the session - use trigger price
                        self._execute(order, order.data.datetime[0], price=pcreated)

            elif order.exectype == Order.StopLimit:
                if isinstance(order, BuyOrder):
                    if popen >= pcreated:
                        order.triggered = True
                        # price penetrated with an open gap
                        if plimit >= popen:
                            self._execute(order, order.data.datetime[0], price=popen)
                        elif plimit >= plow: # execute in same bar
                            self._execute(order, order.data.datetime[0], price=plimit)

                    elif phigh >= pcreated:
                        # price penetrated upwards during the session
                        order.triggered = True
                        # can calculate execution for a few cases
                        if popen > pclose:
                            if plimit >= pcreated:
                                self._execute(order, order.data.datetime[0], price=pcreated)
                            elif plimit >= pclose:
                                self._execute(order, order.data.datetime[0], price=plimit)
                        else: # popen < pclose
                            if plimit >= pcreated:
                                self._execute(order, order.data.datetime[0], price=pcreated)
                else: # Sell
                    if popen <= pcreated:
                        # price penetrated downwards with an open gap
                        order.triggered = True
                        if plimit <= open:
                            self._execute(order, order.data.datetime[0], price=popen)
                        elif plimit <= phigh: # execute in same bar
                            self._execute(order, order.data.datetime[0], price=plimit)

                    elif plow <= pcreated:
                        # price penetrated downwards during the session
                        order.triggered = True
                        # can calculate execution for a few cases
                        if popen <= pclose:
                            if plimit <= pcreated:
                                self._execute(order, order.data.datetime[0], price=pcreated)
                            elif plimit <= pclose:
                                self._execute(order, order.data.datetime[0], price=plimit)
                        else: # popen > pclose
                            if plimit <= pcreated:
                                self._execute(order, order.data.datetime[0], price=pcreated)


            if order.alive():
                self.pending.append(order)
