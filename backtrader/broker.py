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

from comminfo import CommissionInfo
import metabase
from order import Order, BuyOrder, SellOrder


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
        self.startingcash = self.params.cash

        self.orders = list() # will only be appending
        self.pending = collections.deque() # need to popleft and append(right)

        self.position = collections.defaultdict(BrokerBack.Position)
        self.comminfo = dict({None: self.params.commission})
        self.notifs = collections.deque()

    def getcash(self):
        return self.params.cash

    def setcash(self, cash):
        self.startingcash = self.params.cash = cash

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
        except ValueError:
            # If the list didn't have the element we didn't cancel anything
            return False

        order.cancel()
        self.notify(order)
        return True

    def getvalue(self, datas=None):
        if not datas:
            datas = self.position.iterkeys()

        pos_value = 0.0
        for data in datas:
            comminfo = self.getcommissioninfo(data)
            position = self.position[data]
            pos_value += comminfo.getvalue(position, data.close[0])

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

        # Get comminfo object for the data
        comminfo = self.getcommissioninfo(order.data)

        closingsize = abs(size) - abs(remsize)
        # Get back cash for closed size
        ordervalue = comminfo.getoperationcost(closingsize, price)
        self.params.cash += ordervalue
        # Discount commision
        ordercomm = comminfo.getcomm_pricesize(closingsize, price)
        self.params.cash -= ordercomm
        # Re-adjust cash according to close price (it was discounted on loop enter)
        self.params.cash -= comminfo.cashadjust(closingsize, price, order.data.close[0])

        # order.execute(abs(size) - abs(remsize), price, dt, ordervalue, ordercomm, comminfo.margin)
        order.execute(closingsize, price, dt, ordervalue, ordercomm, comminfo.margin)

        if remsize:
            if not comminfo.checkmargin(size, price, self.params.cash):
                order.margin()
                self.notify(order)
                return

            # Returned remaining size has the right sign already
            self.openposition(order.data, remsize, price)

            sizeabs = abs(remsize)
            # Re-adjust cash according to operatio cost
            ordervalue = comminfo.getoperationcost(sizeabs, price)
            self.params.cash -= ordervalue

            # Reduce according to commission scheme
            ordercomm = comminfo.getcomm_pricesize(sizeabs, price)
            self.params.cash -= ordercomm

            # Re-adjust cash according to close price
            self.params.cash += comminfo.cashadjust(sizeabs, price, order.data.close[0])

            order.execute(sizeabs, price, dt, ordervalue, ordercomm, comminfo.margin)

        # We need to notify the owner
        self.notify(order)

    def closeposition(self, data, size, price):
        # FIXME: Are we checking if the position is closing a position in the same direction ??
        position = self.position[data]
        if not position.size:
            return size

        positionsign = position.size/abs(position.size)

        # number of contracts to close is the entire position or just the size
        closingabs = min(abs(position.size), abs(size))
        closing = positionsign * closingabs

        position.size -= closing
        return size + closing

    def openposition(self, data, size, price):
        position = self.position[data]
        # Calculate the new average price
        oldpos = position.price * position.size
        newpos = price * size

        position.size += size
        position.price = (oldpos + newpos) / position.size

    def notify(self, order):
        self.notifs.append(order)

    def next(self):
        for data, pos in self.position.iteritems():
            # futures change cash in the broker in every bar to ensure margin requirements are met
            comminfo = self.getcommissioninfo(data)
            self.params.cash += comminfo.cashadjust(pos.size, data.close[1], data.close[0])

        # Iterate once over all elements of the pending queue
        for i in xrange(len(self.pending)):
            order = self.pending.popleft()

            if order.expire():
                self.notify(order)
                continue

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
