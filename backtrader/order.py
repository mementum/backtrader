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

        self.value = 0.0
        self.comm = 0.0
        self.margin = None


class Order(object):
    __metaclass__ = metabase.MetaParams

    Market, Close, Limit, Stop, StopLimit = range(5)
    Buy, Sell, Stop, StopLimit = range(4)

    Submitted, Accepted, Partial, Completed, Canceled, Expired, Margin = range(7)
    Status =['Submitted', 'Accepted', 'Partial', 'Completed', 'Canceled', 'Expired', 'Margin']

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

    def isbuy(self):
        return isinstance(self, BuyOrder)

    def issell(self):
        return isinstance(self, SellOrder)

    def accept(self):
        self.status = Order.Accepted

    def cancel(self):
        self.status = Order.Canceled
        self.executed = self.data.datetime[0]

    def execute(self, size, price, dt, value, comm, margin):
        if not size:
            return

        self.executed.dt = dt

        oldexec = self.executed.size * (self.executed.price or 0.0)
        newexec = price * size
        self.executed.size += size
        self.executed.price = (oldexec + newexec) / self.executed.size
        self.executed.remsize -= size
        self.executed.value += value
        self.executed.comm += comm
        self.executed.margin = margin

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
